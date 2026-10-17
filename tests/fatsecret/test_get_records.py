import pytest

from datetime import date

from weight_up.fatsecret import get_records
from weight_up.fatsecret.get_records import FatDate, FatRecord, get_by_month


class FakeResponse:
    def __init__(self, payload=None, content=b"", error=None):
        self.payload = payload
        self.content = content
        self.error = error

    def raise_for_status(self):
        if self.error is not None:
            raise self.error

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.request = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def get(self, url, *, params, **kwargs):
        self.request = (url, params)
        return self.response


def test_get_by_month_signs_get_and_parses_monthly_days(monkeypatch):
    session = FakeSession(FakeResponse({
        "month": {
            "day": [
                {
                    "date_int": "19782",
                    "calories": "1234.5",
                    "carbohydrate": "125.25",
                    "protein": "80",
                    "fat": "42.5",
                }
            ]
        }
    }))
    monkeypatch.setattr(get_records, "create_authenticated_session", lambda: session)
    monkeypatch.setattr(get_records, "_today", lambda: date(1970, 1, 1))

    [record] = get_by_month()

    assert session.request[0] == (
        "https://platform.fatsecret.com/rest/food-entries/month/v1"
    )
    assert session.request[1] == {"date": 0, "format": "json"}
    assert record == FatRecord(
        date=FatDate(2024, 2, 29),
        calories=1234.5,
        carbs=125.25,
        protein=80.0,
        fat=42.5,
    )


def test_get_by_month_handles_a_single_day_object(monkeypatch):
    session = FakeSession(FakeResponse({
        "month": {
            "day": {
                "date_int": "0",
                "calories": "0",
                "carbohydrate": "0",
                "protein": "0",
                "fat": "0",
            }
        }
    }))
    monkeypatch.setattr(get_records, "create_authenticated_session", lambda: session)

    assert get_by_month() == [
        FatRecord(FatDate(), calories=0.0, carbs=0.0, protein=0.0, fat=0.0)
    ]


def test_get_by_month_parses_xml(monkeypatch):
    session = FakeSession(FakeResponse(content=(
        b"<food_entries><month><day><date_int>0</date_int>"
        b"<calories>12.5</calories><carbohydrate>3</carbohydrate>"
        b"<protein>4</protein><fat>5</fat></day></month></food_entries>"
    )))
    monkeypatch.setattr(get_records, "create_authenticated_session", lambda: session)
    monkeypatch.setattr(get_records, "_today", lambda: date(1970, 1, 1))

    assert get_by_month("xml") == [
        FatRecord(FatDate(), calories=12.5, carbs=3.0, protein=4.0, fat=5.0)
    ]
    assert session.request[1] == {"date": 0, "format": "xml"}


def test_get_by_month_returns_empty_list_when_month_has_no_days(monkeypatch):
    session = FakeSession(FakeResponse({"month": {}}))
    monkeypatch.setattr(get_records, "create_authenticated_session", lambda: session)

    assert get_by_month() == []


def test_get_by_month_propagates_http_errors(monkeypatch):
    session = FakeSession(FakeResponse(error=RuntimeError("HTTP failure")))
    monkeypatch.setattr(get_records, "create_authenticated_session", lambda: session)

    with pytest.raises(RuntimeError, match="HTTP failure"):
        get_by_month()


def test_fat_date_resolves_calendar_days_exactly():
    assert FatDate(2024, 3, 1).resolve() - FatDate(2024, 2, 28).resolve() == 2


class SequenceSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def get(self, url, *, params, **kwargs):
        self.requests.append((url, params))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def month_response(date_int):
    return FakeResponse({
        "month": {
            "day": {
                "date_int": str(date_int),
                "calories": "100",
                "carbohydrate": "20",
                "protein": "30",
                "fat": "40",
            }
        }
    })


def test_get_all_walks_months_back_to_the_fatsecret_epoch(monkeypatch, tmp_path):
    session = SequenceSession([
        month_response(63),
        month_response(31),
        month_response(0),
    ])
    monkeypatch.setattr(get_records, "create_authenticated_session", lambda: session)
    monkeypatch.setattr(get_records, "_today", lambda: date(1970, 3, 5))

    records = get_records.get_all(output_path=tmp_path / "records.jsonl")

    assert [params["date"] for _, params in session.requests] == [63, 58, 30]
    assert [record.date for record in records] == [
        FatDate(1970, 3, 5),
        FatDate(1970, 2, 1),
        FatDate(1970, 1, 1),
    ]
    assert len((tmp_path / "records.jsonl").read_text().splitlines()) == 3


def test_get_all_resumes_at_the_interrupted_month(monkeypatch, tmp_path):
    output_path = tmp_path / "records.jsonl"
    first_session = SequenceSession([
        month_response(63),
        RuntimeError("connection interrupted"),
    ])
    monkeypatch.setattr(
        get_records, "create_authenticated_session", lambda: first_session
    )
    monkeypatch.setattr(get_records, "_today", lambda: date(1970, 3, 5))

    with pytest.raises(RuntimeError, match="connection interrupted"):
        get_records.get_all(output_path=output_path)

    resumed_session = SequenceSession([month_response(31), month_response(0)])
    monkeypatch.setattr(
        get_records, "create_authenticated_session", lambda: resumed_session
    )

    records = get_records.get_all(output_path=output_path)

    assert [params["date"] for _, params in resumed_session.requests] == [58, 30]
    assert len(records) == 3
    assert len(output_path.read_text().splitlines()) == 3


def test_get_all_returns_saved_records_after_a_completed_run(
    monkeypatch,
    tmp_path,
):
    output_path = tmp_path / "records.jsonl"
    first_session = SequenceSession([
        month_response(63),
        month_response(31),
        month_response(0),
    ])
    monkeypatch.setattr(
        get_records, "create_authenticated_session", lambda: first_session
    )
    monkeypatch.setattr(get_records, "_today", lambda: date(1970, 3, 5))
    records = get_records.get_all(output_path=output_path)
    monkeypatch.setattr(
        get_records,
        "create_authenticated_session",
        lambda: pytest.fail("completed output should not make more requests"),
    )

    saved_records = get_records.get_all(output_path=output_path)

    assert saved_records == records
