"""Log in to Xiaomi Cloud and return credentials for signed API calls.

Two entry points:

- login: email and password, with the captcha and email-code challenges
  delegated to caller-supplied providers.
- login_with_token: re-issue credentials from a saved passToken, with no
  password and no 2FA code.

Both raise XiaomiAuthError, naming the failed step, instead of returning a
partial result.
"""

import hashlib
import logging
from typing import Any, Callable

import requests

from .constants import ACCOUNT_URL, SERVICE_ID
from .errors import XiaomiAuthError
from .models import XiaomiAuthResult
from .session import (
    find_cookie,
    form_headers,
    generate_user_agent,
    parse_response,
    start_login_session,
    text_or_none,
)
from .two_factor import XiaomiEmailTwoFactorAuthenticator

CodeProvider = Callable[[], str]
CaptchaProvider = Callable[[bytes], str]


def login(
    email: str,
    password: str,
    code_provider: CodeProvider,
    captcha_provider: CaptchaProvider | None = None,
    logger: logging.Logger | None = None,
) -> XiaomiAuthResult:
    """Log in with email and password, completing any challenge Xiaomi raises.

    code_provider is called once, after Xiaomi has emailed the 2FA code, and
    returns it. captcha_provider receives the captcha image bytes and returns
    the text shown; without it a captcha ends the login. The result includes
    a pass_token when Xiaomi sets one, so later runs can use login_with_token.
    """
    if not email or not password:
        raise ValueError("email and password are required")
    logger = logger or logging.getLogger(__name__)
    user_agent = generate_user_agent()
    session = start_login_session()

    sign = _request_login_sign(session, user_agent, email)
    reply = _submit_credentials(session, user_agent, email, password, sign)
    if reply.get("captchaUrl"):
        reply = _solve_captcha(
            session, user_agent, email, password, sign, reply, captcha_provider)

    if reply.get("notificationUrl"):
        return XiaomiEmailTwoFactorAuthenticator(
            session, user_agent, code_provider, logger
        ).authenticate(
            reply["notificationUrl"],
            user_id=text_or_none(reply.get("userId")),
            c_user_id=text_or_none(reply.get("cUserId")),
        )
    if reply.get("ssecurity") and reply.get("location"):
        return _complete_without_two_factor(session, user_agent, reply)
    raise XiaomiAuthError(f"Login rejected (code={reply.get('code')})")


def login_with_token(
    user_id: str,
    pass_token: str,
    logger: logging.Logger | None = None,
) -> XiaomiAuthResult:
    """Re-issue ssecurity and serviceToken from a saved passToken.

    Raises XiaomiAuthError if Xiaomi rejects the token, for example because
    it has expired; the caller then needs a full login.
    """
    if not user_id or not pass_token:
        raise ValueError("user_id and pass_token are required")
    (logger or logging.getLogger(__name__)).debug("Logging in with passToken")
    user_agent = generate_user_agent()
    session = requests.Session()

    response = session.get(
        f"{ACCOUNT_URL}/pass/serviceLogin",
        params={"_json": "true", "sid": SERVICE_ID},
        headers={"User-Agent": user_agent},
        cookies={"userId": user_id, "passToken": pass_token},
    )
    reply = _read_reply(response, "serviceLogin")
    if reply.get("result") != "ok":
        raise XiaomiAuthError(
            f"passToken rejected (result={reply.get('result')})")
    if not (reply.get("ssecurity") and reply.get("location")):
        raise XiaomiAuthError("serviceLogin gave no ssecurity or location")

    reply.setdefault("userId", user_id)
    reply.setdefault("passToken", pass_token)
    return _complete_without_two_factor(session, user_agent, reply)


def _read_reply(response: requests.Response, step: str) -> dict[str, Any]:
    if response.status_code != 200:
        raise XiaomiAuthError(f"{step} failed: status={response.status_code}")
    try:
        return parse_response(response.text)
    except ValueError as error:
        raise XiaomiAuthError(f"{step} returned an unreadable reply") from error


def _request_login_sign(
    session: requests.Session, user_agent: str, email: str
) -> str:
    response = session.get(
        f"{ACCOUNT_URL}/pass/serviceLogin?sid={SERVICE_ID}&_json=true",
        headers={"User-Agent": user_agent},
        cookies={"userId": email},
    )
    sign = _read_reply(response, "serviceLogin").get("_sign")
    if not sign:
        raise XiaomiAuthError("serviceLogin did not return a _sign; check the email")
    return sign


def _submit_credentials(
    session: requests.Session,
    user_agent: str,
    email: str,
    password: str,
    sign: str,
    captcha_code: str | None = None,
) -> dict[str, Any]:
    # Xiaomi expects an upper-case MD5 of the password, not the password itself.
    fields = {
        "sid": SERVICE_ID,
        "hash": hashlib.md5(password.encode()).hexdigest().upper(),
        "callback": "https://sts.api.io.mi.com/sts",
        "qs": "%3Fsid%3Dxiaomiio%26_json%3Dtrue",
        "user": email,
        "_sign": sign,
        "_json": "true",
    }
    if captcha_code:
        fields["captCode"] = captcha_code
    response = session.post(
        f"{ACCOUNT_URL}/pass/serviceLoginAuth2",
        params=fields,
        headers=form_headers(user_agent),
        allow_redirects=False,
    )
    return _read_reply(response, "serviceLoginAuth2")


def _fetch_captcha_image(
    session: requests.Session, user_agent: str, captcha_url: str
) -> bytes:
    # The captcha is bound to this session, so it must be fetched with it.
    if captcha_url.startswith("/"):
        captcha_url = ACCOUNT_URL + captcha_url
    response = session.get(captcha_url, headers={"User-Agent": user_agent})
    if response.status_code != 200:
        raise XiaomiAuthError("Unable to download the captcha image")
    return response.content


def _solve_captcha(
    session: requests.Session,
    user_agent: str,
    email: str,
    password: str,
    sign: str,
    reply: dict[str, Any],
    captcha_provider: CaptchaProvider | None,
) -> dict[str, Any]:
    """Resubmit the credentials once with the captcha text."""
    if captcha_provider is None:
        raise XiaomiAuthError(
            "Xiaomi requires a captcha and no solver was given")
    image = _fetch_captcha_image(session, user_agent, reply["captchaUrl"])
    captcha_code = captcha_provider(image).strip()
    if not captcha_code:
        raise XiaomiAuthError("No captcha text provided")

    retry_reply = _submit_credentials(
        session, user_agent, email, password, sign, captcha_code)
    if retry_reply.get("captchaUrl") or retry_reply.get("code") == 87001:
        raise XiaomiAuthError("Captcha rejected; run again for a new one")
    return retry_reply


def _complete_without_two_factor(
    session: requests.Session,
    user_agent: str,
    reply: dict[str, Any],
) -> XiaomiAuthResult:
    """Fetch the service token from the reply's location URL."""
    response = session.get(reply["location"], headers={"User-Agent": user_agent})
    service_token = (
        response.cookies.get("serviceToken")
        or find_cookie(session, "serviceToken")
    )
    if response.status_code != 200 or not service_token:
        raise XiaomiAuthError(
            "Could not fetch a service token from the location URL")
    return XiaomiAuthResult(
        ssecurity=str(reply["ssecurity"]),
        service_token=service_token,
        user_id=text_or_none(reply.get("userId")),
        c_user_id=text_or_none(reply.get("cUserId")),
        pass_token=(
            text_or_none(reply.get("passToken"))
            or find_cookie(session, "passToken")
        ),
    )
