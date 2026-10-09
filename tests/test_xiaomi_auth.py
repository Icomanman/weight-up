import importlib
import sys
from pathlib import Path


def load_auth_module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parent))
    monkeypatch.setattr(sys, "argv", ["pytest", "--unrelated-option"])
    return importlib.import_module("xiaomi_auth")


def test_auth_module_import_does_not_parse_command_line_arguments(monkeypatch):
    auth_module = load_auth_module(monkeypatch)

    assert auth_module.XiaomiEmailTwoFactorAuthenticator


class FakeResponse:
    def __init__(self, status_code, headers=None, text="", payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON response")
        return self._payload


class FakeCookies:
    def __init__(self):
        self.values = {("ick", None): "identity-cookie"}

    def get(self, name, domain=None):
        return self.values.get((name, domain))

    def set(self, name, value, domain=None):
        self.values[(name, domain)] = value


class FakeSession:
    def __init__(self):
        self.cookies = FakeCookies()
        self.get_responses = iter(
            [
                FakeResponse(200),
                FakeResponse(200),
                FakeResponse(
                    302,
                    headers={"Location": "https://account.xiaomi.com/serviceLoginAuth2/end"},
                ),
                FakeResponse(
                    302,
                    headers={
                        "extension-pragma": '{"ssecurity":"security-value"}',
                        "Location": "https://sts.api.io.mi.com/sts",
                    },
                ),
                FakeResponse(200),
            ]
        )
        self.post_responses = iter(
            [
                FakeResponse(200, payload={}),
                FakeResponse(
                    200,
                    payload={
                        "location": "https://account.xiaomi.com/identity/result/check?ok=1"
                    },
                ),
            ]
        )
        self.posted_data = []

    def get(self, url, **kwargs):
        if url == "https://sts.api.io.mi.com/sts":
            self.cookies.set("serviceToken", "service-token", ".sts.api.io.mi.com")
        return next(self.get_responses)

    def post(self, url, **kwargs):
        self.posted_data.append(kwargs["data"])
        return next(self.post_responses)


def test_email_code_completes_2fa_and_returns_session_tokens(monkeypatch):
    auth_module = load_auth_module(monkeypatch)
    session = FakeSession()

    result = auth_module.XiaomiEmailTwoFactorAuthenticator(
        session=session,
        user_agent="test-agent",
        code_provider=lambda: "manual-code",
    ).authenticate(
        "https://account.xiaomi.com/verify?context=test-context",
        user_id="user-1",
        c_user_id="c-user-1",
    )

    assert result.ssecurity == "security-value"
    assert result.service_token == "service-token"
    assert result.user_id == "user-1"
    assert result.c_user_id == "c-user-1"
    assert session.posted_data[1]["ticket"] == "manual-code"
    for domain in (".api.io.mi.com", ".io.mi.com", ".mi.com"):
        assert session.cookies.get("serviceToken", domain=domain) == "service-token"
        assert session.cookies.get("yetAnotherServiceToken", domain=domain) == "service-token"