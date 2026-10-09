import json
import os

from dataclasses import dataclass
from http import HTTPResponse, HTTPRequest, HTTPStatus
from dotenv import load_dotenv
load_dotenv()


@dataclass(frozen=True, slots=True)
class FatDate:
    """
    Default values are based on FatSecret's base date: 01 January 1970
    """
    year: int = 1970
    month: int = 1
    day: int = 1

    def resolve(self) -> int:
        return (self.year - 1970) * 365 + (self.month - 1) * 30 + (self.day - 1)


@dataclass(frozen=True, slots=True)
class FatRecord:
    date: FatDate
    calories: int
    carbs: int
    protein: int
    fat: int


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

    _endpoint: str = f"https://platform.fatsecret.com/rest/food-entries/month/v1?format={response_format}"
    # Assemble the GET request using OAuth1 credentials

    # Process the response and convert it into a list of FatRecord instances
    # Loop through each json entry
    # return the list of FatRecord instances


def _json_to_fatrecord(json_data: dict) -> FatRecord:
    date = FatDate(
        year=json_data.get("year", 1970),
        month=json_data.get("month", 1),
        day=json_data.get("day", 1)
    )
    return FatRecord(
        date=date,
        calories=json_data.get("calories", 0),
        carbs=json_data.get("carbs", 0),
        protein=json_data.get("protein", 0),
        fat=json_data.get("fat", 0)
    )


__all__ = ["FatDate", "FatRecord", "get_by_month"]

if __name__ == "__main__":
    get_by_month()
