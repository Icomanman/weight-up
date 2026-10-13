"""Client for Xiaomi's regional cloud API host.

Everything that talks to <region>.api.io.mi.com lives here: one signed,
encrypted request, a credential check, and the paged scale-history endpoint.

It does not log in (see auth), implement the cryptography (see signing), or
interpret the records it fetches (see weights).
"""

import json
import os
import time
from typing import Any

import requests

from .models import XiaomiApiError, XiaomiAuthResult, XiaomiWeight
from .session import generate_user_agent
from .signing import build_encrypted_params, build_nonce, decrypt_response
from .weights import parse_scale_records

# Regions that serve scale data through getUserDataByPage.
SCALE_REGIONS = ("de", "i2", "ru", "sg", "us")

# Regions with a known api.io.mi.com host. cn has no region prefix.
API_REGIONS = ("cn", *SCALE_REGIONS, "tw", "in")

REQUEST_TIMEOUT_SECONDS = 30
DEVICE_COUNT_PATH = "/app/v2/user/get_device_cnt"
SCALE_DATA_PATH = "/app/eco/common/scale/getUserDataByPage"
SCALE_PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 500

# Mi Home app cookies sent with every call; values mirror the reference client.
_APP_COOKIES = {
    "locale": "en_GB",
    "timezone": "GMT+02:00",
    "is_daylight": "1",
    "dst_offset": "3600000",
    "channel": "MI_APP_STORE",
}


# Signed transport
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
        path,
        auth_result.ssecurity,
        nonce,
        {"data": data}
    )
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


# Scale history
def fetch_weights(
    auth_result: XiaomiAuthResult,
    region: str,
    model: str,
    session: requests.Session | None = None,
) -> list[XiaomiWeight]:
    """Return every weigh-in Xiaomi holds for one scale model, newest first."""
    records = fetch_scale_records(auth_result, region, model, session=session)
    return parse_scale_records(records)


def fetch_scale_records(
    auth_result: XiaomiAuthResult,
    region: str,
    model: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Page through raw scale records for one model, newest first.

    Records are returned unparsed; createTime is in milliseconds. Raises
    ValueError for inputs that can never work, before any request is made, and
    XiaomiApiError if max_pages is reached with data remaining or the paging
    cursor stops advancing, rather than returning a silent truncation.
    """
    _validate_scale_request(auth_result, region, model)
    records: list[dict[str, Any]] = []
    begin_time = int(time.time() * 1000)
    for _ in range(max_pages):
        page = _fetch_scale_page(
            auth_result,
            region,
            model,
            begin_time,
            session
        )
        records.extend(page)
        next_begin_time = _next_begin_time(page)
        if next_begin_time is None:
            return records
        if next_begin_time >= begin_time:
            raise XiaomiApiError("Scale paging did not advance")
        begin_time = next_begin_time
    raise XiaomiApiError(
        f"Stopped after {max_pages} pages; more scale data may remain"
    )


def _validate_scale_request(
    auth_result: XiaomiAuthResult, region: str, model: str
) -> None:
    if region not in SCALE_REGIONS:
        raise ValueError(
            f"scale data is only supported for {SCALE_REGIONS}, got {region!r}")
    if not model:
        raise ValueError("a scale model is required")
    if not auth_result.user_id:
        raise ValueError("user_id is required to query scale data")


def _fetch_scale_page(
    auth_result: XiaomiAuthResult,
    region: str,
    model: str,
    begin_time: int,
    session: requests.Session | None,
) -> list[dict[str, Any]]:
    query = {
        "endTime": 1,
        "beginTime": begin_time,
        "model": model,
        "uid": str(auth_result.user_id),
        "did": 0,
        "accountId": 0,
    }
    result = call_encrypted_api(
        auth_result,
        region,
        SCALE_DATA_PATH,
        json.dumps(query, separators=(",", ":")),
        {"MIOT-REQUEST-MODEL": model},
        session,
    )
    return result or []


def _next_begin_time(page: list[dict[str, Any]]) -> int | None:
    """Return the cursor for the next page, or None when this was the last."""
    if len(page) < SCALE_PAGE_SIZE:
        return None
    # Xiaomi pages by the createTime of the last record on a full page.
    try:
        return int(page[SCALE_PAGE_SIZE - 1]["createTime"])
    except (KeyError, TypeError, ValueError) as error:
        raise XiaomiApiError(
            f"Scale record has no usable createTime: {error!r}") from error
