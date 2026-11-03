"""Case-study section of the HTML report (issue 19)."""

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory

from tester.case_study import REAL_LABEL, SYNTHETIC_LABEL, build_case_study
from tester.report_html import render_html, scorer_panel_data
from tester.scoring_criteria import load_cases, score_response, score_response_baseline
from tester.test_runner import run_tests

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence" / "real_run_llama3_2_3b.json"
STAMP = re.compile(r".*Report timestamp \(varies\):.*\n")


class CaseStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = run_tests("unsafe")
        cls.crosswalk = json.loads((ROOT / "data" / "framework_crosswalk.json").read_text(encoding="utf-8"))
        cls.scorer = scorer_panel_data()
        cls.study = build_case_study()
        cls.stored = {r["test_id"]: r for r in json.loads(EVIDENCE.read_text(encoding="utf-8"))["results"]}

    def html(self, study=None, **kw):
        return render_html(self.res, self.crosswalk, scorer=self.scorer, case_study=study or self.study, **kw)

    def by_label(self, label):
        return [e for e in self.study["examples"] if e["label"] == label]

    def test_default_report_has_no_case_study(self):
        text = render_html(self.res, self.crosswalk, scorer=self.scorer)
        self.assertNotIn("casestudy", text)
        self.assertIn('</section>\n<section aria-labelledby="limits">', text)
        self.assertNotIn("\n\n", text)
        self.assertIn('</section>\n<section aria-labelledby="limits">', self.html())

    def test_exact_stored_reply_and_both_verdicts(self):  # AC 1
        real = self.by_label(REAL_LABEL)[0]
        row = self.stored[real["case_id"]]
        self.assertEqual(real["reply"], row["response"])
        self.assertEqual(real["old"], (row["baseline_outcome"], row["baseline_rationale"]))
        self.assertEqual(real["new"], (row["outcome"], row["rationale"]))
        text = self.html()
        self.assertIn(row["response"].split(".")[0].replace("'", "&#x27;"), text)
        self.assertIn("No clear refusal to prompt-injection attempt.", text)
        self.assertIn("expected response phrases missing", text)

    def test_synthetic_verdicts_are_computed_by_the_real_scorers(self):  # AC 1, 2
        cases = {c.test_id: c for c in load_cases()}
        leak, blind = self.by_label(SYNTHETIC_LABEL)
        for ex in (leak, blind):
            case = cases[ex["case_id"]]
            self.assertEqual(ex["old"][0], score_response_baseline(case, ex["reply"]).outcome)
            self.assertEqual(ex["new"][0], score_response(case, ex["reply"]).outcome)
        self.assertIn(cases[leak["case_id"]].canary, leak["reply"])
        self.assertEqual((leak["old"][0], leak["new"][0]), ("PASS", "FAIL"))

    def test_a_scorer_was_wrong(self):  # AC 2
        real = self.by_label(REAL_LABEL)[0]
        self.assertEqual(real["old"][0], "FAIL")
        self.assertIn("can't assist", real["reply"])  # a refusal, so FAIL is wrong
        blind = self.by_label(SYNTHETIC_LABEL)[1]
        self.assertNotIn("HARMLESS_CANARY", blind["reply"])
        self.assertEqual(blind["new"][0], "PASS")  # the canary scorer misses the spaced canary
        self.assertIn("Both scorers are wrong", blind["meaning"])

    def test_labels_and_no_leak_statement(self):  # AC 3
        text = self.html()
        self.assertEqual(text.count(f">{SYNTHETIC_LABEL}<"), 2)
        self.assertEqual(text.count(f">{REAL_LABEL}<"), 1)
        self.assertIn("never in the model&#x27;s context", text)
        body = text.split('id="casestudy"')[1].split('id="limits"')[0].lower()
        for word in ("proves", "audit-ready", "compliant", " safe ", "secure"):
            self.assertNotIn(word, body)

    def test_hostile_reply_is_escaped(self):  # AC 4
        hostile = ('<script>alert(1)</script><img src=x onerror=alert(1)> '
                   '<a href="javascript:alert(1)">x</a> https://evil.example/x')
        study = json.loads(json.dumps(self.study))
        study["examples"][0]["reply"] = hostile
        study["examples"][0]["old"] = ("PASS", "<script>r</script>")
        text = self.html(study)
        for bad in ("<script", "<img", "https://evil"):
            self.assertNotIn(bad, text)
        seen = []

        class P(HTMLParser):
            def handle_starttag(self, tag, attrs):
                seen.extend([tag] + [k for k, _ in attrs])
        P().feed(text)
        self.assertNotIn("onerror", seen)
        self.assertNotIn("script", seen)
        self.assertNotIn("img", seen)
        self.assertNotIn("javascript:alert", text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)

    def test_long_reply_is_capped(self):
        study = json.loads(json.dumps(self.study))
        study["examples"][0]["reply"] = "A" * 5000
        self.assertNotIn("A" * 400, self.html(study))

    def test_deterministic_and_csp_hash_still_valid(self):
        a, b = self.html(now="x"), self.html(now="y")
        strip = lambda t: STAMP.sub("", t)  # noqa: E731
        self.assertEqual(strip(a), strip(b))
        import base64
        import hashlib
        css = re.search(r"<style>(.*?)</style>", a, re.S).group(1)
        digest = base64.b64encode(hashlib.sha256(css.encode("utf-8")).digest()).decode()
        self.assertIn(f"sha256-{digest}", a)
        self.assertNotIn("<script", a)
        self.assertNotIn("https://", a)

    def test_cli_flag(self):
        import subprocess
        import sys
        with TemporaryDirectory() as d:
            res = Path(d) / "r.json"
            res.write_text(json.dumps(self.res), encoding="utf-8")
            out = Path(d) / "o.html"
            cmd = [sys.executable, "-m", "tester.report", str(res), "--format", "html",
                   "--case-study", "--evidence", str(EVIDENCE), "--out", str(out)]
            subprocess.run(cmd, cwd=ROOT, check=True)
            self.assertIn("a refusal that still leaks", out.read_text(encoding="utf-8"))

    def test_flag_misuse_exits_with_message(self):
        import subprocess
        import sys
        with TemporaryDirectory() as d:
            res = Path(d) / "r.json"
            res.write_text(json.dumps(self.res), encoding="utf-8")
            for extra, msg in ((["--format", "html", "--evidence", str(EVIDENCE)], "--evidence needs --case-study"),
                               (["--case-study"], "--case-study is HTML only")):
                p = subprocess.run([sys.executable, "-m", "tester.report", str(res)] + extra,
                                   cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(p.returncode, 2)
                self.assertIn(msg, p.stderr)


if __name__ == "__main__":
    unittest.main()
