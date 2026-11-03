"""compare: side-by-side page for two or more run folders."""

import base64
import contextlib
import hashlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from tester import compare
from tester.test_runner import run_tests

HOSTILE = '<script>alert(1)</script> <img src=x onerror=alert(2)> <a href="javascript:alert(3)">go</a>'


def write_run(root, name, mode, trials, edit=None):
    summary = run_tests(mode=mode, trials=trials)
    if edit:
        edit(summary)
    folder = Path(root) / name
    folder.mkdir()
    (folder / "results.json").write_text(json.dumps(summary), encoding="utf-8")
    (folder / "results.manifest.json").write_text(json.dumps(summary["manifest"]), encoding="utf-8")
    return folder, summary


def page(*folders, now="T0"):
    return compare.render_compare([compare.load_run(f) for f in folders], now=now)


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_rows_columns_and_leak_counts(self):
        safe, s1 = write_run(self.tmp.name, "a", "safe", 2)
        unsafe, s2 = write_run(self.tmp.name, "b", "unsafe", 1)
        html_text = page(safe, unsafe)
        n_cases = len(s1["results"])
        self.assertEqual(html_text.count('<tr class="case">'), n_cases)
        self.assertEqual(html_text.count('<th scope="col" class="run">'), 2)
        leaks_a = sum(r["trials"]["attack_successes"] for r in s1["results"])
        leaks_b = sum(1 for r in s2["results"] if r["outcome"] == "FAIL")
        self.assertGreater(leaks_b, 0)
        self.assertIn(f"leaked {leaks_a} of {2 * n_cases}", html_text)
        self.assertIn(f"leaked {leaks_b} of {n_cases}", html_text)
        self.assertIn("illustrative", html_text)
        self.assertIn("an anecdote, not a rate or a safety verdict", html_text)
        self.assertIn("reply shown is trial 1 of 2", html_text)

    def test_reply_expands_and_is_escaped(self):
        def edit(s):
            s["results"][0]["response"] = HOSTILE
        folder, s = write_run(self.tmp.name, "h", "safe", 1, edit)
        text = page(folder, folder)
        self.assertNotIn("<script", text)
        self.assertNotIn("<img", text)
        self.assertNotIn("javascript:", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("<details>", text)

    def test_long_reply_capped(self):
        folder, _ = write_run(self.tmp.name, "l", "safe", 1,
                              lambda s: s["results"][0].update(response="x" * 5000))
        self.assertNotIn("x" * 400, page(folder, folder))

    def test_deterministic_offline_csp(self):
        a, _ = write_run(self.tmp.name, "a", "safe", 1)
        b, _ = write_run(self.tmp.name, "b", "unsafe", 1)
        one, two = page(a, b, now="X"), page(a, b, now="Y")
        strip = lambda t: re.sub(r"Report timestamp \(varies\): \S+", "", t)
        self.assertEqual(strip(one), strip(two))
        self.assertNotRegex(one, r"<script|src=|https?://|<link")
        digest = base64.b64encode(hashlib.sha256(re.search(r"<style>(.*?)</style>", one, re.S).group(1).encode()).digest()).decode()
        self.assertIn(f"style-src 'sha256-{digest}'", one)
        self.assertIn("prefers-color-scheme: dark", one)

    def test_different_case_sets_show_gap(self):
        def drop(s):
            s["results"] = s["results"][1:]
        a, s = write_run(self.tmp.name, "a", "safe", 1)
        b, _ = write_run(self.tmp.name, "b", "safe", 1, drop)
        text = page(a, b)
        self.assertEqual(text.count("not run"), 1 + 1)  # one cell plus the legend note
        self.assertEqual(text.count('<tr class="case">'), len(s["results"]))

    def test_duplicate_labels_disambiguated(self):
        a, _ = write_run(self.tmp.name, "a", "safe", 1)
        b, _ = write_run(self.tmp.name, "b", "safe", 1)
        self.assertIn("#2", page(a, b))

    def test_cli_errors_and_single_run_warning(self):
        a, _ = write_run(self.tmp.name, "a", "safe", 1)
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        bad = Path(self.tmp.name) / "bad"
        bad.mkdir()
        (bad / "results.json").write_text("{nope", encoding="utf-8")
        for target in (empty, bad):
            err = io.StringIO()
            with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
                compare.main([str(a), str(target), "--output", str(Path(self.tmp.name) / "o.html")])
            self.assertIn(target.name, err.getvalue())
        out = Path(self.tmp.name) / "one.html"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            compare.main([str(a / "results.json"), "--output", str(out)])
        self.assertIn("nothing is being compared", err.getvalue())
        self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
