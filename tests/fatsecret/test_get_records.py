import pytest

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

    def get(self, url, *, params):
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

    [record] = get_by_month()

    assert session.request == (
        "https://platform.fatsecret.com/rest/food-entries/month/v1",
        {"format": "json"},
    )
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

    assert get_by_month("xml") == [
        FatRecord(FatDate(), calories=12.5, carbs=3.0, protein=4.0, fat=5.0)
    ]
    assert session.request[1] == {"format": "xml"}


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
