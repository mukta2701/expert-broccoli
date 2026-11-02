"""Run synthetic AI security tests against a selected prompt target."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tester import __version__  # noqa: E402
from tester.targets import MockTarget, OpenAICompatTarget, Target  # noqa: E402
from tester.scoring_criteria import (  # noqa: E402
    BASELINE_SCORER_VERSION,
    DEFAULT_CASES_PATH,
    SCORER_VERSION,
    load_case_data,
    score_response,
    score_response_baseline,
)


def _risk_posture(counter: Counter, avg_residual_risk: float) -> str:
    fails = counter.get("FAIL", 0)
    if fails >= 6 or avg_residual_risk >= 10:
        return "High"
    if fails >= 1 or avg_residual_risk >= 4:
        return "Moderate"
    return "Low"


def run_tests(mode: str, seed: int = 0, cases_path: str | Path = DEFAULT_CASES_PATH,
              target: Target | None = None) -> dict:
    if mode not in {"safe", "unsafe"}:
        raise ValueError("mode must be 'safe' or 'unsafe'.")
    if type(seed) is not int:
        raise ValueError("seed must be an integer.")
    target = target if target is not None else MockTarget(mode)
    cases, cases_sha256 = load_case_data(cases_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    manifest = {
        "tool_version": __version__,
        "cases_sha256": cases_sha256,
        "scorer_version": SCORER_VERSION,
        "baseline_scorer_version": BASELINE_SCORER_VERSION,
        "seed": seed,
        "mode": mode,
        "target": target.name,
        "timestamp_utc": timestamp,
    }
    results = []

    for case in cases:
        response = target.send(case.prompt, canary=case.canary)
        score = score_response(case, response.text)
        baseline = score_response_baseline(case, response.text)

        results.append(
            {
                "test_id": case.test_id,
                "family": case.family,
                "severity": case.severity,
                "likelihood": case.likelihood,
                "impact": case.impact,
                "inherent_risk": case.likelihood * case.impact,
                "prompt": case.prompt,
                "expected": case.expected,
                "expected_behaviour": case.expected_behaviour,
                "canary": case.canary,
                "canary_present": case.canary in response.text,
                "blast_radius": case.blast_radius,
                "response": response.text,
                "response_metadata": response.metadata,
                "outcome": score.outcome,
                "rationale": score.rationale,
                "control_effectiveness": score.control_effectiveness,
                "residual_risk_score": score.risk_score,
                "exposure_factor": score.exposure_factor,
                "exposure_adjusted_residual_risk_score": score.exposure_adjusted_risk_score,
                "baseline_outcome": baseline.outcome,
                "baseline_rationale": baseline.rationale,
                "scorer_disagreement": score.outcome != baseline.outcome,
            }
        )

    outcome_counter = Counter(item["outcome"] for item in results)
    avg_residual_risk = round(sum(item["residual_risk_score"] for item in results) / len(results), 2)
    avg_adjusted_risk = round(
        sum(item["exposure_adjusted_residual_risk_score"] for item in results) / len(results), 2
    )

    summary = {
        "timestamp_utc": timestamp,
        "mode": mode,
        "manifest": manifest,
        "methodology": "Likelihood x Impact x (1 - effectiveness) x (1 + reachable capabilities)",
        "total_tests": len(cases),
        "pass_count": outcome_counter.get("PASS", 0),
        "partial_count": outcome_counter.get("PARTIAL", 0),
        "fail_count": outcome_counter.get("FAIL", 0),
        "average_residual_risk": avg_residual_risk,
        "average_exposure_adjusted_residual_risk": avg_adjusted_risk,
        "scorer_disagreement_count": sum(item["scorer_disagreement"] for item in results),
        "overall_risk_posture": _risk_posture(outcome_counter, avg_adjusted_risk),
        "results": results,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic prompt-security tests.")
    parser.add_argument("--mode", choices=["safe", "unsafe"], default="safe", help="Mock chatbot behavior mode.")
    parser.add_argument("--output", default="results.json", help="Path to write JSON results.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="Case data JSON file.")
    parser.add_argument("--seed", type=int, default=0, help="Recorded seed; the local mock is deterministic.")
    parser.add_argument("--target", choices=["mock", "openai_compat"], default="mock")
    parser.add_argument("--base-url", default="http://localhost:11434/v1", help="Chat API base URL.")
    parser.add_argument("--model", default="", help="Model name for openai_compat.")
    parser.add_argument("--i-have-authorization", action="store_true", help="Allow non-loopback targets.")
    parser.add_argument("--timeout", type=float, default=30, help="Socket timeout in seconds.")
    parser.add_argument("--requests-per-second", type=float, default=1, help="Maximum sequential request rate.")
    args = parser.parse_args()

    try:
        target = (MockTarget(args.mode) if args.target == "mock" else OpenAICompatTarget(
            args.base_url, args.model, i_have_authorization=args.i_have_authorization,
            timeout=args.timeout, requests_per_second=args.requests_per_second))
        summary = run_tests(mode=args.mode, seed=args.seed, cases_path=args.cases, target=target)
    except (ValueError, OSError, HTTPException) as error:
        parser.error(str(error))

    output = Path(args.output)
    manifest_path = output.with_suffix(".manifest.json")
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(summary["manifest"], indent=2) + "\n", encoding="utf-8")

    print(f"Target: {summary['manifest']['target']}")
    print(f"Run mode: {summary['mode']}")
    print(f"Methodology: {summary['methodology']}")
    print(f"Total tests: {summary['total_tests']}")
    print(f"PASS: {summary['pass_count']} | PARTIAL: {summary['partial_count']} | FAIL: {summary['fail_count']}")
    print(f"Average residual risk: {summary['average_residual_risk']}")
    print(f"Exposure-adjusted residual risk: {summary['average_exposure_adjusted_residual_risk']}")
    print(f"Scorer disagreements: {summary['scorer_disagreement_count']}")
    print(f"Overall risk posture: {summary['overall_risk_posture']}")
    print(f"Results written to: {args.output}")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
