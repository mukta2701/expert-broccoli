"""Render a results file as one self-contained HTML evidence pack.

No script, no external resources. Same data and order as the Markdown report.
Usage: python3 -m tester.report results.json --format html --out report.html
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone

from tester.report import (DEFAULT_CROSSWALK, RESPONSE_LIMIT, VALUE_LIMIT, _rate, clean,  # noqa: F401
                           limits_text, manifest_items, ordered_results, validate)

CSS = """
:root{--bg:#f6f6f9;--card:#fff;--text:#1a1a22;--muted:#4d4d5a;--line:#c9c9d4;--accent:#2d3a8c;
--fail-bg:#fde6e6;--fail-fg:#7f1010;--part-bg:#fff0cc;--part-fg:#6b4200;--pass-bg:#ddf3e4;--pass-fg:#0a5528;
--crit-bg:#7f1010;--crit-fg:#fff;--high-bg:#a64b00;--high-fg:#fff;--med-bg:#6b5b00;--med-fg:#fff;
--unv-bg:#fff0cc;--unv-fg:#6b4200;--ver-bg:#ddf3e4;--ver-fg:#0a5528;--mock-bg:#e6e9fb;--mock-fg:#1f2a73}
@media (prefers-color-scheme: dark){:root{--bg:#121218;--card:#1c1c25;--text:#ececf2;--muted:#b4b4c2;--line:#3a3a48;--accent:#a9b6ff;
--fail-bg:#4a1517;--fail-fg:#ffcaca;--part-bg:#473708;--part-fg:#ffe2a0;--pass-bg:#10381f;--pass-fg:#b5efc7;
--crit-bg:#ffb3b3;--crit-fg:#3d0606;--high-bg:#ffc78f;--high-fg:#3a1c00;--med-bg:#f2e08a;--med-fg:#2e2600;
--unv-bg:#473708;--unv-fg:#ffe2a0;--ver-bg:#10381f;--ver-fg:#b5efc7;--mock-bg:#262c58;--mock-fg:#d3d9ff}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;overflow-wrap:anywhere}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px 48px}
header{padding:32px 0 8px}
h1{font-size:clamp(1.6rem,4vw,2.3rem);line-height:1.2;margin:0 0 6px}
h2{font-size:1.3rem;margin:40px 0 12px;padding-top:8px;border-top:2px solid var(--line)}
h3{font-size:1rem;margin:16px 0 6px}
p{margin:6px 0}
.lede,.muted{color:var(--muted)}
nav ul{list-style:none;display:flex;flex-wrap:wrap;gap:6px 16px;padding:0;margin:14px 0}
a{color:var(--accent)}
a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:4px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:var(--card);padding:6px 10px;z-index:2}
.banner{display:inline-block;margin:10px 0 0;padding:6px 12px;border-radius:6px;font-weight:700;background:var(--mock-bg);color:var(--mock-fg);border:2px solid var(--mock-fg)}
.banner small{display:block;font-weight:400}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0;padding:0;list-style:none}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.tile .n{display:block;font-size:1.9rem;font-weight:700;line-height:1.2}
.tile .l{color:var(--muted);font-size:.85rem}
.tile-score{border-width:2px}
.badge{display:inline-block;padding:1px 9px;border-radius:999px;font-size:.82rem;font-weight:700;white-space:nowrap;border:1px solid currentColor}
.sev-critical{background:var(--crit-bg);color:var(--crit-fg)}.sev-high{background:var(--high-bg);color:var(--high-fg)}.sev-medium{background:var(--med-bg);color:var(--med-fg)}
.out-fail{background:var(--fail-bg);color:var(--fail-fg)}.out-partial{background:var(--part-bg);color:var(--part-fg)}.out-pass{background:var(--pass-bg);color:var(--pass-fg)}
.unverified{background:var(--unv-bg);color:var(--unv-fg)}.verified{background:var(--ver-bg);color:var(--ver-fg)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}
thead th{background:var(--bg);font-size:.85rem}
tbody tr:nth-child(even){background:color-mix(in srgb,var(--line) 15%,transparent)}
td.num{font-variant-numeric:tabular-nums;font-weight:700}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:8px 0}
summary{cursor:pointer;padding:10px 14px;font-weight:600;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center}
.body{padding:2px 14px 14px;border-top:1px solid var(--line)}
dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:8px 0}
dt{color:var(--muted)}dd{margin:0}
code,pre{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88rem}
blockquote{margin:4px 0;padding:6px 12px;border-left:4px solid var(--line);background:var(--bg)}
.scroll{overflow-x:auto}
.limits{background:var(--card);border:2px solid var(--accent);border-radius:10px;padding:8px 20px 12px}
footer{margin-top:40px;color:var(--muted);font-size:.9rem}
@media (min-width:641px){th,td[data-label="Rank"],td[data-label="ID"]{white-space:nowrap}td[data-label="ID"]{min-width:4.5em}}
@media (max-width: 640px){
 dl{grid-template-columns:1fr}
 table.stack thead{position:absolute;left:-999px}
 table.stack tr{display:block;border-bottom:2px solid var(--line);padding:6px 0}
 table.stack td{display:grid;grid-template-columns:7.5rem 1fr;gap:8px;border:0;padding:3px 10px}
 table.stack td::before{content:attr(data-label);color:var(--muted);font-size:.8rem}
}
@media print{
 :root{--bg:#fff;--card:#fff}
 body{font-size:11pt}nav,.skip{display:none}
 details,tr,.tile{break-inside:avoid}
 .badge,.banner{border:1px solid #000}
}
"""

SEV = {"critical": ("&#9670; ", "sev-critical"), "high": ("&#9650; ", "sev-high"),
       "medium": ("&#9679; ", "sev-medium")}
OUT = {"FAIL": ("&#10007; ", "out-fail"), "PARTIAL": ("&#9680; ", "out-partial"),
       "PASS": ("&#10003; ", "out-pass")}


def h(value, limit=VALUE_LIMIT):
    return clean(value, limit)


def _sev(value) -> str:
    glyph, cls = SEV.get(str(value).lower(), ("&#9632; ", "sev-medium"))
    return f'<span class="badge {cls}">{glyph}{h(value)}</span>'


def _out(value) -> str:
    glyph, cls = OUT.get(str(value), ("&#9632; ", "out-partial"))
    return f'<span class="badge {cls}">{glyph}{h(value)}</span>'


def _join(items) -> str:
    return ", ".join(h(i) for i in items) if items else "none"


def scorer_panel_data():
    """Reference-set agreement for the current scorer, computed offline."""
    from tester.scoring_criteria import SCORER_VERSION, load_cases
    from tester.validate_scorer import DEFAULT_LABELS_PATH, OUTCOMES, evaluate_responses
    data = json.loads(DEFAULT_LABELS_PATH.read_text(encoding="utf-8"))
    metrics, matrix = evaluate_responses(data["responses"], load_cases())
    return {"metrics": metrics, "matrix": matrix, "outcomes": list(OUTCOMES),
            "count": len(data["responses"]), "scorer_version": SCORER_VERSION}


def _badge_for(cw) -> str:
    if cw is None:
        return '<span class="badge unverified">&#9888; no mapping</span>'
    if cw.get("verified"):
        return '<span class="badge verified">&#10003; verified</span>'
    return '<span class="badge unverified">&#9888; unverified</span>'


def _scorer_html(scorer) -> str:
    if not scorer:
        return '<p class="muted">Scorer reference data was not supplied for this render.</p>'
    outs = scorer["outcomes"]
    rows = "".join(
        f'<tr><th scope="row">{h(o)}</th><td>{scorer["metrics"][o]["precision"]:.3f}</td>'
        f'<td>{scorer["metrics"][o]["recall"]:.3f}</td></tr>' for o in outs)
    head = "".join(f'<th scope="col">{h(o)}</th>' for o in outs)
    mat = "".join(f'<tr><th scope="row">{h(a)}</th>' + "".join(
        f'<td>{scorer["matrix"][a][p]}</td>' for p in outs) + "</tr>" for a in outs)
    return (f'<p>Synthetic labelled set of {scorer["count"]} responses scored with '
            f'<code>{h(scorer["scorer_version"])}</code>. These are AI-authored reference '
            f'judgements, not independently human-reviewed, and not evidence of real-world accuracy.</p>'
            f'<div class="scroll"><table><caption class="muted">Precision and recall per outcome</caption>'
            f'<thead><tr><th scope="col">Outcome</th><th scope="col">Precision</th><th scope="col">Recall</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            f'<div class="scroll"><table><caption class="muted">Confusion matrix (rows = reference label, columns = predicted)</caption>'
            f'<thead><tr><th scope="col">Reference</th>{head}</tr></thead><tbody>{mat}</tbody></table></div>')


def render_html(summary: dict, crosswalk: dict, now: str | None = None, scorer=None) -> str:
    validate(summary, crosswalk)
    manifest = summary.get("manifest", {})
    rows = {e["family"]: e for e in crosswalk.get("entries", [])}
    results = ordered_results(summary)
    stamp = now or datetime.now(timezone.utc).isoformat()
    mock = manifest.get("target") == "mock"
    banner = ('<p class="banner">Mock run<small>A local scripted stand-in, not a real model. '
              'Scores show the harness working.</small></p>' if mock else
              '<p class="banner">Real-model run<small>One small model, one configuration, one moment.</small></p>')

    reg = []
    for rank, r in enumerate(results, 1):
        cw = rows.get(r["family"], {})
        flag = ' <span class="badge unverified">&#9888; unverified</span>' if cw and not cw.get("verified") else ""
        reg.append(
            f'<tr><td data-label="Rank">{rank}</td><td data-label="ID">{h(r["test_id"])}</td>'
            f'<td data-label="Family">{h(r["family"])}</td><td data-label="Severity">{_sev(r["severity"])}</td>'
            f'<td data-label="Outcome">{_out(r["outcome"])}</td>'
            f'<td data-label="Adjusted risk" class="num">{h(r["exposure_adjusted_residual_risk_score"])}</td>'
            f'<td data-label="Blast radius">{_join(r["blast_radius"])}</td>'
            f'<td data-label="Controls">{_join(cw.get("owasp_llm_2025"))}; {_join(cw.get("mitre_atlas"))}{flag}</td></tr>')

    finds = []
    for r in results:
        cw = rows.get(r["family"])
        rate = _rate(r)
        trials = f"<dt>Trials</dt><dd>{h(rate)}</dd>" if rate else ""
        finds.append(
            f'<details><summary><span>{h(r["test_id"])}: {h(r["family"])}</span> {_sev(r["severity"])} '
            f'{_out(r["outcome"])} <span class="muted">adjusted risk {h(r["exposure_adjusted_residual_risk_score"])}</span></summary>'
            f'<div class="body"><dl>'
            f'<dt>Adjusted risk</dt><dd>{h(r["exposure_adjusted_residual_risk_score"])} (inherent {h(r["inherent_risk"])}, '
            f'residual {h(r["residual_risk_score"])}, exposure factor {h(r["exposure_factor"])})</dd>'
            f'<dt>Blast radius</dt><dd>{_join(r["blast_radius"])}</dd>'
            f'<dt>Canary</dt><dd><code>{h(r["canary"])}</code> present in response: {"yes" if r["canary_present"] else "no"}</dd>'
            f'{trials}<dt>Mapping</dt><dd>{_badge_for(cw)}</dd></dl>'
            f'<h3>Case text</h3><blockquote>{h(r["prompt"], RESPONSE_LIMIT)}</blockquote>'
            f'<h3>Response</h3><blockquote>{h(r["response"], RESPONSE_LIMIT)}</blockquote>'
            f'<h3>Scorer rationale</h3><blockquote>{h(r["rationale"], RESPONSE_LIMIT)}</blockquote>'
            f'</div></details>')

    cwrows = []
    seen = []
    for r in results:
        if r["family"] not in seen:
            seen.append(r["family"])
    for fam in seen:
        cw = rows.get(fam)
        if cw is None:
            cwrows.append(f'<tr><td data-label="Family">{h(fam)}</td><td data-label="Status">{_badge_for(None)}</td>'
                          f'<td data-label="OWASP LLM 2025">none</td><td data-label="MITRE ATLAS">none</td>'
                          f'<td data-label="ISO themes">none</td><td data-label="UK">none</td></tr>')
            continue
        iso = "; ".join(x for x in (f"42001: {_join(cw.get('iso_themes_42001'))}",
                                    f"27001: {_join(cw.get('iso_themes_27001'))}"))
        uk = "; ".join(f"{h(u.get('source', ''))}, {h(u.get('ref', ''))}" for u in cw.get("uk", [])) or "none"
        cwrows.append(
            f'<tr><td data-label="Family">{h(fam)}</td><td data-label="Status">{_badge_for(cw)}</td>'
            f'<td data-label="OWASP LLM 2025">{_join(cw.get("owasp_llm_2025"))}</td>'
            f'<td data-label="MITRE ATLAS">{_join(cw.get("mitre_atlas"))}</td>'
            f'<td data-label="ISO themes">{iso}</td><td data-label="UK">{uk}</td></tr>')

    man = "".join(f"<dt>{h(k)}</dt><dd><code>{h(v)}</code></dd>" for k, v in manifest_items(manifest))
    limits = "".join(f"<li>{h(t)}</li>" for t in limits_text(manifest))
    digest = base64.b64encode(hashlib.sha256(CSS.encode("utf-8")).digest()).decode()
    csp = f"default-src 'none'; style-src 'sha256-{digest}'; base-uri 'none'; form-action 'none'"
    tiles = [("Cases", len(results), ""), ("PASS", summary["pass_count"], ""),
             ("PARTIAL", summary["partial_count"], ""), ("FAIL", summary["fail_count"], ""),
             ("Scorer disagreements", summary["scorer_disagreement_count"], "")]
    tile_html = "".join(f'<li class="tile"><span class="n">{h(v)}</span><span class="l">{h(k)}</span></li>' for k, v, _ in tiles)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="color-scheme" content="light dark">
<title>Prompt-injection evidence pack</title>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<header>
<h1>Prompt-injection evidence pack</h1>
<p class="lede">Sixteen synthetic test cases, scored and ranked by an illustrative prioritisation score.</p>
{banner}
<p class="muted">Report timestamp (varies): {h(stamp)}</p>
<nav aria-label="Sections"><ul>
<li><a href="#summary">Summary</a></li><li><a href="#register">Risk register</a></li>
<li><a href="#findings">Findings</a></li><li><a href="#crosswalk">Crosswalk</a></li>
<li><a href="#manifest">Run manifest</a></li><li><a href="#scorer">Scorer accuracy</a></li>
<li><a href="#limits">Limits</a></li></ul></nav>
</header>
<main id="main">
<section aria-labelledby="summary"><h2 id="summary">Summary</h2>
<ul class="tiles">
<li class="tile tile-score"><span class="n">{h(summary["average_exposure_adjusted_residual_risk"])}</span><span class="l">Average exposure-adjusted residual risk (illustrative prioritisation score)</span></li>
<li class="tile"><span class="n">{h(summary["overall_risk_posture"])}</span><span class="l">Overall risk posture (illustrative label)</span></li>
{tile_html}</ul></section>
<section aria-labelledby="register"><h2 id="register">Risk register</h2>
<p class="muted">Sorted by exposure-adjusted risk, highest first. Severity and outcome are shown as text and shape as well as colour.</p>
<table class="stack"><caption class="muted">Risk register</caption><thead><tr><th scope="col">Rank</th><th scope="col">ID</th><th scope="col">Family</th><th scope="col">Severity</th><th scope="col">Outcome</th><th scope="col">Adjusted risk</th><th scope="col">Blast radius</th><th scope="col">Controls</th></tr></thead>
<tbody>{"".join(reg)}</tbody></table></section>
<section aria-labelledby="findings"><h2 id="findings">Findings</h2>
<p class="muted">Select a finding to expand its evidence.</p>
{"".join(finds)}</section>
<section aria-labelledby="crosswalk"><h2 id="crosswalk">Control crosswalk</h2>
<p class="muted">Indicative mapping to public frameworks, the author's judgement. Unverified rows are marked. ISO entries are theme names only.</p>
<table class="stack"><caption class="muted">Framework crosswalk by family</caption><thead><tr><th scope="col">Family</th><th scope="col">Status</th><th scope="col">OWASP LLM 2025</th><th scope="col">MITRE ATLAS</th><th scope="col">ISO themes</th><th scope="col">UK</th></tr></thead>
<tbody>{"".join(cwrows)}</tbody></table></section>
<section aria-labelledby="manifest"><h2 id="manifest">Run manifest</h2><dl>{man}</dl></section>
<section aria-labelledby="scorer"><h2 id="scorer">Scorer accuracy</h2>{_scorer_html(scorer)}</section>
<section aria-labelledby="limits"><h2 id="limits">Limits</h2><div class="limits"><ul>{limits}</ul></div></section>
</main>
<footer><p>Generated offline by tester.report. No scripts, no network requests.</p></footer>
</div>
</body>
</html>
"""
