"""Repeated trials and the Wilson interval."""

import unittest

from tester.stats import wilson_interval
from tester.targets import MockTarget
from tester.test_runner import run_tests


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

    def test_manifest_records_target_model_temperature_trials(self):
        manifest = run_tests("safe", trials=3)["manifest"]
        self.assertEqual(manifest["target_type"], "mock")
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

    def test_invalid_trials_rejected(self):
        for bad in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                run_tests("safe", trials=bad)


if __name__ == "__main__":
    unittest.main()
