import hashlib

import pytest

from weight_up.xiaomi import XiaomiAuthError, auth as auth_module
from .xiaomi_fakes import FakeResponse, FakeSession, guarded

EMAIL = "user@example.com"
PASSWORD = "pw"
NOTIFICATION_URL = "https://account.xiaomi.com/identity/authStart?context=ctx-1"
LOCATION = "https://sts.api.io.mi.com/sts?x=1"


def sign_route():
    return ("GET", "pass/serviceLogin?sid", FakeResponse(
        200, text=guarded({"_sign": "sign-1"})))


def auth2_route(*replies):
    queue = iter(replies)
    return ("POST", "serviceLoginAuth2", lambda s, k: next(queue))


def reply(payload):
    return FakeResponse(200, text=guarded(payload))


def location_route(session_cookie=True):
    def handler(session, kwargs):
        response = FakeResponse(200)
        if session_cookie:
            response.cookies.set("serviceToken", "svc-token")
            session.cookies.set("passToken", "cookie-pass",
                                domain=".xiaomi.com")
        return response
    return ("GET", "sts.api.io.mi.com/sts", handler)


@pytest.fixture
def use_session(monkeypatch):
    def install(session):
        monkeypatch.setattr(
            auth_module, "start_login_session", lambda: session)
        return session
    return install


def test_password_is_sent_as_uppercase_md5_with_the_sign(use_session):
    session = use_session(FakeSession([
        sign_route(),
        auth2_route(reply({"ssecurity": "sec-value", "location": LOCATION,
                           "userId": 7, "cUserId": "c-7"})),
        location_route(),
    ]))

    result = auth_module.login(EMAIL, PASSWORD, code_provider=lambda: "unused")

    [(_, _, call)] = session.calls_to("serviceLoginAuth2")
    assert call["params"]["hash"] == hashlib.md5(b"pw").hexdigest().upper()
    assert call["params"]["_sign"] == "sign-1"
    assert call["params"]["user"] == EMAIL
    assert (result.ssecurity, result.service_token) == (
        "sec-value", "svc-token")
    assert (result.user_id, result.c_user_id) == ("7", "c-7")
    assert result.pass_token == "cookie-pass"


def test_two_factor_branch_uses_the_code_provider(use_session, monkeypatch):
    seen = {}

    class FakeAuthenticator:
        def __init__(self, session, user_agent, code_provider, logger):
            seen["code"] = code_provider()

        def authenticate(self, notification_url, user_id, c_user_id):
            seen["args"] = (notification_url, user_id, c_user_id)
            return "authenticated"

    monkeypatch.setattr(
        auth_module, "XiaomiEmailTwoFactorAuthenticator", FakeAuthenticator)
    use_session(FakeSession([
        sign_route(),
        auth2_route(reply({"notificationUrl": NOTIFICATION_URL, "userId": 7})),
    ]))

    result = auth_module.login(EMAIL, PASSWORD, code_provider=lambda: "654321")

    assert result == "authenticated"
    assert seen == {"code": "654321", "args": (NOTIFICATION_URL, "7", None)}


def test_captcha_is_fetched_with_the_session_and_resubmitted(use_session):
    images = []
    session = use_session(FakeSession([
        sign_route(),
        ("GET", "pass/getCode", FakeResponse(200, content=b"IMAGE")),
        auth2_route(
            reply({"captchaUrl": "/pass/getCode?icodeType=login"}),
            reply({"ssecurity": "sec-value", "location": LOCATION, "userId": 7}),
        ),
        location_route(),
    ]))

    def solver(image):
        images.append(image)
        return " AbC1 "

    result = auth_module.login(
        EMAIL, PASSWORD, code_provider=lambda: "", captcha_provider=solver)

    assert images == [b"IMAGE"]
    assert session.calls_to("getCode")[0][1].startswith(
        "https://account.xiaomi.com/")
    retry = session.calls_to("serviceLoginAuth2")[1][2]["params"]
    assert retry["captCode"] == "AbC1"
    assert result.service_token == "svc-token"


def test_captcha_without_a_solver_is_an_error(use_session):
    use_session(FakeSession([
        sign_route(),
        auth2_route(reply({"captchaUrl": "/pass/getCode"})),
    ]))

    with pytest.raises(XiaomiAuthError, match="captcha"):
        auth_module.login(EMAIL, PASSWORD, code_provider=lambda: "")


