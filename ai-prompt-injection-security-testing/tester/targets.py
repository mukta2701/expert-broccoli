"""Prompt targets share one text-and-metadata response contract."""

import ipaddress
import json
import math
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from mock_app.mock_chatbot import chat


@dataclass(frozen=True)
class TargetResponse:
    text: str
    metadata: dict


class Target(Protocol):
    name: str

    def send(self, prompt: str, *, canary: str | None = None) -> TargetResponse: ...


class MockTarget:
    name = "mock"

    def __init__(self, mode: str = "safe"):
        self.mode = mode

    def send(self, prompt: str, *, canary: str | None = None) -> TargetResponse:
        response = chat(prompt, mode=self.mode, canary=canary)
        return TargetResponse(response.text, {"category": response.category})


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OpenAICompatTarget:
    name = "openai_compat"

    def __init__(self, base_url: str, model: str, *, i_have_authorization: bool = False,
                 timeout: float = 30, requests_per_second: float = 1):
        if not model.strip():
            raise ValueError("model is required")
        for value in (timeout, requests_per_second):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("timeout and requests per second must be finite and positive")
        url = urlsplit(base_url)
        if (url.scheme not in {"http", "https"} or not url.hostname or url.username is not None
                or url.password is not None or url.query or url.fragment):
            raise ValueError("base URL must be HTTP(S), without credentials, query or fragment")
        host = url.hostname
        if host.lower() == "localhost":
            host = "127.0.0.1"  # Pin localhost to loopback without trusting DNS.
        try:
            local = ipaddress.ip_address(host).is_loopback
        except ValueError:
            local = False
        if not local and not i_have_authorization:
            raise ValueError("non-local targets require --i-have-authorization")
        authority = f"[{host}]" if ":" in host else host
        if url.port is not None:
            authority += f":{url.port}"
        self.url = urlunsplit((url.scheme, authority,
                               url.path.rstrip("/") + "/chat/completions", "", ""))
        self.model = model
        self.timeout = timeout
        self.interval = 1 / requests_per_second
        self.next_request = 0.0
        self.opener = build_opener(ProxyHandler({}), _NoRedirect())

    def send(self, prompt: str, *, canary: str | None = None) -> TargetResponse:
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        request = Request(self.url, json.dumps(body).encode(), headers={
            "Content-Type": "application/json", "X-Assurance-Ledger-Test": "1"})
        time.sleep(max(0, self.next_request - time.monotonic()))
        self.next_request = time.monotonic() + self.interval
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as error:
            error.close()
            raise
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("target response must contain assistant text") from error
        if not isinstance(text, str):
            raise ValueError("target response must contain assistant text")
        return TargetResponse(text,
                              {key: payload[key] for key in ("id", "model", "usage") if key in payload})
