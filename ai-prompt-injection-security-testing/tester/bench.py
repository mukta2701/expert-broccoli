"""One command: run the cases, show live progress, save everything in a run folder."""

from __future__ import annotations

import argparse
import json
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tester.report import DEFAULT_CROSSWALK, render_report  # noqa: E402
from tester.report_html import render_html, scorer_panel_data  # noqa: E402
from tester.scoring_criteria import DEFAULT_CASES_PATH  # noqa: E402
from tester.targets import MockTarget, OpenAICompatTarget  # noqa: E402
from tester.test_runner import run_tests  # noqa: E402

_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b[@-_]")
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def safe_text(value, limit: int) -> str:
    """One line, no ANSI or control characters: model replies are untrusted."""
    text = _CONTROL.sub("", _ANSI.sub("", " ".join(str(value).split())))
    return text if len(text) <= limit else text[:limit] + "..."


def folder_name(when: datetime, label: str) -> str:
    return f"{when:%Y-%m-%d_%H%M}_{re.sub(r'[^A-Za-z0-9._-]+', '-', label).strip('-') or 'run'}"


class Progress:
    """Prints one block per finished request; the tally uses scorer outcomes, not a verdict."""

    def __init__(self, out):
        self.out = out
        self.tally = {"PASS": 0, "FAIL": 0, "PARTIAL": 0}

    def __call__(self, e: dict) -> None:
        self.tally[e["outcome"]] = self.tally.get(e["outcome"], 0) + 1
        t = self.tally
        width = len(str(e["total"]))
        lines = [
            f"[{e['index']:>{width}}/{e['total']}] {safe_text(e['test_id'], 20)} {safe_text(e['family'], 40)}"
            f"  trial {e['trial']}/{e['trials']}  {e['seconds']:.1f}s",
            f"  sent:  \"{safe_text(e['prompt'], 80)}\"",
            f"  reply: \"{safe_text(e['reply'], 100)}\"",
            f"  so far (scorer labels, not a verdict): {t['PASS']} PASS (refused/ok) · "
            f"{t['FAIL']} FAIL (went along) · {t['PARTIAL']} PARTIAL (unclear)",
        ]
        self.out.write("\n".join(lines) + "\n")
        self.out.flush()


def main(argv=None, out=None, open_url=webbrowser.open, now=None) -> int:
    out = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(description="Run the cases with live progress and save a run folder.")
    parser.add_argument("model_name", nargs="?", default="", metavar="MODEL", help="Model name (same as --model).")
    parser.add_argument("--model", default="", help="Model name for openai_compat.")
    parser.add_argument("--target", choices=["mock", "openai_compat"], default=None)
    parser.add_argument("--mode", choices=["safe", "unsafe"], default="safe", help="Mock chatbot behaviour.")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--requests-per-second", type=float, default=1)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--i-have-authorization", action="store_true", help="Allow non-loopback targets.")
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--open", action="store_true", help="Open the HTML report when done.")
    args = parser.parse_args(argv)

    model = args.model or args.model_name
    target_name = args.target or ("openai_compat" if model else "mock")
    try:
        target = (MockTarget(args.mode) if target_name == "mock" else OpenAICompatTarget(
            args.base_url, model, i_have_authorization=args.i_have_authorization,
            timeout=args.timeout, requests_per_second=args.requests_per_second))
        summary = run_tests(mode=args.mode, cases_path=args.cases, target=target, trials=args.trials,
                            temperature=args.temperature, progress=Progress(out))
        crosswalk = json.loads(Path(DEFAULT_CROSSWALK).read_text(encoding="utf-8"))
    except Exception as error:  # surface any run failure as a clean message, no partial folder
        parser.error(f"run failed: {safe_text(error, 300)}")

    when = now or datetime.now()
    run_dir = args.runs_dir / folder_name(when, f"mock-{args.mode}" if target_name == "mock" else model)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (run_dir / "results.manifest.json").write_text(json.dumps(summary["manifest"], indent=2) + "\n", encoding="utf-8")
    (run_dir / "risk_register.md").write_text(render_report(summary, crosswalk), encoding="utf-8")
    html_path = run_dir / "evidence_pack.html"
    html_path.write_text(render_html(summary, crosswalk, scorer=scorer_panel_data()), encoding="utf-8")

    out.write(f"Run folder: {run_dir}\n")
    out.flush()
    if args.open:
        open_url(html_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
