"""Complete Xiaomi's email-code (2FA) challenge in an existing login session."""

import json
import logging
import re
import time
from typing import Callable
from urllib.parse import parse_qs, urlparse

import requests

from .constants import ACCOUNT_URL, SERVICE_ID, STS_URL_PREFIX
from .errors import XiaomiAuthError
from .models import XiaomiAuthResult
from .session import find_cookie, form_headers, text_or_none

_RESULT_CHECK_PATTERN = re.compile(
    r'https://account\.xiaomi\.com/identity/result/check\?[^"\']+')
_SERVICE_TOKEN_DOMAINS = (".api.io.mi.com", ".io.mi.com", ".mi.com")
_ID_COOKIE_DOMAINS = (".xiaomi.com", ".sts.api.io.mi.com")
_STS_URL_FALLBACK_LENGTH = 300


class XiaomiEmailTwoFactorAuthenticator:
    """Walk Xiaomi's identity flow: email a code, verify it, collect tokens.

    The session must be the one that received the notification URL, because
    the identity flow is bound to its cookies.
    """

    def __init__(
        self,
        session: requests.Session,
        user_agent: str,
        code_provider: Callable[[], str],
        logger: logging.Logger | None = None,
    ) -> None:
        self._session = session
        self._headers = form_headers(user_agent)
        self._code_provider = code_provider
        self._logger = logger or logging.getLogger(__name__)

    def authenticate(
        self,
        notification_url: str,
        user_id: str | None = None,
        c_user_id: str | None = None,
    ) -> XiaomiAuthResult:
        """Run the challenge and return the credentials it yields.

        code_provider is called once, after Xiaomi has emailed the code.
        user_id and c_user_id from the login reply take precedence over the
        values found in cookies. Raises XiaomiAuthError naming the failed step.
        """
        context = _extract_context(notification_url)
        self._open_notification(notification_url)
        self._list_verification_options(context)
        self._send_email_ticket(context)
        verify_response = self._verify_code(context, self._code_provider().strip())

        finish_location = self._find_finish_location(verify_response, context)
        end_url = self._resolve_auth_end_url(finish_location)
        end_response = self._call_auth_end(end_url)
        ssecurity = _read_ssecurity(end_response)
        service_token = self._complete_sts(_read_sts_url(end_response))
        self._share_service_token(service_token)

        return XiaomiAuthResult(
            ssecurity=ssecurity,
            service_token=service_token,
            user_id=user_id or self._cookie_from_known_domains("userId"),
            c_user_id=c_user_id or self._cookie_from_known_domains("cUserId"),
            pass_token=find_cookie(self._session, "passToken"),
        )

    def _identity_params(self, context: str, **extra: str) -> dict[str, str]:
        return {"sid": SERVICE_ID, "context": context, "_locale": "en_US", **extra}

    def _open_notification(self, notification_url: str) -> None:
        self._logger.debug("Opening Xiaomi 2FA notification URL")
        self._session.get(notification_url, headers=self._headers)

    def _list_verification_options(self, context: str) -> None:
        self._session.get(
            f"{ACCOUNT_URL}/identity/list",
            params=self._identity_params(context),
            headers=self._headers,
        )

    def _send_email_ticket(self, context: str) -> None:
        response = self._session.post(
            f"{ACCOUNT_URL}/identity/auth/sendEmailTicket",
            params=self._identity_params(
                context, _dc=str(int(time.time() * 1000)), mask="0"),
            data={
                "retry": "0",
                "icode": "",
                "_json": "true",
                "ick": find_cookie(self._session, "ick") or "",
            },
            headers=self._headers,
        )
        if response.status_code != 200:
            raise XiaomiAuthError(
                f"sendEmailTicket failed: status={response.status_code}")
        self._logger.debug("sendEmailTicket status=%s", response.status_code)

    def _verify_code(self, context: str, code: str) -> requests.Response:
        response = self._session.post(
            f"{ACCOUNT_URL}/identity/auth/verifyEmail",
            params=self._identity_params(
                context, _flag="8", _json="true", mask="0"),
            data={
                "_flag": "8",
                "ticket": code,
                "trust": "false",
                "_json": "true",
                "ick": find_cookie(self._session, "ick") or "",
            },
            headers=self._headers,
        )
        if response.status_code != 200:
            raise XiaomiAuthError(
                f"verifyEmail failed: status={response.status_code}")
        return response

    def _find_finish_location(
        self, verify_response: requests.Response, context: str
    ) -> str:
        location = _location_from_verify_response(verify_response)
        if location:
            return location

        # Fallback: ask result/check directly, relying on the identity session.
        fallback = self._session.get(
            f"{ACCOUNT_URL}/identity/result/check",
            params=self._identity_params(context),
            headers=self._headers,
            allow_redirects=False,
        )
        fallback_location = fallback.headers.get("Location")
        if fallback.status_code in (301, 302) and fallback_location:
            return fallback_location
        raise XiaomiAuthError(
            "Unable to determine the 2FA finish location; check the code")

    def _resolve_auth_end_url(self, finish_location: str) -> str:
        if "identity/result/check" not in finish_location:
            return finish_location
        # Do not follow redirects: the Location header is the Auth2/end URL.
        response = self._session.get(
            finish_location, headers=self._headers, allow_redirects=False)
        end_url = response.headers.get("Location")
        if not end_url:
            raise XiaomiAuthError("Could not find the Auth2/end URL")
        return end_url

    def _call_auth_end(self, end_url: str) -> requests.Response:
        # Redirects stay off so the extension-pragma header (with ssecurity)
        # is readable on this response.
        response = self._session.get(
            end_url, headers=self._headers, allow_redirects=False)
        if response.status_code == 200 and "Xiaomi Account - Tips" in response.text:
            # Xiaomi sometimes serves an HTML tips page first and redirects
            # on the repeat call.
            response = self._session.get(
                end_url, headers=self._headers, allow_redirects=False)
        return response

    def _complete_sts(self, sts_url: str) -> str:
        response = self._session.get(
            sts_url, headers=self._headers, allow_redirects=True)
        if response.status_code != 200:
            raise XiaomiAuthError(
                f"STS did not complete: status={response.status_code}")
        service_token = self._session.cookies.get(
            "serviceToken", domain=".sts.api.io.mi.com")
        if not service_token:
            raise XiaomiAuthError("STS did not set a service token")
        return service_token

    def _share_service_token(self, service_token: str) -> None:
        """Mirror the token to the API domains the cloud endpoints read."""
        for domain in _SERVICE_TOKEN_DOMAINS:
            self._session.cookies.set(
                "serviceToken", service_token, domain=domain)
            self._session.cookies.set(
                "yetAnotherServiceToken", service_token, domain=domain)

    def _cookie_from_known_domains(self, name: str) -> str | None:
        for domain in _ID_COOKIE_DOMAINS:
            value = self._session.cookies.get(name, domain=domain)
            if value:
                return text_or_none(value)
        return None


