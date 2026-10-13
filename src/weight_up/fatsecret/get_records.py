from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from xml.etree import ElementTree

from .auth import create_authenticated_session


_FATSECRET_EPOCH = date(1970, 1, 1)
_ENDPOINT = "https://platform.fatsecret.com/rest/food-entries/month/v1"


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


def get_by_month(response_format: str = "json") -> list[FatRecord]:
    """
    Fetches food records for the current month from the FatSecret API.

    Args:
        response_format (str): The format of the response, either 'json' or 'xml'.

    Returns:
        list[FatRecord]: A list of FatRecord instances representing the food entries for the month.
    """

    if response_format not in ("json", "xml"):
        raise ValueError("response_format must be 'json' or 'xml'")

    with create_authenticated_session() as session:
        response = session.get(
            _ENDPOINT,
            params={"format": response_format},
        )
        response.raise_for_status()

        if response_format == "json":
            return _json_to_fatrecords(response.json())
        return _xml_to_fatrecords(response.content)


def get_all(response_format: str = "json") -> list[FatRecord]:
    pass


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


__all__ = ["FatDate", "FatRecord", "get_by_month"]

if __name__ == "__main__":
    get_by_month()
