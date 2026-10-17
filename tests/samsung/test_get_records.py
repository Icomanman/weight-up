import pytest

from weight_up.samsung.get_records import _csv_to_records


def test_csv_to_records_collects_only_requested_columns(tmp_path):
    csv_path = tmp_path / "steps.csv"
    csv_path.write_text(
        "com.samsung.shealth.step_daily_trend,7006011,6\n"
        "count,calorie,day_time,unused\n"
        "100,4.5,2025-09-13 00:00:00.000,ignored\n"
        "200,8.0,2025-09-14 00:00:00.000,ignored\n",
        encoding="utf-8",
    )

    records = _csv_to_records(str(csv_path), ["count", "day_time"])

    assert records == {
        "count": ["100", "200"],
        "day_time": ["2025-09-13 00:00:00.000", "2025-09-14 00:00:00.000"],
    }


def test_csv_to_records_rejects_missing_target_header(tmp_path):
    csv_path = tmp_path / "steps.csv"
    csv_path.write_text(
        "com.samsung.shealth.step_daily_trend,7006011,6\n"
        "count,day_time\n"
        "100,2025-09-13 00:00:00.000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CSV is missing headers: calorie"):
        _csv_to_records(str(csv_path), ["count", "calorie"])
