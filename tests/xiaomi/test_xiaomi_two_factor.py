import pytest
from requests.cookies import RequestsCookieJar

from weight_up.xiaomi import XiaomiAuthError
from weight_up.xiaomi.two_factor import XiaomiEmailTwoFactorAuthenticator
from .xiaomi_fakes import FakeResponse, FakeSession

NOTIFICATION_URL = "https://account.xiaomi.com/identity/authStart?context=ctx-1"
CHECK_URL = "https://account.xiaomi.com/identity/result/check?ok=1"
END_URL = "https://account.xiaomi.com/serviceLoginAuth2/end"
STS_URL = "https://sts.api.io.mi.com/sts?token=1"


def sts_handler(session, kwargs):
    session.cookies.set("serviceToken", "svc-token",
                        domain=".sts.api.io.mi.com")
    session.cookies.set("passToken", "pass-token", domain=".xiaomi.com")
    session.cookies.set("userId", "cookie-user", domain=".xiaomi.com")
    session.cookies.set("cUserId", "cookie-c-user", domain=".xiaomi.com")
    return FakeResponse(200)


def happy_routes(verify_response=None):
    return [
        ("GET", "identity/authStart", FakeResponse(200)),
        ("GET", "identity/list", FakeResponse(200)),
        ("POST", "sendEmailTicket", FakeResponse(200, payload={"code": 0})),
        ("POST", "verifyEmail",
         verify_response or FakeResponse(200, payload={"location": CHECK_URL})),
        ("GET", "result/check",
         FakeResponse(302, headers={"Location": END_URL})),
        ("GET", "serviceLoginAuth2/end", FakeResponse(302, headers={
            "extension-pragma": '{"ssecurity":"sec-value"}',
            "Location": STS_URL})),
        ("GET", "sts.api.io.mi.com/sts", sts_handler),
    ]


def make(session, code="123456"):
    session.cookies.set("ick", "ick-value")
    return XiaomiEmailTwoFactorAuthenticator(
        session, "test-agent", code_provider=lambda: code)


def test_completes_challenge_and_returns_every_credential():
    session = FakeSession(happy_routes())

    result = make(session, code=" 123456 ").authenticate(NOTIFICATION_URL)

    assert result.ssecurity == "sec-value"
    assert result.service_token == "svc-token"
    assert result.pass_token == "pass-token"
    assert result.user_id == "cookie-user"
    assert result.c_user_id == "cookie-c-user"
    [(_, _, verify_call)] = session.calls_to("verifyEmail")
    assert verify_call["data"]["ticket"] == "123456"  # trimmed
    assert verify_call["data"]["ick"] == "ick-value"


def test_login_reply_ids_take_precedence_over_cookies():
    result = make(FakeSession(happy_routes())).authenticate(
        NOTIFICATION_URL, user_id="reply-user", c_user_id="reply-c-user")

    assert (result.user_id, result.c_user_id) == ("reply-user", "reply-c-user")


def test_service_token_is_mirrored_to_the_api_domains():
    session = FakeSession(happy_routes())

    make(session).authenticate(NOTIFICATION_URL)

    for domain in (".api.io.mi.com", ".io.mi.com", ".mi.com"):
        assert session.cookies.get(
            "serviceToken", domain=domain) == "svc-token"
        assert session.cookies.get(
            "yetAnotherServiceToken", domain=domain) == "svc-token"


def test_result_does_not_expose_secrets_in_repr():
    result = make(FakeSession(happy_routes())).authenticate(NOTIFICATION_URL)

    text = repr(result)

    assert "sec-value" not in text and "svc-token" not in text
    assert "pass-token" not in text


def test_notification_url_without_context_fails_before_any_request():
    session = FakeSession([])

    with pytest.raises(XiaomiAuthError, match="context"):
        make(session).authenticate(
            "https://account.xiaomi.com/identity/authStart")

    assert session.calls == []


def test_ticket_failure_stops_before_asking_for_a_code():
    routes = happy_routes()
    routes[2] = ("POST", "sendEmailTicket", FakeResponse(429))
    asked = []
    session = FakeSession(routes)
    session.cookies = RequestsCookieJar()
    authenticator = XiaomiEmailTwoFactorAuthenticator(
        session, "agent", code_provider=lambda: asked.append(1) or "1")

    with pytest.raises(XiaomiAuthError, match="sendEmailTicket failed: status=429"):
        authenticator.authenticate(NOTIFICATION_URL)

    assert asked == []


def test_verify_http_error_is_reported():
    routes = happy_routes(verify_response=FakeResponse(500))

    with pytest.raises(XiaomiAuthError, match="verifyEmail failed: status=500"):
        make(FakeSession(routes)).authenticate(NOTIFICATION_URL)


def test_non_json_verify_reply_falls_back_to_the_url_in_the_body():
    body = f'<a href="{CHECK_URL}">continue</a>'
    routes = happy_routes(verify_response=FakeResponse(200, text=body))

    result = make(FakeSession(routes)).authenticate(NOTIFICATION_URL)

    assert result.ssecurity == "sec-value"


def test_missing_location_falls_back_to_result_check_redirect():
    routes = happy_routes(
        verify_response=FakeResponse(200, payload={"code": 0}))
    session = FakeSession(routes)

    result = make(session).authenticate(NOTIFICATION_URL)

    [(_, _, fallback_call)] = session.calls_to("identity/result/check")
    assert fallback_call["params"]["context"] == "ctx-1"
    assert fallback_call["allow_redirects"] is False
    assert result.service_token == "svc-token"


def test_no_finish_location_anywhere_asks_the_user_to_check_the_code():
    routes = happy_routes(verify_response=FakeResponse(
        200, payload={"code": 70014}))
    routes.insert(4, ("GET", "identity/result/check", FakeResponse(200)))

    with pytest.raises(XiaomiAuthError, match="check the code"):
        make(FakeSession(routes)).authenticate(NOTIFICATION_URL)


def test_tips_page_is_requested_again():
    routes = happy_routes()
    tips = FakeResponse(200, text="<title>Xiaomi Account - Tips</title>")
    end_ok = routes[5][2]
    replies = iter([tips, end_ok])
    routes[5] = ("GET", "serviceLoginAuth2/end", lambda s, k: next(replies))
    session = FakeSession(routes)

    result = make(session).authenticate(NOTIFICATION_URL)

    assert len(session.calls_to("serviceLoginAuth2/end")) == 2
    assert result.ssecurity == "sec-value"


def test_missing_ssecurity_header_is_an_error():
    routes = happy_routes()
    routes[5] = ("GET", "serviceLoginAuth2/end",
                 FakeResponse(302, headers={"Location": STS_URL}))

    with pytest.raises(XiaomiAuthError, match="ssecurity"):
        make(FakeSession(routes)).authenticate(NOTIFICATION_URL)


def test_sts_url_can_be_read_from_the_body():
    routes = happy_routes()
    body = f'<a href="{STS_URL}">go</a>'
    routes[5] = ("GET", "serviceLoginAuth2/end", FakeResponse(
        200, text=body, headers={"extension-pragma": '{"ssecurity":"sec-value"}'}))

    result = make(FakeSession(routes)).authenticate(NOTIFICATION_URL)

    assert result.service_token == "svc-token"


def test_sts_without_a_service_cookie_is_an_error():
    routes = happy_routes()
    routes[6] = ("GET", "sts.api.io.mi.com/sts", FakeResponse(200))

    with pytest.raises(XiaomiAuthError, match="service token"):
        make(FakeSession(routes)).authenticate(NOTIFICATION_URL)
