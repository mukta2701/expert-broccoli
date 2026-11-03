"""Build the 'refusal that still leaks' case study from real scorers and stored evidence.

Verdicts for synthetic examples are computed by running both scorers at
generation time. Real replies are read from the evidence file, never copied here.
"""

from __future__ import annotations

import json
from pathlib import Path

from tester.scoring_criteria import load_cases, score_response, score_response_baseline

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASE_STUDY = ROOT / "data" / "case_study.json"
SYNTHETIC_LABEL = "Synthetic"
REAL_LABEL = "Real reply from llama3.2:3b (one model, one machine)"
NOTE = ("The real run found no leak because the protected canary was never in the model's context. "
        "The synthetic examples show what the scorers do when a canary is present. "
        "They are not observed model behaviour.")


def build_case_study(evidence=None, path=DEFAULT_CASE_STUDY) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    evidence_path = Path(evidence) if evidence else ROOT / spec["evidence_file"]
    summary = json.loads(evidence_path.read_text(encoding="utf-8"))
    cases = {c.test_id: c for c in load_cases()}
    stored = {r["test_id"]: r for r in summary["results"]}
    examples = []
    for item in spec["synthetic"]:
        case = cases[item["case_id"]]
        reply = item["reply_text"].replace("{canary}", case.canary)
        new, old = score_response(case, reply), score_response_baseline(case, reply)
        examples.append({"label": SYNTHETIC_LABEL, "title": item["title"], "case_id": case.test_id,
                         "case_text": case.prompt, "reply": reply, "meaning": item["meaning"],
                         "old": (old.outcome, old.rationale), "new": (new.outcome, new.rationale)})
    for item in spec["real"]:
        row = stored[item["case_id"]]
        examples.append({"label": REAL_LABEL, "title": item["title"], "case_id": row["test_id"],
                         "case_text": row["prompt"], "reply": row["response"], "meaning": item["meaning"],
                         "old": (row["baseline_outcome"], row["baseline_rationale"]),
                         "new": (row["outcome"], row["rationale"])})
    return {"note": NOTE, "examples": examples}
