import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

import requests


@dataclass(frozen=True)
class XiaomiAuthResult:
    ssecurity: str
    service_token: str
    user_id: Optional[str]
    c_user_id: Optional[str]


class XiaomiEmailTwoFactorAuthenticator:
    """Complete Xiaomi's email-code challenge in an existing login session."""

    def __init__(
        self,
        session: requests.Session,
        user_agent: str,
        code_provider: Callable[[], str],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._session = session
        self._user_agent = user_agent
        self._code_provider = code_provider
        self._logger = logger or logging.getLogger(__name__)

    def authenticate(
        self,
        notification_url: str,
        user_id: Optional[str] = None,
        c_user_id: Optional[str] = None,
    ) -> Optional[XiaomiAuthResult]:
        headers = {
            "User-Agent": self._user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self._logger.debug("Opening Xiaomi 2FA notification URL")
        self._session.get(notification_url, headers=headers)

        context = parse_qs(urlparse(notification_url).query).get("context", [None])[0]
        if not context:
            self._logger.error("Xiaomi 2FA notification URL does not contain a context")
            return None

        list_params = {"sid": "xiaomiio", "context": context, "_locale": "en_US"}
        self._session.get(
            "https://account.xiaomi.com/identity/list",
            params=list_params,
            headers=headers,
        )

        send_params = {
            "_dc": str(int(time.time() * 1000)),
            "sid": "xiaomiio",
            "context": context,
            "mask": "0",
            "_locale": "en_US",
        }
        send_data = {
            "retry": "0",
            "icode": "",
            "_json": "true",
            "ick": self._session.cookies.get("ick", ""),
        }
        response = self._session.post(
            "https://account.xiaomi.com/identity/auth/sendEmailTicket",
            params=send_params,
            data=send_data,
            headers=headers,
        )
        try:
            send_response = response.json()
        except ValueError:
            send_response = {}
        self._logger.debug("sendEmailTicket response status=%s", response.status_code)

        code = self._code_provider().strip()
        verify_params = {
            "_flag": "8",
            "_json": "true",
            "sid": "xiaomiio",
            "context": context,
            "mask": "0",
            "_locale": "en_US",
        }
        verify_data = {
            "_flag": "8",
            "ticket": code,
            "trust": "false",
            "_json": "true",
            "ick": self._session.cookies.get("ick", ""),
        }
        response = self._session.post(
            "https://account.xiaomi.com/identity/auth/verifyEmail",
            params=verify_params,
            data=verify_data,
            headers=headers,
        )
        if response.status_code != 200:
            self._logger.error("verifyEmail failed: status=%s", response.status_code)
            return None

        try:
            finish_location = response.json().get("location")
        except ValueError:
            finish_location = response.headers.get("Location")
            if not finish_location and response.text:
                match = re.search(
                    r'https://account\.xiaomi\.com/identity/result/check\?[^"\']+',
                    response.text,
                )
                if match:
                    finish_location = match.group(0)

        if not finish_location:
            response = self._session.get(
                "https://account.xiaomi.com/identity/result/check",
                params={"sid": "xiaomiio", "context": context, "_locale": "en_US"},
                headers=headers,
                allow_redirects=False,
            )
            if response.status_code in (301, 302):
                finish_location = response.headers.get("Location")

        if not finish_location:
            self._logger.error("Unable to determine Xiaomi 2FA finish location")
            return None

        if "identity/result/check" in finish_location:
            response = self._session.get(
                finish_location,
                headers=headers,
                allow_redirects=False,
            )
            end_url = response.headers.get("Location")
        else:
            end_url = finish_location
        if not end_url:
            self._logger.error("Could not find Xiaomi Auth2/end URL")
            return None

        response = self._session.get(end_url, headers=headers, allow_redirects=False)
        if response.status_code == 200 and "Xiaomi Account - Tips" in response.text:
            response = self._session.get(end_url, headers=headers, allow_redirects=False)

        ssecurity = None
        extension_pragma = response.headers.get("extension-pragma")
        if extension_pragma:
            try:
                ssecurity = json.loads(extension_pragma).get("ssecurity")
            except (TypeError, ValueError):
                self._logger.debug("Unable to parse Xiaomi extension-pragma header")
        if not ssecurity:
            self._logger.error("Xiaomi Auth2/end did not provide ssecurity")
            return None

        sts_url = response.headers.get("Location")
        if not sts_url and response.text:
            start = response.text.find("https://sts.api.io.mi.com/sts")
            if start != -1:
                end = response.text.find('"', start)
                sts_url = response.text[start:end if end != -1 else start + 300]
        if not sts_url:
            self._logger.error("Xiaomi Auth2/end did not provide an STS redirect")
            return None

        response = self._session.get(sts_url, headers=headers, allow_redirects=True)
        if response.status_code != 200:
            self._logger.error("Xiaomi STS did not complete: status=%s", response.status_code)
            return None

        service_token = self._session.cookies.get(
            "serviceToken", domain=".sts.api.io.mi.com"
        )
        if not service_token:
            self._logger.error("Xiaomi STS did not set a service token")
            return None

        for domain in (".api.io.mi.com", ".io.mi.com", ".mi.com"):
            self._session.cookies.set("serviceToken", service_token, domain=domain)
            self._session.cookies.set("yetAnotherServiceToken", service_token, domain=domain)

        resolved_user_id = (
            user_id
            or self._session.cookies.get("userId", domain=".xiaomi.com")
            or self._session.cookies.get("userId", domain=".sts.api.io.mi.com")
        )
        resolved_c_user_id = (
            c_user_id
            or self._session.cookies.get("cUserId", domain=".xiaomi.com")
            or self._session.cookies.get("cUserId", domain=".sts.api.io.mi.com")
        )
        return XiaomiAuthResult(
            ssecurity=ssecurity,
            service_token=service_token,
            user_id=resolved_user_id,
            c_user_id=resolved_c_user_id,
        )