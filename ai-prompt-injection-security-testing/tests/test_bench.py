"""bench: live progress, run folder, mock target, untouched test_runner output."""

import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tester import bench
from tests.test_targets import fake_api

ROOT = Path(__file__).resolve().parent.parent


class RecordingOut(io.StringIO):
    """Notes how many requests the server had seen when each block header was printed."""

    def __init__(self, requests):
        super().__init__()
        self.requests, self.seen = requests, []

    def write(self, text):
        if text.startswith("["):
            self.seen.append(len(self.requests))
        return super().write(text)


class BenchTests(unittest.TestCase):
    def test_progress_block_printed_before_next_request(self):
        with fake_api(reply_text="I cannot help \x1b[31mwith that\x1b[0m") as (url, requests), \
                tempfile.TemporaryDirectory() as runs:
            out = RecordingOut(requests)
            bench.main(["--model", "toy", "--base-url", url, "--trials", "2", "--requests-per-second", "1000",
                        "--runs-dir", runs], out=out)
        self.assertEqual(len(out.seen), 32)
        self.assertEqual(out.seen, list(range(1, 33)))  # block k printed when exactly k requests were made
        text = out.getvalue()
        self.assertIn("trial 2/2", text)
        self.assertIn("  sent:  \"", text)
        self.assertIn("scorer labels, not a verdict", text)
        self.assertNotIn("\x1b", text)

    def test_run_folder_contents_and_no_browser_by_default(self):
        opened = []
        with tempfile.TemporaryDirectory() as runs:
            out = io.StringIO()
            bench.main(["--target", "mock", "--mode", "unsafe", "--trials", "1", "--runs-dir", runs],
                       out=out, open_url=opened.append, now=datetime(2026, 11, 3, 14, 5))
            folder = Path(runs) / "2026-11-03_1405_mock-unsafe"
            names = sorted(p.name for p in folder.iterdir())
            self.assertEqual(names, ["evidence_pack.html", "results.json", "results.manifest.json",
                                     "risk_register.md"])
            self.assertEqual(json.loads((folder / "results.json").read_text())["fail_count"], 16)
            self.assertIn(f"Run folder: {folder}", out.getvalue())
            self.assertEqual(opened, [])
            bench.main(["--target", "mock", "--trials", "1", "--runs-dir", runs, "--open"],
                       out=io.StringIO(), open_url=opened.append)
            self.assertEqual(len(opened), 1)
            self.assertTrue(opened[0].endswith("evidence_pack.html"))

    def test_test_runner_output_unchanged_and_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, "-m", "tester.test_runner", "--mode", "unsafe",
                                     "--output", str(Path(tmp) / "r.json")],
                                    cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertNotIn("sent:", result.stdout)
        self.assertTrue(result.stdout.startswith("Target: mock\nRun mode: unsafe\n"))

    def test_safe_text_strips_control_and_collapses(self):
        self.assertEqual(bench.safe_text("a\n\x1b[2Jb\x07\tc", 50), "a b c")
        self.assertEqual(bench.safe_text("x" * 20, 5), "xxxxx...")


if __name__ == "__main__":
    unittest.main()
