"""Render a results file as a Markdown risk register or a single-file HTML evidence pack.

Usage: python3 -m tester.report results.json --format md|html
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tester.stats import wilson_interval  # noqa: E402

DEFAULT_CROSSWALK = PROJECT_ROOT / "data" / "framework_crosswalk.json"
MD_SPECIAL = set("\\`*_[]()!|~#")
RESPONSE_LIMIT = 300


def clean(value, limit: int | None = None) -> str:
    """HTML-escape and defang untrusted text; keep it on one line. Safe for HTML and Markdown."""
    text = " ".join(str(value).split())
    if limit and len(text) > limit:
        text = text[:limit] + "..."
    text = html.escape(text, quote=True)
    text = re.sub(r"(?i)(https?|ftp):(?=//)", lambda m: m.group(1) + "&#58;", text)
    text = re.sub(r"(?i)\bwww\.", lambda m: m.group(0)[:3] + "&#46;", text)
    text = re.sub(r"(?i)\b(javascript|data|vbscript):", lambda m: m.group(1) + "&#58;", text)
    return text


def esc(value, limit: int | None = None) -> str:
    """Neutralise HTML and Markdown in untrusted text; keep it on one line."""
    return "".join("\\" + c if c in MD_SPECIAL else c for c in clean(value, limit))


MANIFEST_KEYS = ("mode", "target", "model", "tool_version", "scorer_version", "baseline_scorer_version",
                 "cases_sha256", "seed", "temperature", "trials", "timestamp_utc")


def manifest_items(manifest: dict) -> list:
    """(key, value) pairs shown in every format, in one order."""
    items = []
    for key in MANIFEST_KEYS:
        if key in manifest:
            value = manifest[key]
            if value is None and key in ("model", "temperature"):
                value = "n/a (mock)"
            items.append((key, value))
    return items


def ordered_results(summary: dict) -> list:
    """Highest exposure-adjusted risk first, ties by test id."""
    return sorted(summary["results"],
                  key=lambda r: (-r["exposure_adjusted_residual_risk_score"], r["test_id"]))


def _join(items) -> str:
    return ", ".join(esc(i) for i in items) if items else "none"


def _rate(item: dict) -> str | None:
    t = item.get("trials")
    if not t:
        return None
    low, high = wilson_interval(t["attack_successes"], t["n"])
    return f"{t['attack_successes']}/{t['n']} attack successes, Wilson 95% interval {low:.2f} to {high:.2f}"


def limits_text(manifest: dict) -> list:
    if manifest.get("target") == "mock":
        target = ("In this run the target is a mock: a local scripted stand-in, not a real model. "
                  "Outcomes show the test harness working, not how any real system behaves.")
    else:
        target = ("This is a real-model run against one small model. Results describe that model, "
                  "that configuration and that moment only.")
    return [
        target,
        "Scores are an illustrative prioritisation score: likelihood x impact, reduced by control "
        "effectiveness and raised by reachable capabilities. They are not measured probabilities.",
        "Framework mappings are indicative. They are the author's judgement, not a compliance verdict, "
        "and ISO entries are theme names only, with no clause numbers.",
        "Sixteen synthetic cases cover a small slice of prompt-injection techniques. A pass does not "
        "show an absence of weaknesses.",
    ]


def _limits(manifest: dict) -> list:
    return ["- " + t for t in limits_text(manifest)]


def validate(summary, crosswalk) -> None:
    if not isinstance(summary, dict) or not isinstance(summary.get("results"), list):
        raise ValueError("results file must be a JSON object with a results list")
    if not isinstance(crosswalk, dict) or not isinstance(crosswalk.get("entries"), list):
        raise ValueError("crosswalk must be a JSON object with an entries list")
    if not all(isinstance(r, dict) for r in summary["results"]) or not isinstance(summary.get("manifest", {}), dict):
        raise ValueError("results entries and manifest must be JSON objects")


def render_report(summary: dict, crosswalk: dict, now: str | None = None) -> str:
    validate(summary, crosswalk)
    manifest = summary.get("manifest", {})
    rows = {e["family"]: e for e in crosswalk.get("entries", [])}
    results = ordered_results(summary)
    stamp = now or datetime.now(timezone.utc).isoformat()
    L = ["# Prompt-injection risk register", "",
         f"Report timestamp (varies): {stamp}", "",
         "## Summary", "",
         f"- Cases: {len(results)}",
         f"- PASS: {summary['pass_count']} | PARTIAL: {summary['partial_count']} | FAIL: {summary['fail_count']}",
         f"- Average exposure-adjusted residual risk (illustrative prioritisation score): "
         f"{summary['average_exposure_adjusted_residual_risk']}",
         f"- Overall risk posture: {esc(summary['overall_risk_posture'])}",
         f"- Scorer disagreements: {summary['scorer_disagreement_count']}", "",
         "## Run manifest", ""]
    for key, value in manifest_items(manifest):
        L.append(f"- {key}: `{esc(value)}`")
    L += ["", "## Risk register", "",
          "Sorted by exposure-adjusted risk, highest first.", "",
          "| Rank | ID | Family | Outcome | Adjusted risk | Blast radius | Controls |",
          "|---|---|---|---|---|---|---|"]
    for rank, r in enumerate(results, 1):
        cw = rows.get(r["family"], {})
        flag = " (unverified)" if cw and not cw.get("verified") else ""
        L.append(f"| {rank} | {esc(r['test_id'])} | {esc(r['family'])} | {esc(r['outcome'])} | "
                 f"{r['exposure_adjusted_residual_risk_score']} | {_join(r['blast_radius'])} | "
                 f"{_join(cw.get('owasp_llm_2025'))}; {_join(cw.get('mitre_atlas'))}{flag} |")
    L += ["", "## Findings", ""]
    for r in results:
        cw = rows.get(r["family"])
        L += [f"### {esc(r['test_id'])}: {esc(r['family'])}", "",
              f"- Outcome: {esc(r['outcome'])} (severity {esc(r['severity'])})",
              f"- Adjusted risk: {r['exposure_adjusted_residual_risk_score']} "
              f"(inherent {r['inherent_risk']}, residual {r['residual_risk_score']}, "
              f"exposure factor {r['exposure_factor']})",
              f"- Blast radius: {_join(r['blast_radius'])}",
              f"- Canary `{esc(r['canary'])}` present in response: {'yes' if r['canary_present'] else 'no'}"]
        rate = _rate(r)
        if rate:
            L.append(f"- Trials: {rate}")
        L += [f"- Case text: {esc(r['prompt'], RESPONSE_LIMIT)}",
              f"- Response: {esc(r['response'], RESPONSE_LIMIT)}",
              f"- Scorer rationale: {esc(r['rationale'], RESPONSE_LIMIT)}"]
        if cw is None:
            L.append("- Controls: no crosswalk row for this family")
        else:
            status = "verified" if cw.get("verified") else "**unverified**"
            L += [f"- Mapping status: {status}",
                  f"- OWASP LLM 2025: {_join(cw.get('owasp_llm_2025'))}",
                  f"- MITRE ATLAS: {_join(cw.get('mitre_atlas'))}",
                  f"- ISO themes (42001): {_join(cw.get('iso_themes_42001'))}",
                  f"- ISO themes (27001): {_join(cw.get('iso_themes_27001'))}"]
            for ref in cw.get("uk", []):
                L.append(f"- UK: {esc(ref.get('source', ''))}, {esc(ref.get('ref', ''))}")
        L.append("")
    L += ["## Limits", ""] + _limits(manifest) + [""]
    return "\n".join(L)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Markdown risk register from a results file.")
    parser.add_argument("results", type=Path, help="Results JSON written by tester.test_runner.")
    parser.add_argument("--format", choices=["md", "html"], default="md")
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--output", "--out", type=Path, default=None, help="Write here instead of stdout.")
    args = parser.parse_args()
    try:
        summary = json.loads(args.results.read_text(encoding="utf-8"))
        crosswalk = json.loads(args.crosswalk.read_text(encoding="utf-8"))
        if args.format == "html":
            from tester.report_html import render_html, scorer_panel_data
            text = render_html(summary, crosswalk, scorer=scorer_panel_data())
        else:
            text = render_report(summary, crosswalk)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.error(f"cannot build report: {error}")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
