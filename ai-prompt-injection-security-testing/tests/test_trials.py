"""Repeated trials and the Wilson interval."""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tester.stats import wilson_interval
from tester.targets import MockTarget, OpenAICompatTarget
from tester import test_runner
from tester.test_runner import run_tests
from tests.test_targets import fake_api


class WilsonIntervalTests(unittest.TestCase):
    def assertInterval(self, successes, trials, low, high):
        got_low, got_high = wilson_interval(successes, trials)
        self.assertAlmostEqual(got_low, low, places=4)
        self.assertAlmostEqual(got_high, high, places=4)

    def test_known_values(self):
        self.assertInterval(5, 5, 0.5655, 1.0)
        self.assertInterval(0, 5, 0.0, 0.4345)
        self.assertInterval(3, 10, 0.1078, 0.6032)

    def test_rejects_bad_counts(self):
        for successes, trials in ((1, 0), (-1, 5), (6, 5)):
            with self.assertRaises(ValueError):
                wilson_interval(successes, trials)


class TrialsRunTests(unittest.TestCase):
    def test_five_trials_report_count_and_interval(self):
        summary = run_tests("unsafe", trials=5)
        for result in summary["results"]:
            trial = result["trials"]
            self.assertEqual(trial["n"], 5)
            self.assertEqual(len(trial["outcomes"]), 5)
            self.assertEqual(trial["attack_successes"], 5 if result["outcome"] == "FAIL" else 0)
            self.assertEqual(len(trial["wilson_95"]), 2)

    def test_partial_is_not_an_attack_success(self):
        class Score:
            outcome, rationale, control_effectiveness = "PARTIAL", "x", 0.5
            risk_score = exposure_factor = exposure_adjusted_risk_score = 1
        with patch.object(test_runner, "score_response", return_value=Score):
            results = run_tests("safe", trials=2)["results"]
        self.assertTrue(all(r["trials"]["attack_successes"] == 0 for r in results))
        self.assertIn("PARTIAL not counted", test_runner.TRIALS_HELP)

    def test_manifest_records_target_model_temperature_trials(self):
        manifest = run_tests("safe", trials=3)["manifest"]
        self.assertEqual(manifest["target"], "mock")
        self.assertNotIn("target_type", manifest)
        self.assertIsNone(manifest["model"])
        self.assertIsNone(manifest["temperature"])
        self.assertEqual(manifest["trials"], 3)

    def test_default_single_trial_matches_current_output(self):
        for mode, fails in (("safe", 0), ("unsafe", 16)):
            summary = run_tests(mode)
            self.assertEqual(summary["manifest"]["trials"], 1)
            self.assertEqual(summary["fail_count"], fails)
            self.assertTrue(all("trials" not in r for r in summary["results"]))
            self.assertEqual(summary["results"], run_tests(mode, trials=1, target=MockTarget(mode))["results"])

    def test_http_target_temperature_is_sent_and_recorded_only_when_set(self):
        with TemporaryDirectory() as tmp, fake_api(reply_text="No.") as (url, requests):
            cases = test_runner.DEFAULT_CASES_PATH
            manifests = []
            for temperature in (None, 0.7):
                target = OpenAICompatTarget(url, "toy", requests_per_second=1000)
                manifests.append(run_tests("safe", target=target, cases_path=cases,
                                           temperature=temperature)["manifest"])
        self.assertEqual(manifests[0]["temperature"], "server default")
        self.assertEqual(manifests[1]["temperature"], 0.7)
        self.assertEqual(manifests[1]["model"], "toy")
        first, second = requests[:16], requests[16:]
        self.assertTrue(all("temperature" not in body for _, _, body in first))
        self.assertTrue(all(body["temperature"] == 0.7 for _, _, body in second))

    def test_invalid_trials_rejected(self):
        for bad in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                run_tests("safe", trials=bad)


if __name__ == "__main__":
    unittest.main()
