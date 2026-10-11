"""Fetch raw scale records from Xiaomi's getUserDataByPage endpoint."""

import json
import time
from typing import Any

import requests

from .cloud_api import call_encrypted_api
from .constants import SCALE_REGIONS
from .errors import XiaomiApiError
from .models import XiaomiAuthResult

SCALE_DATA_PATH = "/app/eco/common/scale/getUserDataByPage"
SCALE_PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 500


def validate_scale_request(
    auth_result: XiaomiAuthResult, region: str, model: str
) -> None:
    """Fail early on inputs that can never produce scale data."""
    if region not in SCALE_REGIONS:
        raise ValueError(
            f"scale data is only supported for {SCALE_REGIONS}, got {region!r}")
    if not model:
        raise ValueError("a scale model is required")
    if not auth_result.user_id:
        raise ValueError("user_id is required to query scale data")


def fetch_scale_records(
    auth_result: XiaomiAuthResult,
    region: str,
    model: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Page through raw scale records for one model, newest first.

    Records are returned unparsed; createTime is in milliseconds. Raises
    XiaomiApiError if max_pages is reached with data remaining, or if the
    paging cursor stops advancing, rather than returning a silent truncation.
    """
    validate_scale_request(auth_result, region, model)
    records: list[dict[str, Any]] = []
    begin_time = int(time.time() * 1000)
    for _ in range(max_pages):
        page = _fetch_page(auth_result, region, model, begin_time, session)
        records.extend(page)
        next_begin_time = _next_begin_time(page)
        if next_begin_time is None:
            return records
        if next_begin_time >= begin_time:
            raise XiaomiApiError("Scale paging did not advance")
        begin_time = next_begin_time
    raise XiaomiApiError(
        f"Stopped after {max_pages} pages; more scale data may remain")


def _fetch_page(
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
