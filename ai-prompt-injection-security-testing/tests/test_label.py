"""label: loopback-only local labelling page, token-guarded, atomic saves."""

import http.client
import json
import re
import tempfile
import threading
import unittest
from unittest import mock
from pathlib import Path

from tester import label

HOSTILE = "<script>alert(1)</script> & <img src=x onerror=alert(2)>"


def make_run(root, n=3):
    run = Path(root) / "2026-11-03_mock"
    run.mkdir()
    results = [{"test_id": f"PI-0{i}", "family": "fam", "prompt": f"attack {i}",
                "response": HOSTILE if i == 1 else f"reply {i}"} for i in range(1, n + 1)]
    summary = {"results": results, "manifest": {"cases_sha256": "abc123", "model": "toy"}}
    (run / "results.json").write_text(json.dumps(summary), encoding="utf-8")
    return run


class Session:
    def __init__(self, run):
        self.server = label.make_server(run, port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = {"Host": f"127.0.0.1:{self.port}"}
        hdrs.update(headers or {})
        conn.request(method, path, body=body, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp, data

    def sid(self):
        _, data = self.request("GET", "/")
        return re.search(rb'data-sid="([^"]+)"', data).group(1).decode()

    def post(self, payload, sid="ok", **extra):
        if sid == "ok":
            sid = self.sid()
        body = payload if isinstance(payload, bytes) else json.dumps({"sid": sid, **payload}).encode()
        hdrs = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.port}"}
        hdrs.update(extra)
        return self.request("POST", "/save", body, hdrs)

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class LabelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run_dir = make_run(self.tmp.name)
        self.s = Session(self.run_dir)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.s.close)

    def test_binds_loopback_only_and_refuses_other_hosts(self):
        self.assertEqual(self.s.server.server_address[0], "127.0.0.1")
        with self.assertRaises(TypeError):
            label.make_server(self.run_dir, port=0, **{"bind": "0.0.0.0"})
        with self.assertRaises(ValueError):
            label.make_server(self.run_dir, port=0, host="0.0.0.0")

    def test_bad_host_header_403(self):
        resp, _ = self.s.request("GET", "/", headers={"Host": "evil.example:80"})
        self.assertEqual(resp.status, 403)
        resp, _ = self.s.request("GET", "/", headers={"Host": f"localhost:{self.s.port}"})
        self.assertEqual(resp.status, 200)

    def test_hostile_reply_escaped_and_csp(self):
        resp, data = self.s.request("GET", "/")
        html = data.decode()
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("1 of 3", html)
        csp = resp.getheader("Content-Security-Policy")
        self.assertIn("default-src 'none'", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertEqual(len(re.findall(r"<script", html)), 1)
        self.assertNotIn("http://", html.replace(f"127.0.0.1:{self.s.port}", ""))
        self.assertNotRegex(html, r'(src|href)="https?:')

    def test_reply_is_length_capped(self):
        text = label.cap("x" * 100000)
        self.assertLess(len(text), 10000)

    def test_missing_or_wrong_token_403(self):
        self.assertEqual(self.s.post({"case_id": "PI-01", "choice": "1"}, sid="")[0].status, 403)
        self.assertEqual(self.s.post({"case_id": "PI-01", "choice": "1"}, sid="nope")[0].status, 403)
        self.assertFalse((self.run_dir / "labels.json").exists())

    def test_wrong_origin_403(self):
        resp, _ = self.s.post({"case_id": "PI-01", "choice": "1"}, Origin="http://evil.example")
        self.assertEqual(resp.status, 403)

    def test_oversized_body_413(self):
        resp, _ = self.s.post(b"x" * 100000)
        self.assertEqual(resp.status, 413)

    def test_wrong_content_type_415(self):
        resp, _ = self.s.post({"case_id": "PI-01", "choice": "1"}, **{"Content-Type": "text/plain"})
        self.assertEqual(resp.status, 415)

    def test_invalid_label_400(self):
        for bad in ({"case_id": "PI-01", "choice": "9"}, {"case_id": "../x", "choice": "1"},
                    {"case_id": "PI-01"}, {"case_id": "PI-01", "choice": 1}):
            self.assertEqual(self.s.post(bad)[0].status, 400, bad)
        self.assertEqual(self.s.post(b"not json")[0].status, 400)
        self.assertFalse((self.run_dir / "labels.json").exists())

    def test_saved_after_each_answer_atomically_and_resumes(self):
        resp, _ = self.s.post({"case_id": "PI-01", "choice": "1"})
        self.assertEqual(resp.status, 200)
        saved = json.loads((self.run_dir / "labels.json").read_text(encoding="utf-8"))
        rec = saved["labels"]["PI-01"]
        self.assertEqual((rec["label"], rec["choice"]), ("PASS", "refused"))
        self.assertEqual((rec["run"], rec["cases_sha256"], rec["model"]),
                         ("2026-11-03_mock", "abc123", "toy"))
        self.assertIn("labelled by a human (the owner), single labeller", rec["note"])
        self.assertTrue(rec["labelled_at"])
        self.assertEqual(sorted(p.name for p in self.run_dir.iterdir() if p.name.startswith("labels")),
                         ["labels.json"])  # no temp files left behind
        self.s.post({"case_id": "PI-02", "choice": "2"})
        self.assertEqual(json.loads((self.run_dir / "labels.json").read_text())["labels"]["PI-02"]["label"], "FAIL")
        self.s.close()
        self.s = Session(self.run_dir)  # restart
        _, data = self.s.request("GET", "/")
        self.assertIn("3 of 3", data.decode())
        self.s.post({"case_id": "PI-01", "choice": "3"})  # change an earlier answer
        self.assertEqual(json.loads((self.run_dir / "labels.json").read_text())["labels"]["PI-01"]["label"], "PARTIAL")

    def test_bad_labels_file_refused_and_left_alone(self):
        path = self.run_dir / "labels.json"
        for bad in ("not json", "[1]", '{"labels": [1]}', '{"labels": {"PI-01": 5}}', '{"labels": {"PI-01": {}}}'):
            path.write_text(bad, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "labels.json.*move it aside"):
                label.make_server(self.run_dir, port=0)
            self.assertEqual(path.read_text(encoding="utf-8"), bad)

    def test_stalled_client_is_closed(self):
        import socket
        self.assertEqual(label.Handler.timeout, 10)
        with mock.patch.object(label.Handler, "timeout", 0.3):
            sock = socket.create_connection(("127.0.0.1", self.s.port), timeout=5)
            sock.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1")  # never finishes the request
            self.assertEqual(sock.recv(10), b"")  # server closed it
            sock.close()

    def test_accepts_results_json_path(self):
        self.assertEqual(label.resolve_run(self.run_dir / "results.json"), self.run_dir.resolve())
        self.assertEqual(label.resolve_run(self.run_dir), self.run_dir.resolve())


if __name__ == "__main__":
    unittest.main()
