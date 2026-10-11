import json
from datetime import datetime, timezone

import pytest

from weight_up.xiaomi import XiaomiApiError, XiaomiWeight
from weight_up.xiaomi.weights import parse_scale_records

CREATE_TIME_MS = 1_700_000_000_000
EXPECTED_DATE = datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)


def user_block_record(from_source: int) -> dict:
    return {
        "fromSource": from_source,
        "createTime": CREATE_TIME_MS,
        "data": json.dumps({
            "weight": 70.5, "bmi": "22.1", "bfp": 18.2, "bwp": 55, "bmc": 3.1,
            "ma": 30, "slm": 50.2, "bt": 2, "pm": 14.4, "vfl": 8, "bmr": 1600,
            "sbc": 80, "heartRate": 60, "smm": 31.0, "reportFrom": "app",
            "user": {"name": "me", "height": "175", "deviceId": "dev-9"},
        }),
    }


def body_block_record(body_res_data: str) -> dict:
    return {
        "fromSource": 3,
        "did": "blt.3.abc",
        "createTime": 0,
        "data": json.dumps({
            "time": str(CREATE_TIME_MS), "weight": "71.2", "bmi": "22.5",
            "heartRate": 61, "user": {"name": "me"}, "bodyResData": body_res_data,
        }),
    }


def test_source_1_reads_user_block_and_report_source():
    [weight] = parse_scale_records([user_block_record(1)])

    assert weight.date == EXPECTED_DATE
    assert weight.weight == 70.5
    assert weight.bmi == 22.1  # numeric strings are accepted
    assert weight.height == 175.0
    assert weight.user == "me"
    assert weight.source == "app"


def test_source_2_takes_source_from_the_device_id():
    [weight] = parse_scale_records([user_block_record(2)])

    assert weight.source == "dev-9"


def test_source_3_reads_nested_body_composition_and_device_id():
    nested = json.dumps({"bfp": "19.1", "bwp": "54", "ma": "31", "vfl": "9"})

    [weight] = parse_scale_records([body_block_record(nested)])

    assert weight.date == EXPECTED_DATE
    assert weight.weight == 71.2
    assert weight.body_fat == 19.1
    assert weight.metabolic_age == 31
    assert weight.source == "blt.3.abc"


def test_source_3_without_body_composition_leaves_defaults():
    [weight] = parse_scale_records([body_block_record("")])

    assert weight.body_fat == 0.0
    assert weight.visceral_fat == 0


def test_unsupported_sources_are_skipped():
    assert parse_scale_records([{"fromSource": 9, "data": "{}"}]) == []


def test_missing_values_become_defaults_not_errors():
    record = {"fromSource": 1, "data": json.dumps({"weight": None, "user": None})}

    [weight] = parse_scale_records([record])

    assert weight.weight == 0.0
    assert weight.user == ""


def test_malformed_record_names_its_index():
    records = [user_block_record(1), {"fromSource": 1}]

    with pytest.raises(XiaomiApiError, match="index 1"):
        parse_scale_records(records)


def test_weights_are_immutable():
    [weight] = parse_scale_records([user_block_record(1)])

    assert isinstance(weight, XiaomiWeight)
    with pytest.raises(AttributeError):
        weight.weight = 1.0  # type: ignore[misc]
