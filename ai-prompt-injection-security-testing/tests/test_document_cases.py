"""Hidden-instruction-in-a-document cases (issue 42)."""

import json
import re
import subprocess
import unittest
from pathlib import Path

from tester.scoring_criteria import load_cases
from tester.test_runner import run_tests

ROOT = Path(__file__).resolve().parents[1]
DOC_CASES = ROOT / "data" / "cases_document.json"
CASES = ROOT / "data" / "cases.json"
CROSSWALK = ROOT / "data" / "framework_crosswalk.json"


class DocumentCaseTests(unittest.TestCase):
    def test_loads_with_canary_and_expected_behaviour(self):
        cases = load_cases(DOC_CASES)
        self.assertTrue(5 <= len(cases) <= 6)
        self.assertEqual([c.test_id for c in cases],
                         ["DOC-%02d" % n for n in range(1, len(cases) + 1)])
        for case in cases:
            self.assertTrue(case.canary.startswith("HARMLESS_CANARY_DOC_"))
            self.assertTrue(case.expected_behaviour["description"])
            self.assertTrue(case.expected_behaviour["required_all"])

    def test_families_exist_in_crosswalk(self):
        known = {e["family"] for e in json.loads(CROSSWALK.read_text())["entries"]}
        for case in load_cases(DOC_CASES):
            self.assertIn(case.family, known)

    def test_mock_safe_mode_is_deterministic(self):
        first = run_tests("safe", cases_path=DOC_CASES)["results"]
        second = run_tests("safe", cases_path=DOC_CASES)["results"]
        self.assertEqual([r["response"] for r in first], [r["response"] for r in second])
        self.assertFalse(any(r["canary_present"] for r in first))
        self.assertEqual([r["outcome"] for r in first],
                         ["PARTIAL"] * 5 + ["PASS"])

    def test_mock_unsafe_mode_leaks_every_canary(self):
        results = run_tests("unsafe", cases_path=DOC_CASES)["results"]
        self.assertEqual([r["outcome"] for r in results], ["FAIL"] * len(results))
        for result in results:
            self.assertTrue(result["canary_present"])
            self.assertIn(result["canary"], result["response"])

    def test_existing_cases_unchanged(self):
        self.assertEqual(len(json.loads(CASES.read_text())["cases"]), 16)
        self.assertEqual(len(load_cases(CASES)), 16)
        repo = ROOT.parent
        staged = subprocess.run(
            ["git", "-C", str(repo), "show", "origin/staging:" + CASES.relative_to(repo).as_posix()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if staged.returncode != 0:
            self.skipTest("origin/staging not available")
        self.assertEqual(CASES.read_bytes(), staged.stdout)

    def test_case_text_is_harmless(self):
        raw = DOC_CASES.read_text()
        self.assertNotIn("http://", raw)
        self.assertNotIn("https://", raw)
        self.assertNotIn("@", raw)
        self.assertIsNone(re.search(r"\d[\d\s().-]{6,}\d", raw))


if __name__ == "__main__":
    unittest.main()
