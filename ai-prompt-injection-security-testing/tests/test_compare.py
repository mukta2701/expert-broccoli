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
    counter = __import__("itertools").count()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_rows_columns_and_leak_counts(self):
        planted = lambda s: s["manifest"].update(system_variant="weak")
        safe, s1 = write_run(self.tmp.name, "a", "safe", 2, planted)
        unsafe, s2 = write_run(self.tmp.name, "b", "unsafe", 1, planted)
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

    def _bad(self, edit, needle):
        folder, _ = write_run(self.tmp.name, f"x{next(self.counter)}", "safe", 2, edit)
        with self.assertRaises(ValueError) as ctx:
            compare.load_run(folder)
        self.assertIn(needle, str(ctx.exception))

    def test_bad_inputs_give_clear_messages(self):
        self._bad(lambda s: s["results"][0]["trials"].pop("attack_successes"), "attack_successes")
        self._bad(lambda s: s["results"][0]["trials"].pop("n"), "'n'")
        self._bad(lambda s: s.update(results=[]), "no results")

    def test_non_object_manifest_uses_fallback(self):
        folder, _ = write_run(self.tmp.name, "m", "safe", 1, lambda s: s.update(manifest="oops"))
        self.assertIn("manifest missing", compare.load_run(folder)["label"])

    def test_unwritable_output_is_parser_error(self):
        a, _ = write_run(self.tmp.name, "a", "safe", 1)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            compare.main([str(a), str(a), "--output", str(Path(self.tmp.name) / "nodir" / "o.html")])
        self.assertIn("cannot write", err.getvalue())

    def test_wording_depends_on_planted_canary(self):
        def planted(s):
            s["manifest"]["system_variant"] = "weak"
        a, _ = write_run(self.tmp.name, "a", "unsafe", 1)
        b, _ = write_run(self.tmp.name, "b", "unsafe", 1, planted)
        self.assertIn("no secret · FAIL 1 of 1", page(a, a))
        self.assertNotIn("leaked", page(a, a).split("<tbody>")[1])
        self.assertIn("leaked 1 of 1", page(b, b))
        self.assertNotIn("no secret", page(b, b).split("<tbody>")[1])

    def test_no_secret_cells_are_neutral_never_green(self):
        a, _ = write_run(self.tmp.name, "a", "safe", 2)  # system variant n/a: nothing planted
        body = page(a, a).split("<tbody>")[1]
        self.assertIn("badge neutral", body)
        self.assertNotIn("out-pass", body)
        self.assertNotIn("&#10003;", body)
        self.assertIn("no secret · FAIL 0 of 2", body)

    def test_planted_zero_leaks_is_green(self):
        a, _ = write_run(self.tmp.name, "a", "safe", 2, lambda s: s["manifest"].update(system_variant="strong"))
        body = page(a, a).split("<tbody>")[1]
        self.assertIn("badge out-pass", body)
        self.assertIn("leaked 0 of 2", body)

    def test_two_line_header_and_layout_css(self):
        a, _ = write_run(self.tmp.name, "a", "safe", 2, lambda s: s["manifest"].update(system_variant="strong"))
        text = page(a, a)
        self.assertIn('<th scope="col" class="run"><span class="mname">mock (safe)</span>'
                      '<span class="msub">system strong · temp n/a · 2 trials · ', text)
        self.assertIn("table-layout:fixed", text)
        self.assertIn("min(1800px,96vw)", text)
        self.assertIn("scroll sideways to see more runs", text)
        self.assertNotIn("<caption", text)

    def test_bidi_controls_stripped(self):
        folder, _ = write_run(self.tmp.name, "bd", "safe", 1,
                              lambda s: s["results"][0].update(response="ok \u202eevil\u2066 x"))
        text = page(folder, folder)
        for ch in "\u202a\u202e\u2066\u2069":
            self.assertNotIn(ch, text)


if __name__ == "__main__":
    unittest.main()
