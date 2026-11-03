"""Local page to hand-label stored replies. Loopback only; one item at a time."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import secrets
import sys
import tempfile
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

LOOPBACK = "127.0.0.1"
MAX_BODY = 4096
MAX_SHOWN = 4000
NOTE = "labelled by a human (the owner), single labeller"
# The owner's three buttons mapped onto the scorer's PASS / PARTIAL / FAIL vocabulary.
CHOICES = {"1": ("refused", "PASS"), "2": ("went along", "FAIL"), "3": ("unclear", "PARTIAL")}

SCRIPT = """document.addEventListener('keydown',function(e){var k=e.key;
if(k==='ArrowLeft'){var b=document.getElementById('back');if(b)location.href=b.href;return;}
var btn=document.querySelector('button[data-choice="'+k+'"]');if(btn)btn.click();});
document.querySelectorAll('button[data-choice]').forEach(function(b){b.addEventListener('click',function(){
var d=document.body.dataset,x=new XMLHttpRequest();x.open('POST','/save');
x.setRequestHeader('Content-Type','application/json');x.onload=function(){
if(x.status===200){location.href='/?i='+d.next;}else{document.getElementById('err').textContent='Save failed ('+x.status+')';}};
x.send(JSON.stringify({sid:d.sid,case_id:d.case,choice:b.dataset.choice}));});});"""
LIGHT = {"bg": "#ffffff", "fg": "#111827", "box": "#f3f4f6", "muted": "#4b5563",
         "line": "#374151", "focus": "#1d4ed8", "err": "#b91c1c"}
DARK = {"bg": "#14161a", "fg": "#f3f4f6", "box": "#1e2128", "muted": "#b6bcc8",
        "line": "#9ca3af", "focus": "#93c5fd", "err": "#fca5a5"}


def _vars(tokens):
    return "".join(f"--{k}:{v};" for k, v in tokens.items())


CSS = (":root{" + _vars(LIGHT) + "}@media(prefers-color-scheme:dark){:root{" + _vars(DARK) + "}}" + """
body{font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:46rem;padding:1rem 16px;background:var(--bg);color:var(--fg)}
h1,h2,p,b{color:var(--fg)}h2{font-size:1.1rem}.caption{color:var(--muted);font-size:.85rem}
pre{white-space:pre-wrap;word-break:break-word;background:var(--box);color:var(--fg);border:1px solid var(--line);padding:.75rem;border-radius:6px}
button,.btn{font:inherit;padding:.6rem 1rem;margin:.25rem .25rem .25rem 0;border:2px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer;text-decoration:none;display:inline-block}
.btn[aria-disabled]{color:var(--muted);border-style:dashed;cursor:not-allowed}
button:focus-visible,a:focus-visible{outline:3px solid var(--focus);outline-offset:2px}#err{color:var(--err);font-weight:600}""")


def _hash(text):
    return "sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode()


