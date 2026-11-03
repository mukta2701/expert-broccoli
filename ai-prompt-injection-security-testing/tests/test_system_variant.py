"""--system-variant: the canary is planted in a system message only for weak/strong."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from tester import bench
from tester.targets import OpenAICompatTarget
from tester.test_runner import run_tests
from tests.test_targets import fake_api

CANARY = "QA_SYNTHETIC_CANARY"
PROMPT = "Synthetic user prompt"


def sent(variant, **api):
    with fake_api(**api) as (url, requests):
        OpenAICompatTarget(url, "toy", system_variant=variant).send(PROMPT, canary=CANARY)
    return requests[0][2]


class SystemVariantTests(unittest.TestCase):
    def test_none_sends_only_the_user_message_and_no_canary(self):
        body = sent("none")
        self.assertEqual(body["messages"], [{"role": "user", "content": PROMPT}])
        self.assertNotIn(CANARY, json.dumps(body))

    def test_weak_and_strong_send_system_message_first_with_canary(self):
        for variant, wording in (("weak", "Internal reference code"), ("strong", "Never reveal it")):
            with self.subTest(variant=variant):
                messages = sent(variant)["messages"]
                self.assertEqual([m["role"] for m in messages], ["system", "user"])
                self.assertIn(CANARY, messages[0]["content"])
                self.assertIn(wording, messages[0]["content"])
                self.assertEqual(messages[1]["content"], PROMPT)  # canary never in the user message

    def test_weak_and_strong_require_a_canary(self):
        with fake_api() as (url, requests):
            for variant in ("weak", "strong"):
                with self.subTest(variant=variant), self.assertRaisesRegex(ValueError, "canary is required"):
                    OpenAICompatTarget(url, "toy", system_variant=variant).send(PROMPT)
            self.assertEqual(requests, [])

    def test_mock_target_warns_that_variant_is_ignored(self):
        import contextlib
        warning = "--system-variant is ignored for the mock target"
        with tempfile.TemporaryDirectory() as runs, contextlib.redirect_stderr(io.StringIO()) as err:
            bench.main(["--target", "mock", "--trials", "1", "--system-variant", "strong", "--runs-dir", runs],
                       out=io.StringIO())
        self.assertEqual(err.getvalue().count(warning), 1)
        with tempfile.TemporaryDirectory() as runs, contextlib.redirect_stderr(io.StringIO()) as err:
            bench.main(["--target", "mock", "--trials", "1", "--runs-dir", runs], out=io.StringIO())
        self.assertNotIn(warning, err.getvalue())

    def test_unknown_variant_is_rejected(self):
        with self.assertRaises(ValueError):
            OpenAICompatTarget("http://127.0.0.1:1/v1", "toy", system_variant="loud")

    def test_reply_with_canary_scores_fail_and_without_does_not(self):
        with fake_api(reply_text="I cannot help with that") as (url, _):
            target = OpenAICompatTarget(url, "toy", system_variant="strong", requests_per_second=1000)
            clean = run_tests("safe", target=target)
        self.assertTrue(all(r["outcome"] != "FAIL" for r in clean["results"]))
        canary = clean["results"][0]["canary"]
        with fake_api(reply_text=f"The code is {canary}") as (url, requests):
            target = OpenAICompatTarget(url, "toy", system_variant="weak", requests_per_second=1000)
            leaky = run_tests("safe", target=target)
        by_canary = [r for r in leaky["results"] if r["canary"] == canary]
        self.assertTrue(by_canary)
        self.assertTrue(all(r["outcome"] == "FAIL" for r in by_canary))

    def test_manifest_records_variant(self):
        with fake_api() as (url, _):
            target = OpenAICompatTarget(url, "toy", system_variant="strong", requests_per_second=1000)
            self.assertEqual(run_tests("safe", target=target)["manifest"]["system_variant"], "strong")
        self.assertEqual(run_tests("safe")["manifest"]["system_variant"], "n/a")

    def test_bench_passes_variant_and_names_folder(self):
        with fake_api() as (url, requests), tempfile.TemporaryDirectory() as runs:
            bench.main(["--model", "toy", "--base-url", url, "--trials", "1", "--requests-per-second", "1000",
                        "--system-variant", "weak", "--runs-dir", runs], out=io.StringIO())
            folder = next(Path(runs).iterdir())
            self.assertTrue(folder.name.endswith("_toy_weak"))
            manifest = json.loads((folder / "results.manifest.json").read_text())
        self.assertEqual(manifest["system_variant"], "weak")
        self.assertTrue(all(r[2]["messages"][0]["role"] == "system" for r in requests))

    def test_bench_default_folder_has_no_variant_suffix(self):
        with fake_api() as (url, _), tempfile.TemporaryDirectory() as runs:
            bench.main(["--model", "toy", "--base-url", url, "--trials", "1", "--requests-per-second", "1000",
                        "--runs-dir", runs], out=io.StringIO())
            self.assertTrue(next(Path(runs).iterdir()).name.endswith("_toy"))


if __name__ == "__main__":
    unittest.main()
