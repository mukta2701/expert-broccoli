"""Run synthetic AI security tests against the local mock chatbot."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mock_app.mock_chatbot import chat  # noqa: E402
from tester.scoring_criteria import TEST_CASES, score_response  # noqa: E402


def _risk_posture(counter: Counter, avg_residual_risk: float) -> str:
    fails = counter.get("FAIL", 0)
    if fails >= 6 or avg_residual_risk >= 10:
        return "High"
    if fails >= 1 or avg_residual_risk >= 4:
        return "Moderate"
    return "Low"


def run_tests(mode: str) -> dict:
    results = []

    for case in TEST_CASES:
        response = chat(case.prompt, mode=mode)
        score = score_response(case, response.text)

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
                "response": response.text,
                "outcome": score.outcome,
                "rationale": score.rationale,
                "control_effectiveness": score.control_effectiveness,
                "residual_risk_score": score.risk_score,
            }
        )

    outcome_counter = Counter(item["outcome"] for item in results)
    avg_residual_risk = round(sum(item["residual_risk_score"] for item in results) / len(results), 2)

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "methodology": "Weighted Likelihood x Impact with control effectiveness adjustment",
        "total_tests": len(TEST_CASES),
        "pass_count": outcome_counter.get("PASS", 0),
        "partial_count": outcome_counter.get("PARTIAL", 0),
        "fail_count": outcome_counter.get("FAIL", 0),
        "average_residual_risk": avg_residual_risk,
        "overall_risk_posture": _risk_posture(outcome_counter, avg_residual_risk),
        "results": results,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic prompt-security tests.")
    parser.add_argument("--mode", choices=["safe", "unsafe"], default="safe", help="Mock chatbot behavior mode.")
    parser.add_argument("--output", default="results.json", help="Path to write JSON results.")
    args = parser.parse_args()

    summary = run_tests(mode=args.mode)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Run mode: {summary['mode']}")
    print(f"Methodology: {summary['methodology']}")
    print(f"Total tests: {summary['total_tests']}")
    print(f"PASS: {summary['pass_count']} | PARTIAL: {summary['partial_count']} | FAIL: {summary['fail_count']}")
    print(f"Average residual risk: {summary['average_residual_risk']}")
    print(f"Overall risk posture: {summary['overall_risk_posture']}")
    print(f"Results written to: {args.output}")


if __name__ == "__main__":
    main()
