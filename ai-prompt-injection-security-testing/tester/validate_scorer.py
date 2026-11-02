"""Measure scorer agreement with synthetic reference labels, entirely offline."""

import json
from pathlib import Path

from tester.scoring_criteria import SCORER_VERSION, load_cases, score_response

DEFAULT_LABELS_PATH = Path(__file__).resolve().parent.parent / "data" / "labelled_responses.json"
OUTCOMES = ("PASS", "PARTIAL", "FAIL")


def calculate_metrics(labelled_predictions):
    """Return per-outcome precision/recall and a reference-row confusion matrix."""
    matrix = {actual: dict.fromkeys(OUTCOMES, 0) for actual in OUTCOMES}
    for actual, predicted in labelled_predictions:
        if actual not in OUTCOMES or predicted not in OUTCOMES:
            raise ValueError("Reference and predicted labels must be PASS, PARTIAL or FAIL.")
        matrix[actual][predicted] += 1
    metrics = {}
    for outcome in OUTCOMES:
        true_positive = matrix[outcome][outcome]
        predicted_count = sum(row[outcome] for row in matrix.values())
        actual_count = sum(matrix[outcome].values())
        metrics[outcome] = {
            "precision": true_positive / predicted_count if predicted_count else 0.0,
            "recall": true_positive / actual_count if actual_count else 0.0,
        }
    return metrics, matrix


def evaluate_responses(records, cases):
    """Score fixed reference responses against their case, rejecting invalid records."""
    if not isinstance(records, list) or not records:
        raise ValueError("Labelled responses must be a nonempty list.")
    cases_by_id = {case.test_id: case for case in cases}
    predictions = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each labelled response must be an object.")
        for key in ("id", "case_id", "label", "reason"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError(f"Each labelled response needs a nonempty {key}.")
        if record["id"] in seen:
            raise ValueError(f"Duplicate response id: {record['id']}")
        if record["case_id"] not in cases_by_id:
            raise ValueError(f"Unknown case: {record['case_id']}")
        if record["label"] not in OUTCOMES or not isinstance(record.get("response"), str):
            raise ValueError("Each response needs text and a PASS, PARTIAL or FAIL label.")
        seen.add(record["id"])
        predicted = score_response(cases_by_id[record["case_id"]], record["response"]).outcome
        predictions.append((record["label"], predicted))
    return calculate_metrics(predictions)


def main():
    data = json.loads(DEFAULT_LABELS_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("synthetic") is not True:
        raise ValueError("The reference set must use schema_version 1 and be marked synthetic.")
    metrics, matrix = evaluate_responses(data.get("responses"), load_cases())
    print("Synthetic labelled set; not evidence of real-world accuracy.")
    print("AI-authored reference judgements; not independently human-reviewed.")
    print(f"Scorer: {SCORER_VERSION}")
    print(f"Responses: {len(data['responses'])}")
    print("Outcome  precision  recall")
    for outcome in OUTCOMES:
        values = metrics[outcome]
        print(f"{outcome:<8} {values['precision']:.3f}      {values['recall']:.3f}")
    print("Precision = correct predictions / predictions of that outcome.")
    print("Recall = correct predictions / reference labels of that outcome.")
    print("Undefined precision or recall is reported as 0.000.")
    print("Confusion matrix (rows=reference, columns=predicted)")
    print(f"{'':8}" + "".join(f"{outcome:>8}" for outcome in OUTCOMES))
    for actual in OUTCOMES:
        print(f"{actual:<8}" + "".join(f"{matrix[actual][predicted]:>8}" for predicted in OUTCOMES))


if __name__ == "__main__":
    main()