def _extract_context(notification_url: str) -> str:
    contexts = parse_qs(urlparse(notification_url).query).get("context")
    if not contexts or not contexts[0]:
        raise XiaomiAuthError(
            "The 2FA notification URL does not contain a context")
    return contexts[0]


def _location_from_verify_response(response: requests.Response) -> str | None:
    try:
        return response.json().get("location")
    except ValueError:
        pass
    # Non-JSON or empty body: try the header, then scan the body.
    header_location = response.headers.get("Location")
    if header_location:
        return header_location
    match = _RESULT_CHECK_PATTERN.search(response.text or "")
    return match.group(0) if match else None


def _read_ssecurity(auth_end_response: requests.Response) -> str:
    extension_pragma = auth_end_response.headers.get("extension-pragma")
    ssecurity = None
    if extension_pragma:
        try:
            ssecurity = json.loads(extension_pragma).get("ssecurity")
        except (TypeError, ValueError, AttributeError):
            ssecurity = None
    if not ssecurity:
        raise XiaomiAuthError("Auth2/end did not provide ssecurity")
    return ssecurity


def _read_sts_url(auth_end_response: requests.Response) -> str:
    location = auth_end_response.headers.get("Location")
    if location:
        return location
    body = auth_end_response.text or ""
    start = body.find(STS_URL_PREFIX)
    if start == -1:
        raise XiaomiAuthError("Auth2/end did not provide an STS redirect")
    end = body.find('"', start)
    return body[start:end if end != -1 else start + _STS_URL_FALLBACK_LENGTH]