def test_rejected_captcha_is_an_error(use_session):
    use_session(FakeSession([
        sign_route(),
        ("GET", "pass/getCode", FakeResponse(200, content=b"IMAGE")),
        auth2_route(reply({"captchaUrl": "/pass/getCode"}),
                    reply({"code": 87001})),
    ]))

    with pytest.raises(XiaomiAuthError, match="Captcha rejected"):
        auth_module.login(
            EMAIL, PASSWORD, code_provider=lambda: "", captcha_provider=lambda i: "x")


def test_blank_captcha_text_is_an_error(use_session):
    use_session(FakeSession([
        sign_route(),
        ("GET", "pass/getCode", FakeResponse(200, content=b"IMAGE")),
        auth2_route(reply({"captchaUrl": "/pass/getCode"})),
    ]))

    with pytest.raises(XiaomiAuthError, match="No captcha text"):
        auth_module.login(
            EMAIL, PASSWORD, code_provider=lambda: "", captcha_provider=lambda i: " ")


def test_rejected_credentials_report_xiaomis_code(use_session):
    use_session(FakeSession([
        sign_route(),
        auth2_route(reply({"code": 70016, "desc": "wrong password"})),
    ]))

    with pytest.raises(XiaomiAuthError, match="code=70016"):
        auth_module.login(EMAIL, PASSWORD, code_provider=lambda: "")


def test_missing_sign_points_at_the_email(use_session):
    use_session(FakeSession([
        ("GET", "pass/serviceLogin?sid", FakeResponse(200, text=guarded({}))),
    ]))

    with pytest.raises(XiaomiAuthError, match="check the email"):
        auth_module.login(EMAIL, PASSWORD, code_provider=lambda: "")


def test_unreadable_reply_is_an_auth_error(use_session):
    use_session(FakeSession([
        ("GET", "pass/serviceLogin?sid", FakeResponse(200, text="<html>")),
    ]))

    with pytest.raises(XiaomiAuthError, match="unreadable"):
        auth_module.login(EMAIL, PASSWORD, code_provider=lambda: "")


@pytest.mark.parametrize("email, password", [("", PASSWORD), (EMAIL, "")])
def test_login_requires_email_and_password(email, password):
    with pytest.raises(ValueError):
        auth_module.login(email, password, code_provider=lambda: "")


def token_login_session(monkeypatch, routes):
    session = FakeSession(routes)
    monkeypatch.setattr(auth_module.requests, "Session", lambda: session)
    return session


def test_token_login_reissues_credentials_without_2fa(monkeypatch):
    session = token_login_session(monkeypatch, [
        ("GET", "pass/serviceLogin", reply({
            "result": "ok", "ssecurity": "sec-new", "location": LOCATION,
            "userId": 7, "passToken": "pass-new"})),
        location_route(),
    ])

    result = auth_module.login_with_token("7", "pass-old")

    [(_, _, call)] = session.calls_to("pass/serviceLogin")
    assert call["cookies"] == {"userId": "7", "passToken": "pass-old"}
    assert call["params"] == {"_json": "true", "sid": "xiaomiio"}
    assert (result.ssecurity, result.service_token) == ("sec-new", "svc-token")
    assert result.pass_token == "pass-new"


def test_token_login_keeps_the_given_token_when_xiaomi_returns_none(monkeypatch):
    token_login_session(monkeypatch, [
        ("GET", "pass/serviceLogin", reply({
            "result": "ok", "ssecurity": "s", "location": LOCATION})),
        ("GET", "sts.api.io.mi.com/sts", location_route(False)[2]),
    ])
    monkeypatch.setattr(auth_module, "find_cookie", lambda s, name: (
        "svc-token" if name == "serviceToken" else None))

    result = auth_module.login_with_token("7", "pass-old")

    assert (result.user_id, result.pass_token) == ("7", "pass-old")


def test_expired_token_is_reported_with_xiaomis_result(monkeypatch):
    token_login_session(monkeypatch, [
        ("GET", "pass/serviceLogin", reply({"result": "error"})),
    ])

    with pytest.raises(XiaomiAuthError, match="passToken rejected.*error"):
        auth_module.login_with_token("7", "stale")


def test_token_login_without_ssecurity_is_an_error(monkeypatch):
    token_login_session(monkeypatch, [
        ("GET", "pass/serviceLogin", reply({"result": "ok"})),
    ])

    with pytest.raises(XiaomiAuthError, match="no ssecurity"):
        auth_module.login_with_token("7", "pass")


@pytest.mark.parametrize("user_id, pass_token", [("", "t"), ("7", "")])
def test_token_login_requires_both_values(user_id, pass_token):
    with pytest.raises(ValueError):
        auth_module.login_with_token(user_id, pass_token)
