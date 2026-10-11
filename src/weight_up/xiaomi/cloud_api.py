"""Signed, encrypted calls to Xiaomi's regional cloud API."""

import os
import time
from typing import Any

import requests

from .constants import API_REGIONS
from .errors import XiaomiApiError
from .models import XiaomiAuthResult
from .session import generate_user_agent
from .signing import build_encrypted_params, build_nonce, decrypt_response

REQUEST_TIMEOUT_SECONDS = 30
DEVICE_COUNT_PATH = "/app/v2/user/get_device_cnt"

# Mi Home app cookies sent with every call; values mirror the reference client.
_APP_COOKIES = {
    "locale": "en_GB",
    "timezone": "GMT+02:00",
    "is_daylight": "1",
    "dst_offset": "3600000",
    "channel": "MI_APP_STORE",
}


def api_host(region: str) -> str:
    """Return the API hostname for region, rejecting unknown regions.

    Validating here keeps tokens from being sent to an arbitrary host.
    """
    if region not in API_REGIONS:
        raise ValueError(
            f"unsupported region {region!r}; expected one of {API_REGIONS}")
    return "api.io.mi.com" if region == "cn" else f"{region}.api.io.mi.com"


def call_encrypted_api(
    auth_result: XiaomiAuthResult,
    region: str,
    path: str,
    data: str,
    extra_headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> Any:
    """POST one signed, RC4-encrypted request and return the decoded result.

    path includes the /app prefix and data is the JSON request body as text.
    Raises XiaomiApiError on an HTTP error, an undecryptable reply, or a
    non-zero Xiaomi code.
    """
    host = api_host(region)
    nonce = build_nonce(os.urandom(8), time.time())
    form = build_encrypted_params(
        path, auth_result.ssecurity, nonce, {"data": data})
    response = (session or requests).post(
        f"https://{host}{path}",
        headers=_request_headers(extra_headers),
        cookies=_request_cookies(auth_result),
        data=form,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise XiaomiApiError(f"{host} returned HTTP {response.status_code}")

    try:
        body = decrypt_response(auth_result.ssecurity, nonce, response.text)
    except ValueError as error:
        raise XiaomiApiError(
            "response did not decrypt; ssecurity is probably wrong") from error
    if body.get("code") != 0:
        raise XiaomiApiError(
            f"{host} replied code={body.get('code')} message={body.get('message')}")
    return body.get("result")


def verify_tokens(
    auth_result: XiaomiAuthResult,
    region: str,
    session: requests.Session | None = None,
) -> None:
    """Prove the credentials work with one get_device_cnt call.

    Returns normally when the reply decrypts and Xiaomi reports code 0;
    raises XiaomiApiError otherwise. Checks one regional host only.
    """
    call_encrypted_api(
        auth_result,
        region,
        DEVICE_COUNT_PATH,
        '{"fetch_own": true, "fetch_share": true}',
        session=session,
    )


def _request_headers(extra_headers: dict[str, str] | None) -> dict[str, str]:
    return {
        "Accept-Encoding": "identity",
        "User-Agent": generate_user_agent(),
        "Content-Type": "application/x-www-form-urlencoded",
        "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
        "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
        **(extra_headers or {}),
    }


def _request_cookies(auth_result: XiaomiAuthResult) -> dict[str, str]:
    return {
        "userId": str(auth_result.user_id),
        "yetAnotherServiceToken": auth_result.service_token,
        "serviceToken": auth_result.service_token,
        **_APP_COOKIES,
    }
