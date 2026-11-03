"""Single-file HTML evidence pack from a results file."""

import copy
import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory

from tester.report import render_report
from tester.report_html import render_html, scorer_panel_data
from tester.test_runner import run_tests

ROOT = Path(__file__).resolve().parent.parent
STAMP = re.compile(r".*Report timestamp \(varies\):.*\n")


def strip_stamp(text):
    return STAMP.sub("", text)


class Collect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.extend((tag, k, v) for k, v in attrs)


def parse(text):
    p = Collect()
    p.feed(text)
    return p


class HtmlReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = {m: run_tests(m) for m in ("safe", "unsafe")}
        cls.crosswalk = json.loads((ROOT / "data" / "framework_crosswalk.json").read_text(encoding="utf-8"))
        cls.scorer = scorer_panel_data()

    def html(self, mode="unsafe", **kw):
        return render_html(self.runs[mode], self.crosswalk, scorer=self.scorer, **kw)

    def test_offline_no_external_loads_no_script(self):  # AC a
        for mode in self.runs:
            text = self.html(mode)
            self.assertNotIn("http://", text)
            self.assertNotIn("https://", text)
            p = parse(text)
            for tag in ("script", "link", "img", "iframe", "object", "embed", "form", "base", "svg"):
                self.assertNotIn(tag, p.tags)
            for tag, k, v in p.attrs:
                self.assertFalse(k.startswith("on"), (tag, k))
                self.assertNotIn(k, ("src", "srcset", "action", "style"))
                if k == "href":
                    self.assertTrue(v.startswith("#"), v)

    def test_csp_meta(self):
        text = self.html()
        m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', text)
        self.assertTrue(m)
        csp = m.group(1)
        self.assertIn("default-src 'none'", csp)
        self.assertNotIn("script-src", csp.replace("script-src 'none'", ""))
        self.assertNotIn("unsafe-inline", csp)
        self.assertRegex(csp, r"style-src 'sha256-[A-Za-z0-9+/=]+'")
        import base64, hashlib
        css = re.search(r"<style>(.*?)</style>", text, re.S).group(1)
        digest = base64.b64encode(hashlib.sha256(css.encode("utf-8")).digest()).decode()
        self.assertIn(digest, csp)

    def test_same_findings_and_order_as_markdown(self):  # AC b
        for mode, run in self.runs.items():
            md = render_report(run, self.crosswalk)
            text = self.html(mode)
            md_ids = re.findall(r"\| (PI-\d+) \|", md)
            reg = text.split('id="register"')[1].split('id="findings"')[0]
            html_ids = re.findall(r'data-label="ID">(PI-\d+)<', reg)
            self.assertEqual(len(html_ids), 16)
            self.assertEqual(html_ids, md_ids)
            for r in run["results"]:
                self.assertIn(str(r["exposure_adjusted_residual_risk_score"]), text)
            self.assertEqual(text.count("<details"), 16)
            self.assertIn(str(run["average_exposure_adjusted_residual_risk"]), text)
            self.assertIn(str(run["manifest"]["cases_sha256"]), text)

    def test_unverified_badge(self):  # AC c
        text = self.html("safe")
        n = sum(1 for e in self.crosswalk["entries"] if not e["verified"])
        self.assertEqual(n, 2)
        xw = text.split('id="crosswalk"')[1].split('id="manifest"')[0]
        self.assertEqual(xw.count('class="badge unverified"'), n)
        self.assertGreaterEqual(text.count('class="badge unverified"'), n)
        cw = copy.deepcopy(self.crosswalk)
        for e in cw["entries"]:
            e["verified"] = True
        self.assertEqual(render_html(self.runs["safe"], cw).count('class="badge unverified"'), 0)

    def test_mock_label_before_score_and_wording(self):
        text = self.html("safe")
        self.assertLess(text.index("Mock run"), text.index('class="tile tile-score"'))
        real = copy.deepcopy(self.runs["safe"])
        real["manifest"]["target"] = "openai_compat"
        real["manifest"]["model"] = "tiny-model"
        rt = render_html(real, self.crosswalk)
        self.assertLess(rt.index("Real-model run"), rt.index('class="tile tile-score"'))
        self.assertNotIn("Mock run", rt)
        both = (text + rt).lower()
        for banned in ("audit-ready", "certified", "proves safe", "compliant"):
            self.assertNotIn(banned, both.replace("not a compliance verdict", ""))
        self.assertIn("illustrative prioritisation score", both)
        self.assertIn("indicative", both)

    def test_severity_not_colour_only(self):
        text = self.html()
        for word in ("Critical", "High", "Medium"):
            self.assertIn(f"{word}</span>", text)
        self.assertIn("FAIL", text)
        self.assertIn("&#9670;", text)

    def test_accessibility_structure(self):
        text = self.html()
        p = parse(text)
        for tag in ("header", "main", "footer", "nav", "h1", "h2", "table", "th", "details", "summary"):
            self.assertIn(tag, p.tags)
        self.assertEqual(p.tags.count("h1"), 1)
        self.assertIn('<html lang="en">', text)
        self.assertIn("prefers-color-scheme: dark", text)
        self.assertIn("focus-visible", text)
        self.assertIn("@media print", text)
        self.assertIn("width=device-width", text)
        self.assertIn("max-width: 640px", text)
        self.assertIn("overflow-wrap", text)

    def test_scorer_panel_and_limits(self):
        text = self.html()
        self.assertIn("Scorer accuracy", text)
        self.assertIn("Synthetic", text)
        self.assertIn("Precision", text)
        self.assertIn('id="limits"', text)
        self.assertIn("not measured probabilities", text)

    def test_deterministic_and_timestamp_on_one_line(self):
        a = self.html(now="2026-01-01T00:00:00+00:00")
        b = self.html(now="2030-05-05T00:00:00+00:00")
        self.assertNotEqual(a, b)
        self.assertEqual(strip_stamp(a), strip_stamp(b))
        self.assertEqual(a.count("Report timestamp (varies):"), 1)

    def test_hostile_text_is_escaped(self):
        run = copy.deepcopy(self.runs["unsafe"])
        evil = ('<script>alert(1)</script> <img src=x onerror=alert(2)> '
                '<a href="javascript:alert(3)">x</a> "quoted" \'single\' http://evil.example/p.png')
        r0 = run["results"][0]
        r0["response"] = evil
        r0["prompt"] = evil
        r0["rationale"] = evil
        r0["family"] = evil
        run["manifest"]["model"] = evil
        run["manifest"]["tool_version"] = evil
        run["overall_risk_posture"] = evil
        cw = copy.deepcopy(self.crosswalk)
        cw["entries"][0]["owasp_llm_2025"] = [evil]
        cw["entries"][0]["uk"] = [{"source": evil, "ref": evil}]
        text = render_html(run, cw)
        p = parse(text)
        self.assertEqual(p.tags.count("script"), 0)
        self.assertNotIn("img", p.tags)
        for tag, k, v in p.attrs:
            self.assertFalse(k.startswith("on"), (tag, k))
            self.assertNotIn(k, ("src", "style"))
            if k == "href":
                self.assertTrue(v.startswith("#"), v)
        self.assertNotIn("<script", text)
        self.assertNotIn("<img", text)
        self.assertNotIn("javascript:", text)
        self.assertNotIn("http://", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("&quot;quoted&quot;", text)

    def test_posture_caption_and_scroll_rule(self):
        self.assertIn("Overall risk posture (illustrative label)", self.html())
        self.assertIn("Overall risk posture (illustrative label)", render_report(self.runs["safe"], self.crosswalk))
        self.assertIn(".scroll{overflow-x:auto}", self.html())

    def test_long_values_are_capped(self):
        run = copy.deepcopy(self.runs["unsafe"])
        run["results"][0]["blast_radius"] = ["x" * 100000]
        run["manifest"]["model"] = "m" * 100000
        for text in (render_html(run, self.crosswalk), render_report(run, self.crosswalk)):
            self.assertLess(len(text), 200000)
            self.assertNotIn("x" * 600, text)
            self.assertNotIn("m" * 600, text)
            self.assertIn("...", text)

    def test_cli_html_to_file_twice_identical(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps(run_tests("unsafe", trials=5)), encoding="utf-8")
            outs = []
            for name, flag in (("a.html", "--out"), ("b.html", "--output")):
                out = Path(tmp) / name
                p = subprocess.run([sys.executable, "-m", "tester.report", str(path), "--format", "html", flag, str(out)],
                                   cwd=str(ROOT), capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)
                outs.append(strip_stamp(out.read_text(encoding="utf-8")))
            self.assertEqual(outs[0], outs[1])
            self.assertRegex(outs[0], r"\d/5")
            self.assertIn("Wilson 95%", outs[0])
            self.assertTrue(outs[0].startswith("<!doctype html>"))

    def test_bad_shape_exits_cleanly(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text("[]", encoding="utf-8")
            p = subprocess.run([sys.executable, "-m", "tester.report", str(path), "--format", "html"],
                               cwd=str(ROOT), capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
