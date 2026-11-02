"""Markdown risk register from a results file."""

import copy
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tester.report import render_report
from tester.test_runner import run_tests

ROOT = Path(__file__).resolve().parent.parent


def strip_timestamp(text):
    return "\n".join(l for l in text.splitlines() if not l.startswith("Report timestamp (varies):"))


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = {m: run_tests(m) for m in ("safe", "unsafe")}
        cls.crosswalk = json.loads((ROOT / "data" / "framework_crosswalk.json").read_text(encoding="utf-8"))

    def test_lists_all_cases_with_fields_in_both_modes(self):  # AC a, e
        for mode, run in self.runs.items():
            text = render_report(run, self.crosswalk)
            self.assertEqual(len(run["results"]), 16)
            for r in run["results"]:
                self.assertIn(r["test_id"], text)
                self.assertIn("LLM0", text)
                self.assertIn("AML.T", text)
            self.assertIn("Blast radius", text)
            self.assertIn("Adjusted risk", text)
            self.assertIn("Canary", text)
            self.assertIn("## Limits", text)

    def test_sorted_by_adjusted_risk_highest_first(self):  # AC a
        run = self.runs["unsafe"]
        text = render_report(run, self.crosswalk)
        register = text.split("## Risk register")[1].split("## Findings")[0]
        ids = re.findall(r"\| (PI-\d+) \|", register)
        self.assertEqual(len(ids), 16)
        by_id = {r["test_id"]: r["exposure_adjusted_residual_risk_score"] for r in run["results"]}
        scores = [by_id[i] for i in ids]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_unverified_rows_marked(self):  # AC b
        text = render_report(self.runs["safe"], self.crosswalk)
        unverified = [e["family"] for e in self.crosswalk["entries"] if not e["verified"]]
        self.assertEqual(len(unverified), 2)
        self.assertEqual(text.count("**unverified**"), 2)
        cw = copy.deepcopy(self.crosswalk)
        for e in cw["entries"]:
            e["verified"] = True
        all_ok = render_report(self.runs["safe"], cw)
        self.assertNotIn("**unverified**", all_ok)
        self.assertNotIn("(unverified)", all_ok)

    def test_manifest_and_limits(self):  # AC c
        mock = render_report(self.runs["safe"], self.crosswalk)
        m = self.runs["safe"]["manifest"]
        for value in (m["cases_sha256"], m["tool_version"], m["scorer_version"], m["mode"]):
            self.assertIn(str(value), mock)
        self.assertIn("target is a mock", mock)
        self.assertIn("illustrative prioritisation score", mock)
        self.assertIn("not a compliance verdict", mock)
        real = copy.deepcopy(self.runs["safe"])
        real["manifest"]["target"] = "openai_compat"
        real["manifest"]["model"] = "tiny-model"
        text = render_report(real, self.crosswalk)
        self.assertIn("one small model", text)
        self.assertNotIn("target is a mock", text)
        lowered = (mock + text).lower()
        for banned in ("audit-ready", "certified", "proves safe"):
            self.assertNotIn(banned, lowered)

    def test_deterministic_and_timestamp_on_one_line(self):  # AC d
        a = render_report(self.runs["unsafe"], self.crosswalk, now="2026-01-01T00:00:00+00:00")
        b = render_report(self.runs["unsafe"], self.crosswalk, now="2030-05-05T00:00:00+00:00")
        self.assertNotEqual(a, b)
        self.assertEqual(strip_timestamp(a), strip_timestamp(b))
        self.assertEqual(a.count("Report timestamp (varies):"), 1)

    def test_cli_twice_identical_and_trials(self):  # AC d, e
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps(run_tests("unsafe", trials=5)), encoding="utf-8")
            outs = []
            for _ in range(2):
                p = subprocess.run([sys.executable, "-m", "tester.report", str(path), "--format", "md"],
                                   cwd=str(ROOT), capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)
                outs.append(strip_timestamp(p.stdout))
            self.assertEqual(outs[0], outs[1])
            self.assertRegex(outs[0], r"\d/5")
            self.assertIn("Wilson 95%", outs[0])
        self.assertNotIn("Wilson", render_report(self.runs["safe"], self.crosswalk))

    def test_response_text_is_neutralised(self):  # honest wording / injection
        run = copy.deepcopy(self.runs["unsafe"])
        run["results"][0]["response"] = "[click](http://evil.example) <img src=x onerror=1>\n# Heading"
        run["results"][0]["prompt"] = "<script>alert(1)</script> [a](b)"
        text = render_report(run, self.crosswalk)
        self.assertNotIn("<img", text)
        self.assertNotIn("<script", text)
        self.assertNotIn("[click](", text)
        self.assertNotIn("\n# Heading", text)


if __name__ == "__main__":
    unittest.main()
