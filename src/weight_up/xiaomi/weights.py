"""Pure conversion of raw Xiaomi scale records into XiaomiWeight values."""

import json
from datetime import datetime, timezone
from typing import Any, Iterable

from .models import XiaomiApiError, XiaomiWeight

# fromSource values that carry weight data; others are ignored.
_SOURCES_WITH_USER_BLOCK = (1, 2)
_SOURCE_WITH_BODY_BLOCK = 3


def parse_scale_records(records: Iterable[dict[str, Any]]) -> list[XiaomiWeight]:
    """Convert raw records to weights, skipping unsupported sources.

    Raises XiaomiApiError naming the record index if a supported record is
    malformed, so a format change is noticed instead of silently dropped.
    """
    weights = []
    for index, record in enumerate(records):
        try:
            weight = _parse_record(record)
        except (KeyError, TypeError, ValueError) as error:
            raise XiaomiApiError(
                f"Malformed scale record at index {index}: {error!r}"
            ) from error
        if weight is not None:
            weights.append(weight)
    return weights


def _parse_record(record: dict[str, Any]) -> XiaomiWeight | None:
    source_type = _int(record.get("fromSource"))
    if source_type in _SOURCES_WITH_USER_BLOCK:
        return _parse_user_block_record(record, source_type)
    if source_type == _SOURCE_WITH_BODY_BLOCK:
        return _parse_body_block_record(record)
    return None


def _parse_user_block_record(
    record: dict[str, Any], source_type: int
) -> XiaomiWeight:
    value = json.loads(record["data"])
    user = value.get("user") or {}
    source = (
        str(value.get("reportFrom", ""))
        if source_type == 1
        else str(user.get("deviceId", ""))
    )
    return XiaomiWeight(
        date=_timestamp_millis(record.get("createTime")),
        weight=_float(value.get("weight")),
        bmi=_float(value.get("bmi")),
        body_fat=_float(value.get("bfp")),
        body_water=_float(value.get("bwp")),
        bone_mass=_float(value.get("bmc")),
        metabolic_age=_int(value.get("ma")),
        muscle_mass=_float(value.get("slm")),
        physique_rating=_int(value.get("bt")),
        protein_mass=_float(value.get("pm")),
        visceral_fat=_int(value.get("vfl")),
        basal_metabolism=_int(value.get("bmr")),
        body_score=_int(value.get("sbc")),
        heart_rate=_int(value.get("heartRate")),
        height=_float(user.get("height")),
        skeletal_muscle_mass=_float(value.get("smm")),
        user=str(user.get("name", "")),
        source=source,
    )


def _parse_body_block_record(record: dict[str, Any]) -> XiaomiWeight:
    value = json.loads(record["data"])
    user = value.get("user") or {}
    details = _parse_body_details(value.get("bodyResData", ""))
    return XiaomiWeight(
        date=_timestamp_millis(value.get("time")),
        weight=_float(value.get("weight")),
        bmi=_float(value.get("bmi")),
        heart_rate=_int(value.get("heartRate")),
        user=str(user.get("name", "")),
        source=str(record.get("did", "")),
        **details,
    )


def _parse_body_details(body_res_data: str) -> dict[str, Any]:
    """Return body-composition fields from the nested bodyResData JSON string."""
    if not body_res_data:
        return {}
    details = json.loads(body_res_data)
    return {
        "body_fat": _float(details.get("bfp")),
        "body_water": _float(details.get("bwp")),
        "bone_mass": _float(details.get("bmc")),
        "metabolic_age": _int(details.get("ma")),
        "muscle_mass": _float(details.get("slm")),
        "protein_mass": _float(details.get("pm")),
        "visceral_fat": _int(details.get("vfl")),
        "basal_metabolism": _int(details.get("bmr")),
        "body_score": _int(details.get("sbc")),
        "skeletal_muscle_mass": _float(details.get("smm")),
    }


def _float(value: Any) -> float:
    if isinstance(value, bool) or value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _timestamp_millis(milliseconds: Any) -> datetime:
    return datetime.fromtimestamp(_int(milliseconds) / 1000, tz=timezone.utc)
