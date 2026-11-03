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
from tester.report_html import CSS as BASE_CSS, h as _h  # noqa: E402
from tester.targets import SYSTEM_VARIANTS  # noqa: E402

_BIDI = dict.fromkeys(list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A)))


def h(value, limit=500):
    return _h(str(value).translate(_BIDI), limit)


EXTRA_CSS = """
.wrap{max-width:min(1800px,96vw)}
.cmpwrap{overflow-x:auto}.hint{display:none;margin:4px 0}
.cmp{table-layout:fixed;width:100%;min-width:56rem}
.cmp th.id{width:150px;white-space:normal;position:sticky;left:0;background:var(--card);z-index:1}
.cmp th.run{font-weight:400;white-space:normal}.cmp td{overflow-wrap:anywhere}
.cmp .mname{display:block;font-weight:700}.cmp .msub{display:block;font-size:.78rem;color:var(--muted)}
.cmp details{margin:6px 0 0}.cmp summary{padding:2px 8px;font-weight:400;font-size:.8rem;display:block}
.cmp .gap{color:var(--muted);font-style:italic}.cmp tr.total td,.cmp tr.total th{border-top:2px solid var(--line);font-weight:700}
.cmp .mix{display:block;color:var(--muted);font-size:.8rem}
.cmp .badge{white-space:normal}.badge.neutral{background:var(--bg);color:var(--muted)}
@media (max-width:960px){.hint{display:block}}
@media (max-width:640px){.cmp th.id{width:6.5rem}}
"""
CSS = BASE_CSS + EXTRA_CSS
NOTE = ("Scores are illustrative. Results vary between runs; one small model per column is an anecdote, "
        "not a rate or a safety verdict. \"Leaked\" is used only for columns where a canary was planted in a "
        "system message (system variant weak or strong). Otherwise no secret was in the model's context, and "
        "\"no secret · FAIL n of N\" only counts replies the scorer judged as going along with the "
        "attack. PARTIAL/PASS only means no canary leak was seen.")


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
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise ValueError(f"{file}: not a usable results file ({type(error).__name__})") from None
    if not results:
        raise ValueError(f"{file}: the run has no results")
    for r in results.values():
        t = r.get("trials")
        if t is not None:
            for field in ("n", "attack_successes"):
                if not isinstance(t, dict) or type(t.get(field)) is not int:
                    raise ValueError(f"{file}: case {r['test_id']} trials is missing integer field '{field}'")
    m = summary.get("manifest")
    if not isinstance(m, dict):
        m = {}
        label_note = ", manifest missing"
    else:
        label_note = ""
    planted = m.get("system_variant") in SYSTEM_VARIANTS and m.get("system_variant") != "none"
    model = m.get("model") or f"mock ({m.get('mode', summary.get('mode', '?'))})"
    date = str(m.get("timestamp_utc") or "")[:10] or folder.name or "unknown date"
    sub = (f"system {m.get('system_variant', 'n/a')} · temp {'n/a' if m.get('temperature') is None else m['temperature']}"
           f" · {m.get('trials', 1)} trials · {date}{label_note}")
    label = (f"{model}, system {m.get('system_variant', 'n/a')}, temp {'n/a' if m.get('temperature') is None else m['temperature']}, "
             f"{m.get('trials', 1)} trial(s), {date}{label_note}")
    return {"planted": planted, "label": label, "model": model, "sub": sub, "results": results, "order": [r["test_id"] for r in summary["results"]]}


def _word(leaks, n, planted) -> str:
    return f"leaked {leaks} of {n}" if planted else f"no secret · FAIL {leaks} of {n}"


def _badge(leaks, n, planted) -> str:
    if not planted:
        cls, glyph = "neutral", "&#8854; "
    else:
        cls, glyph = (("out-pass", "&#10003; ") if leaks == 0 else
                      ("out-fail", "&#10007; ") if leaks == n else ("out-partial", "&#9680; "))
    return f'<span class="badge {cls}">{glyph}{_word(leaks, n, planted)}</span>'


def _cell(r, planted) -> str:
    t = r.get("trials")
    n, leaks = (t["n"], t["attack_successes"]) if t else (1, int(r["outcome"] == "FAIL"))
    mix = Counter(t["outcomes"] if t else [r["outcome"]])
    mix_text = " &middot; ".join(f"{k} {mix[k]}" for k in ("FAIL", "PARTIAL", "PASS") if mix[k])
    shown = f"reply shown is trial 1 of {n}" if n > 1 else "stored reply"
    return (f'<td>{_badge(leaks, n, planted)}'
            f'<span class="mix">{mix_text}</span><details><summary>Reply</summary><div class="body">'
            f'<p class="muted">{shown}</p><blockquote>{h(r["response"], RESPONSE_LIMIT)}</blockquote>'
            f'</div></details></td>'), leaks, n


def render_compare(runs: list, now: str | None = None) -> str:
    seen, heads = Counter(), []
    for run in runs:
        seen[run["label"]] += 1
        dup = "" if seen[run["label"]] == 1 else f" #{seen[run['label']]}"
        heads.append(f'<th scope="col" class="run"><span class="mname">{h(run["model"] + dup)}</span>'
                     f'<span class="msub">{h(run["sub"])}</span></th>')
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
            cell, leaks, n = _cell(r, run["planted"])
            totals[i][0] += leaks
            totals[i][1] += n
            cells.append(cell)
        body.append(f'<tr class="case"><th scope="row" class="id">{h(tid)}<span class="mix">{h(family[tid])}</span></th>'
                    + "".join(cells) + "</tr>")
    head = "".join(heads)
    foot = "".join(f"<td>{_badge(a, b, run['planted'])}</td>" for (a, b), run in zip(totals, runs))
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
<p class="lede">Attacks as rows, runs as columns. Each cell counts trials where the canary scorer marked FAIL (a canary leak when a canary was planted).</p>
<p class="limits">{h(NOTE, 1000)} A cell marked "not run" means that run did not include the case.</p>
<p class="muted">Report timestamp (varies): {h(stamp)}</p>
</header>
<main>
<p class="muted">Leaks per attack and run (illustrative)</p>
<p class="hint muted">&#8596; scroll sideways to see more runs</p>
<div class="cmpwrap"><table class="cmp" aria-label="Leaks per attack and run, illustrative">
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
    try:
        Path(args.output).write_text(render_compare(runs), encoding="utf-8")
    except OSError as error:
        parser.error(f"cannot write {args.output}: {error.strerror or error}")
    print(f"Comparison written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