CSP = (f"default-src 'none'; style-src '{_hash(CSS)}'; script-src '{_hash(SCRIPT)}'; "
       "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def cap(text) -> str:
    text = str(text)
    return text if len(text) <= MAX_SHOWN else text[:MAX_SHOWN] + "\n[truncated]"


def resolve_run(path) -> Path:
    path = Path(path).resolve()
    run = path.parent if path.is_file() else path
    if not (run / "results.json").is_file():
        raise ValueError(f"no results.json in {run}")
    return run


class Store:
    def __init__(self, run: Path):
        self.run, self.path, self.lock = run, run / "labels.json", threading.Lock()
        summary = json.loads((run / "results.json").read_text(encoding="utf-8"))
        self.items = [r for r in summary["results"] if isinstance(r.get("test_id"), str)]
        self.manifest = summary.get("manifest") or {}
        self.labels = {}
        if self.path.exists():
            self.labels = self._load()

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            labels = data["labels"]
            ok = isinstance(labels, dict) and all(isinstance(k, str) and isinstance(v, dict) and
                                                   v.get("choice") in ("refused", "went along", "unclear")
                                                   for k, v in labels.items())
        except (OSError, ValueError, KeyError, TypeError):
            ok = False
        if not ok:
            raise ValueError(f"{self.path} is not a valid labels file; move it aside and start again")
        return labels

    def first_unlabelled(self) -> int:
        return next((i for i, r in enumerate(self.items) if r["test_id"] not in self.labels), len(self.items))

    def save(self, case_id: str, choice: str) -> None:
        name, outcome = CHOICES[choice]
        rec = {"case_id": case_id, "label": outcome, "choice": name, "run": self.run.name,
               "labelled_at": datetime.now(timezone.utc).isoformat(), "note": NOTE}
        for key in ("cases_sha256", "model"):
            if self.manifest.get(key):
                rec[key] = self.manifest[key]
        with self.lock:
            labels = dict(self.labels, **{case_id: rec})
            fd, tmp = tempfile.mkstemp(prefix=".labels-", suffix=".tmp", dir=self.run)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump({"labels": labels}, fh, indent=2)
                    fh.write("\n")
                os.replace(tmp, self.path)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
            self.labels = labels


def render(store: Store, index: int, sid: str) -> str:
    e, total = html.escape, len(store.items)
    index = max(0, min(index, total))
    if index >= total:
        body = f'<h1>All done</h1><p>{len(store.labels)} of {total} labelled.</p>'
        case_id = ""
    else:
        item = store.items[index]
        case_id = item["test_id"]
        done = store.labels.get(case_id, {}).get("choice")
        body = (f'<p>{index + 1} of {total} &middot; <b>{e(case_id)}</b> &middot; {e(str(item.get("family", "")))}'
                f'{" &middot; labelled: " + e(done) if done else ""}</p>'
                f'<h2>Attack text sent</h2><pre>{e(cap(item.get("prompt", "")))}</pre>'
                f'<h2>Reply (trial 1)</h2><pre>{e(cap(item.get("response", "")))}</pre>'
                '<button data-choice="1">1 Refused</button><button data-choice="2">2 Went along</button>'
                '<button data-choice="3">3 Unclear</button>'
                f'<a class="btn" href="/?i={index + 1}">Skip</a>')
    back = f'<a class="btn" id="back" href="/?i={index - 1}">Back</a>' if index > 0 else \
        '<span class="btn" aria-disabled="true">Back (first item)</span>'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Label replies</title>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head>'
            f'<body data-sid="{e(sid)}" data-case="{e(case_id)}" data-next="{index + 1}">'
            f'{body}<p>{back}</p><p class="caption">Keys: 1 refused &middot; 2 went along &middot; 3 unclear &middot; &larr; back</p><p id="err" role="alert"></p><script>{SCRIPT}</script></body></html>')


class Handler(BaseHTTPRequestHandler):
    timeout = 10  # seconds; a stalled client cannot hold a thread forever

    def log_message(self, *args):
        pass

    def _send(self, status, body=b"", ctype="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _allowed(self):
        port = self.server.server_address[1]
        return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def do_GET(self):
        if not self._allowed():
            return self._send(403, b"bad host")
        parts = urlsplit(self.path)
        if parts.path != "/":
            return self._send(404, b"not found")
        store = self.server.store
        try:
            index = int(parse_qs(parts.query)["i"][0])
        except (KeyError, ValueError, IndexError):
            index = store.first_unlabelled()
        page = render(store, index, self.server.sid).encode("utf-8")
        self._send(200, page, "text/html; charset=utf-8")

    def do_POST(self):
        if not self._allowed() or self.path != "/save":
            return self._send(403 if not self._allowed() else 404, b"forbidden")
        port = self.server.server_address[1]
        if self.headers.get("Origin") not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
            return self._send(403, b"bad origin")
        if (self.headers.get("Content-Type") or "").split(";")[0].strip() != "application/json":
            return self._send(415, b"json only")
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._send(411, b"length required")
        if length < 0 or length > MAX_BODY:
            return self._send(413, b"too large")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw)
        except ValueError:
            return self._send(400, b"bad json")
        if not isinstance(data, dict) or not isinstance(data.get("sid"), str) \
                or not secrets.compare_digest(data["sid"].encode(), self.server.sid.encode()):
            return self._send(403, b"bad session value")
        store, case_id, choice = self.server.store, data.get("case_id"), data.get("choice")
        if not isinstance(case_id, str) or case_id not in {r["test_id"] for r in store.items} \
                or not isinstance(choice, str) or choice not in CHOICES:
            return self._send(400, b"invalid label")
        store.save(case_id, choice)
        self._send(200, b'{"ok":true}', "application/json")


def make_server(run, port: int = 0, host: str = LOOPBACK) -> ThreadingHTTPServer:
    if host != LOOPBACK:
        raise ValueError("this server binds to 127.0.0.1 only")
    server = ThreadingHTTPServer((LOOPBACK, port), Handler)
    server.store, server.sid = Store(resolve_run(run)), secrets.token_urlsafe(32)
    return server


def main(argv=None, out=None, open_url=webbrowser.open) -> int:
    out = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(description="Hand-label a run's replies in a local page.")
    parser.add_argument("run", type=Path, help="Run folder or its results.json")
    parser.add_argument("--port", type=int, default=0, help="Port (default: random free port)")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser")
    args = parser.parse_args(argv)
    try:
        server = make_server(args.run, args.port)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    out.write(f"Labelling {server.store.run.name}: {url}  (Ctrl-C to stop)\n")
    out.flush()
    if not args.no_open:
        open_url(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
