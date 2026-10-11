"""Test doubles for the Xiaomi cloud modules; no network is ever touched."""

import base64
import json
from typing import Any, Callable

from requests.cookies import RequestsCookieJar

from weight_up.xiaomi import signing


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        text: str = "",
        payload: Any = None,
        content: bytes = b"",
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text
        self.content = content
        self.cookies = RequestsCookieJar()
        self._payload = payload

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("no JSON body")
        return self._payload


Handler = FakeResponse | Callable[["FakeSession", dict[str, Any]], FakeResponse]


class FakeSession:
    """Answers requests from (method, url fragment) routes; first match wins."""

    def __init__(self, routes: list[tuple[str, str, Handler]]) -> None:
        self.cookies = RequestsCookieJar()
        self.routes = routes
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._dispatch("GET", url, kwargs)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._dispatch("POST", url, kwargs)

    def calls_to(self, fragment: str) -> list[tuple[str, str, dict[str, Any]]]:
        return [call for call in self.calls if fragment in call[1]]

    def _dispatch(self, method: str, url: str, kwargs: dict[str, Any]) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        for route_method, fragment, handler in self.routes:
            if route_method == method and fragment in url:
                return handler(self, kwargs) if callable(handler) else handler
        raise AssertionError(f"unexpected {method} {url}")


def guarded(payload: dict[str, Any]) -> str:
    """Wrap JSON the way Xiaomi's account service does."""
    return "&&&START&&&" + json.dumps(payload)


class EncryptedApi:
    """A fake regional API that decrypts requests and encrypts replies.

    pages are returned, in order, for scale-data calls. Every request is
    recorded as (url, decrypted body, request kwargs).
    """

    def __init__(
        self,
        ssecurity: str,
        pages: list[list[dict[str, Any]]] | None = None,
        code: int = 0,
        reply_key: str | None = None,
    ) -> None:
        self.ssecurity = ssecurity
        self.pages = list(pages or [])
        self.code = code
        self.reply_key = reply_key or ssecurity
        self.requests: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        form = kwargs["data"]
        signed_nonce = signing.derive_signed_nonce(self.ssecurity, form["_nonce"])
        body = json.loads(
            signing.rc4_crypt(signed_nonce, base64.b64decode(form["data"])))
        self.requests.append((url, body, kwargs))

        result = self.pages.pop(0) if "scale" in url and self.pages else {}
        reply = {"code": self.code, "message": "fake", "result": result}
        reply_nonce_key = signing.derive_signed_nonce(
            self.reply_key, form["_nonce"])
        encrypted = signing.rc4_crypt(reply_nonce_key, json.dumps(reply).encode())
        return FakeResponse(text=base64.b64encode(encrypted).decode())
