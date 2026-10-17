from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from requests_oauthlib import OAuth1Session

from .auth import create_authenticated_session
from .writer import FatSecretJsonlWriter


_FATSECRET_EPOCH = date(1970, 1, 1)
_ENDPOINT = "https://platform.fatsecret.com/rest/food-entries/month/v1"
_DEFAULT_OUTPUT_PATH = Path("fatsecret_records.jsonl")


@dataclass(frozen=True, slots=True)
class FatDate:
    """
    Default values are based on FatSecret's base date: 01 January 1970
    """
    year: int = 1970
    month: int = 1
    day: int = 1

    def resolve(self) -> int:
        return (date(self.year, self.month, self.day) - _FATSECRET_EPOCH).days


@dataclass(frozen=True, slots=True)
class FatRecord:
    date: FatDate
    calories: float
    carbs: float
    protein: float
    fat: float


def get_by_month(
    response_format: str = "json",
    on_date: FatDate | None = None,
    *,
    session: OAuth1Session | None = None,
) -> list[FatRecord]:
    """
    Fetches food records for the current month from the FatSecret API.

    Args:
        response_format (str): The format of the response, either 'json' or 'xml'.
        on_date (FatDate | None): A date in the month to retrieve.

    Returns:
        list[FatRecord]: A list of FatRecord instances representing the food entries for the month.
    """

    if response_format not in ("json", "xml"):
        raise ValueError("response_format must be 'json' or 'xml'")

    if session is not None:
        return _get_month(session, response_format, on_date or _today())
    with create_authenticated_session() as authenticated_session:
        return _get_month(
            authenticated_session,
            response_format,
            on_date or _today(),
        )


def get_all(
    response_format: str = "json",
    output_path: str | Path = _DEFAULT_OUTPUT_PATH,
) -> list[FatRecord]:
    """Fetch records back to 1970, appending JSON Lines and resuming from a checkpoint.

    The output is written to ``output_path`` and the checkpoint is stored alongside
    it. A completed output is returned as-is on later calls.
    """
    if response_format not in ("json", "xml"):
        raise ValueError("response_format must be 'json' or 'xml'")

    writer = FatSecretJsonlWriter(output_path)
    cursor = writer.get_next_month(response_format, _today())
    if cursor is None:
        return _stored_records_to_fatrecords(writer.records)

    with create_authenticated_session() as session:
        while cursor is not None:
            records = get_by_month(
                response_format,
                FatDate(cursor.year, cursor.month, cursor.day),
                session=session,
            )
            writer.write_records(records)
            cursor = _previous_month(cursor)
            writer.set_next_month(response_format, cursor)

    return _stored_records_to_fatrecords(writer.records)


def _stored_records_to_fatrecords(
    records: list[dict[str, Any]],
) -> list[FatRecord]:
    result: list[FatRecord] = []
    for record in records:
        record_date = record.get("date")
        if not isinstance(record_date, dict):
            raise ValueError("Stored FatSecret record must contain a date object")
        try:
            result.append(
                FatRecord(
                    date=FatDate(
                        year=int(record_date["year"]),
                        month=int(record_date["month"]),
                        day=int(record_date["day"]),
                    ),
                    calories=float(record["calories"]),
                    carbs=float(record["carbs"]),
                    protein=float(record["protein"]),
                    fat=float(record["fat"]),
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Stored FatSecret record has invalid fields") from error
    return result


def _today() -> date:
    return date.today()


def _get_month(
    session: OAuth1Session,
    response_format: str,
    on_date: date | FatDate,
) -> list[FatRecord]:
    if isinstance(on_date, FatDate):
        request_date = date(on_date.year, on_date.month, on_date.day)
    else:
        request_date = on_date

    response = session.get(
        _ENDPOINT,
        params={
            "date": (request_date - _FATSECRET_EPOCH).days,
            "format": response_format,
        },
        timeout=30,
    )
    response.raise_for_status()

    if response_format == "json":
        return _json_to_fatrecords(response.json())
    return _xml_to_fatrecords(response.content)


def _previous_month(cursor: date) -> date | None:
    previous_month = date(cursor.year, cursor.month, 1) - timedelta(days=1)
    if previous_month < _FATSECRET_EPOCH:
        return None
    return previous_month


def _json_to_fatrecords(payload: Any) -> list[FatRecord]:
    if not isinstance(payload, dict) or not isinstance(payload.get("month"), dict):
        raise ValueError("FatSecret response must contain a 'month' object")

    days = payload["month"].get("day", [])
    if days is None:
        return []
    if isinstance(days, dict):
        days = [days]
    if not isinstance(days, list) or not all(isinstance(day, dict) for day in days):
        raise ValueError("FatSecret response 'month.day' must be a list of objects")

    return [_json_to_fatrecord(day) for day in days]


def _xml_to_fatrecords(content: bytes) -> list[FatRecord]:
    root = ElementTree.fromstring(content)
    month = root if root.tag == "month" else root.find(".//month")
    if month is None:
        raise ValueError("FatSecret response must contain a 'month' element")

    days = [
        {child.tag: child.text for child in day}
        for day in month.findall("day")
    ]
    return [_json_to_fatrecord(day) for day in days]


def _json_to_fatrecord(json_data: dict[str, Any]) -> FatRecord:
    if "date_int" not in json_data:
        raise ValueError("FatSecret day is missing 'date_int'")

    try:
        day_date = _FATSECRET_EPOCH + timedelta(days=int(json_data["date_int"]))
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("FatSecret day has an invalid 'date_int'") from error

    return FatRecord(
        date=FatDate(day_date.year, day_date.month, day_date.day),
        calories=_number(json_data, "calories"),
        carbs=_number(json_data, "carbohydrate"),
        protein=_number(json_data, "protein"),
        fat=_number(json_data, "fat"),
    )


def _number(data: dict[str, Any], key: str) -> float:
    try:
        return float(data[key])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"FatSecret day has an invalid or missing '{key}'") from error


__all__ = ["FatDate", "FatRecord", "get_by_month", "get_all"]

if __name__ == "__main__":
    get_by_month()
