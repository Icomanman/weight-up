
import csv
import json
import sys
from weight_up.samsung.models import SamsungDate, StepRecord, WorkRecord

_DATA_SOURCE_PATH: str = ""

_STEP_HEADERS: list[str] = ["count", "calorie", "day_time"]
_WORKOUT_HEADERS: list[str] = [
    "com.samsung.health.exercise.calorie",
    "com.samsung.health.exercise.duration",
    "com.samsung.health.exercise.start_time",
]


def _csv_to_records(
    file_path: str, target_headers: list[str]
) -> dict[str, list[str]]:
    records = {header: [] for header in target_headers}

    with open(file_path, newline="", encoding="utf-8-sig") as csvfile:
        preamble = next(csv.reader(csvfile), None)
        if (
            not preamble
            or not preamble[0].startswith("com.samsung.shealth.")
        ):
            raise ValueError("CSV is missing the Samsung Health metadata row")

        reader = csv.DictReader(csvfile)
        missing_headers = set(target_headers) - set(reader.fieldnames or [])
        if missing_headers:
            raise ValueError(
                f"CSV is missing headers: {', '.join(sorted(missing_headers))}"
            )

        for row_number, row in enumerate(reader, start=1):
            for header in target_headers:
                value = row.get(header)
                if value is None:
                    raise ValueError(
                        f"CSV data row {row_number} is missing a value for {header!r}"
                    )
                records[header].append(value)

    return records


def get_steps(file_path: str = _DATA_SOURCE_PATH) -> list[StepRecord]:
    records: dict[str, list[str]] = _csv_to_records(file_path, _STEP_HEADERS)
    print(records)
    return []


def get_workouts(file_path: str = _DATA_SOURCE_PATH) -> list[WorkRecord]:
    records: dict[str, list[str]] = _csv_to_records(
        file_path, _WORKOUT_HEADERS)
    print(records)
    return []


def get_all(file_path: str = _DATA_SOURCE_PATH) -> dict[str, list]:
    return {
        "steps": get_steps(file_path),
        "workouts": get_workouts(file_path),
    }


def write_to_json(data: dict[str, list], file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_records.py <source_path>")
        sys.exit(1)

    src_path: str = sys.argv[1]
    get_all(src_path)
