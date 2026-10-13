import base64

import pytest

from weight_up.xiaomi import XiaomiApiError, XiaomiAuthResult, fetch_weights
from weight_up.xiaomi.api import (
    api_host,
    call_encrypted_api,
    fetch_scale_records,
    verify_tokens,
)
from .xiaomi_fakes import EncryptedApi

SSECURITY = base64.b64encode(bytes(range(16))).decode()
OTHER_KEY = base64.b64encode(bytes(range(16, 32))).decode()
AUTH = XiaomiAuthResult(SSECURITY, "svc-token", "7", None)
MODEL = "yunmai.scales.ms104"


def full_page(newest_time: int) -> list[dict]:
    return [{"createTime": newest_time - index, "fromSource": 9} for index in range(20)]


def test_verify_passes_when_the_reply_decrypts_with_code_zero():
    api = EncryptedApi(SSECURITY)

    verify_tokens(AUTH, "sg", session=api)

    [(url, body, kwargs)] = api.requests
    assert url == "https://sg.api.io.mi.com/app/v2/user/get_device_cnt"
    assert body == {"fetch_own": True, "fetch_share": True}
    assert kwargs["cookies"]["serviceToken"] == "svc-token"
    assert kwargs["cookies"]["userId"] == "7"
    assert "params" not in kwargs  # fields travel in the POST body


def test_cn_uses_the_unprefixed_host():
    assert api_host("cn") == "api.io.mi.com"
    assert api_host("de") == "de.api.io.mi.com"


@pytest.mark.parametrize("region", ["evil.com/", "", "SG", "xx"])
def test_unknown_region_is_rejected_before_any_request(region):
    api = EncryptedApi(SSECURITY)

    with pytest.raises(ValueError):
        call_encrypted_api(AUTH, region, "/app/v2/x", "{}", session=api)

    assert api.requests == []


def test_nonzero_code_is_reported_with_the_message():
    api = EncryptedApi(SSECURITY, code=3)

    with pytest.raises(XiaomiApiError, match="code=3 message=fake"):
        verify_tokens(AUTH, "sg", session=api)


def test_wrong_ssecurity_is_called_out():
    api = EncryptedApi(SSECURITY, reply_key=OTHER_KEY)

    with pytest.raises(XiaomiApiError, match="ssecurity is probably wrong"):
        verify_tokens(AUTH, "sg", session=api)


def test_http_error_is_reported_with_the_host():
    class Rejecting:
        def post(self, url, **kwargs):
            from .xiaomi_fakes import FakeResponse
            return FakeResponse(401)

    with pytest.raises(XiaomiApiError, match="sg.api.io.mi.com returned HTTP 401"):
        verify_tokens(AUTH, "sg", session=Rejecting())


def test_scale_pages_follow_the_twentieth_record_cursor():
    page_one = full_page(1_700_000_000_000)
    api = EncryptedApi(SSECURITY, pages=[
                       page_one, full_page(1_600_000_000_000)[:5]])

    records = fetch_scale_records(AUTH, "sg", MODEL, session=api)

    assert len(records) == 25
    first_url, first_body, first_kwargs = api.requests[0]
    assert first_url == "https://sg.api.io.mi.com/app/eco/common/scale/getUserDataByPage"
    assert first_body["model"] == MODEL
    assert first_body["uid"] == "7"  # sent as a string, as the app does
    assert first_kwargs["headers"]["MIOT-REQUEST-MODEL"] == MODEL
    assert api.requests[1][1]["beginTime"] == page_one[19]["createTime"]


def test_a_short_first_page_is_the_only_request():
    api = EncryptedApi(SSECURITY, pages=[full_page(1_700_000_000_000)[:3]])

    assert len(fetch_scale_records(AUTH, "sg", MODEL, session=api)) == 3
    assert len(api.requests) == 1


def test_a_cursor_that_does_not_advance_is_an_error():
    future = 9_999_999_999_999
    api = EncryptedApi(SSECURITY, pages=[full_page(future)])

    with pytest.raises(XiaomiApiError, match="did not advance"):
        fetch_scale_records(AUTH, "sg", MODEL, session=api)


def test_hitting_the_page_limit_is_an_error_not_a_truncation():
    pages = [full_page(1_700_000_000_000 - n * 1_000_000) for n in range(3)]
    api = EncryptedApi(SSECURITY, pages=pages)

    with pytest.raises(XiaomiApiError, match="Stopped after 2 pages"):
        fetch_scale_records(AUTH, "sg", MODEL, max_pages=2, session=api)


def test_full_page_without_create_time_is_an_error():
    page = full_page(1_700_000_000_000)
    del page[19]["createTime"]
    api = EncryptedApi(SSECURITY, pages=[page])

    with pytest.raises(XiaomiApiError, match="createTime"):
        fetch_scale_records(AUTH, "sg", MODEL, session=api)


@pytest.mark.parametrize("region", ["cn", "tw", "in", "mars"])
def test_regions_without_the_scale_endpoint_fail_early(region):
    with pytest.raises(ValueError, match="only supported"):
        fetch_scale_records(AUTH, region, MODEL,
                            session=EncryptedApi(SSECURITY))


def test_missing_model_or_user_id_fails_before_any_request():
    no_user = XiaomiAuthResult(SSECURITY, "svc", None, None)
    api = EncryptedApi(SSECURITY)

    with pytest.raises(ValueError, match="model"):
        fetch_weights(AUTH, "sg", "", session=api)
    with pytest.raises(ValueError, match="user_id"):
        fetch_weights(no_user, "sg", MODEL, session=api)

    assert api.requests == []


def test_fetch_weights_returns_parsed_weights():
    record = {"fromSource": 1, "createTime": 1_700_000_000_000,
              "data": '{"weight": 70.5, "user": {"name": "me"}}'}
    api = EncryptedApi(SSECURITY, pages=[[record]])

    [weight] = fetch_weights(AUTH, "sg", MODEL, session=api)

    assert (weight.weight, weight.user) == (70.5, "me")
