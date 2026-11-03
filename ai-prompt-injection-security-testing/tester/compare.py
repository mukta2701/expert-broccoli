"""Put two or more runs side by side in one self-contained HTML page.

Usage: python3 -m tester.compare runs/A runs/B --output compare.html
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tester.report import RESPONSE_LIMIT  # noqa: E402
from tester.report_html import CSS as BASE_CSS, h  # noqa: E402

EXTRA_CSS = """
.cmp{min-width:0}.cmp th.run{min-width:11rem}.cmp td{min-width:11rem}.cmp th.id{white-space:nowrap}
.cmp details{margin:6px 0 0}.cmp summary{padding:4px 10px;font-weight:400;font-size:.85rem}
.cmp .gap{color:var(--muted);font-style:italic}.cmp tr.total td,.cmp tr.total th{border-top:2px solid var(--line);font-weight:700}
.cmp .mix{display:block;color:var(--muted);font-size:.8rem}
"""
CSS = BASE_CSS + EXTRA_CSS
NOTE = ("Scores are illustrative. Results vary between runs; one small model per column is an anecdote, "
        "not a rate or a safety verdict. PARTIAL/PASS here only means no canary leak was seen unless a canary "
        "was planted (system variant none or n/a means no secret was in the model's context).")


def load_run(path) -> dict:
    """Read a run folder or a results.json path; raise ValueError with a clear message."""
    p = Path(path)
    file = p / "results.json" if p.is_dir() else p
    folder = p if p.is_dir() else p.parent
    if not file.is_file():
        raise ValueError(f"{path}: no results.json found")
    try:
        summary = json.loads(file.read_text(encoding="utf-8"))
        results = {r["test_id"]: r for r in summary["results"]}
        for r in results.values():
            r["family"], r["response"], r["outcome"]  # noqa: B018 - required keys
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"{file}: not a usable results file ({type(error).__name__})") from None
    m = summary.get("manifest") or {}
    model = m.get("model") or f"mock ({m.get('mode', summary.get('mode', '?'))})"
    date = str(m.get("timestamp_utc") or "")[:10] or folder.name or "unknown date"
    label = (f"{model}, system {m.get('system_variant', 'n/a')}, temp {'n/a' if m.get('temperature') is None else m['temperature']}, "
             f"{m.get('trials', 1)} trial(s), {date}")
    return {"label": label, "results": results, "order": [r["test_id"] for r in summary["results"]]}


def _cell(r) -> str:
    t = r.get("trials")
    n, leaks = (t["n"], t["attack_successes"]) if t else (1, int(r["outcome"] == "FAIL"))
    mix = Counter(t["outcomes"] if t else [r["outcome"]])
    cls, glyph = (("out-pass", "&#10003; ") if leaks == 0 else
                  ("out-fail", "&#10007; ") if leaks == n else ("out-partial", "&#9680; "))
    mix_text = " &middot; ".join(f"{k} {mix[k]}" for k in ("FAIL", "PARTIAL", "PASS") if mix[k])
    shown = f"reply shown is trial 1 of {n}" if n > 1 else "stored reply"
    return (f'<td><span class="badge {cls}">{glyph}leaked {leaks} of {n}</span>'
            f'<span class="mix">{mix_text}</span><details><summary>Reply</summary><div class="body">'
            f'<p class="muted">{shown}</p><blockquote>{h(r["response"], RESPONSE_LIMIT)}</blockquote>'
            f'</div></details></td>'), leaks, n


def render_compare(runs: list, now: str | None = None) -> str:
    seen, labels = Counter(), []
    for run in runs:
        seen[run["label"]] += 1
        labels.append(run["label"] if seen[run["label"]] == 1 else f"{run['label']} #{seen[run['label']]}")
    ids, family = [], {}
    for run in runs:
        for tid in run["order"]:
            if tid not in family:
                ids.append(tid)
                family[tid] = run["results"][tid]["family"]
    totals = [[0, 0] for _ in runs]
    body = []
    for tid in ids:
        cells = []
        for i, run in enumerate(runs):
            r = run["results"].get(tid)
            if r is None:
                cells.append('<td class="gap">not run</td>')
                continue
            cell, leaks, n = _cell(r)
            totals[i][0] += leaks
            totals[i][1] += n
            cells.append(cell)
        body.append(f'<tr class="case"><th scope="row" class="id">{h(tid)}<span class="mix">{h(family[tid])}</span></th>'
                    + "".join(cells) + "</tr>")
    head = "".join(f'<th scope="col" class="run">{h(lab)}</th>' for lab in labels)
    foot = "".join(f"<td>leaked {a} of {b}</td>" for a, b in totals)
    digest = base64.b64encode(hashlib.sha256(CSS.encode("utf-8")).digest()).decode()
    csp = f"default-src 'none'; style-src 'sha256-{digest}'; base-uri 'none'; form-action 'none'"
    stamp = now or datetime.now(timezone.utc).isoformat()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="color-scheme" content="light dark">
<title>Run comparison</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
<h1>Run comparison</h1>
<p class="lede">Attacks as rows, runs as columns. Each cell counts trials where the canary scorer marked FAIL (a canary leak).</p>
<p class="limits">{h(NOTE, 1000)} A cell marked "not run" means that run did not include the case.</p>
<p class="muted">Report timestamp (varies): {h(stamp)}</p>
</header>
<main>
<div class="scroll"><table class="cmp"><caption class="muted">Leaks per attack and run (illustrative)</caption>
<thead><tr><th scope="col">Attack</th>{head}</tr></thead>
<tbody>{"".join(body)}
<tr class="total"><th scope="row">Total</th>{foot}</tr></tbody></table></div>
</main>
<footer><p>Generated offline by tester.compare. No scripts, no network requests.</p></footer>
</div>
</body>
</html>
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Compare two or more runs on one HTML page.")
    parser.add_argument("runs", nargs="+", help="Run folders (or results.json files).")
    parser.add_argument("--output", default="compare.html")
    args = parser.parse_args(argv)
    try:
        runs = [load_run(p) for p in args.runs]
    except ValueError as error:
        parser.error(str(error))
    if len(runs) == 1:
        print("warning: only one run given, nothing is being compared", file=sys.stderr)
    Path(args.output).write_text(render_compare(runs), encoding="utf-8")
    print(f"Comparison written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
