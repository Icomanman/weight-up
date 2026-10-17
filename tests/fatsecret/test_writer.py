import json
from datetime import date

import pytest

from weight_up.fatsecret.get_records import FatDate, FatRecord
from weight_up.fatsecret.writer import FatSecretJsonlWriter


def record(day):
    return FatRecord(
        date=FatDate(1970, 1, day),
        calories=100.0,
        carbs=20.0,
        protein=30.0,
        fat=40.0,
    )


def test_writer_appends_json_lines_and_skips_duplicate_dates(tmp_path):
    output_path = tmp_path / "records.jsonl"

    writer = FatSecretJsonlWriter(output_path)
    writer.write_records([record(1), record(2)])
    writer.write_records([record(2), record(3)])

    lines = output_path.read_text().splitlines()
    assert [json.loads(line)["date"]["day"] for line in lines] == [1, 2, 3]

    assert len(FatSecretJsonlWriter(output_path).records) == 3


def test_writer_truncates_only_an_incomplete_final_json_line(tmp_path):
    output_path = tmp_path / "records.jsonl"
    FatSecretJsonlWriter(output_path).write_records([record(1)])

    with output_path.open("ab") as output_file:
        output_file.write(b'{"date":')

    writer = FatSecretJsonlWriter(output_path)
    assert len(writer.records) == 1
    writer.write_records([record(2)])

    assert len(output_path.read_text().splitlines()) == 2


def test_writer_rejects_invalid_json_lines(tmp_path):
    output_path = tmp_path / "records.jsonl"
    output_path.write_text("{invalid}\n")

    with pytest.raises(ValueError, match="line 1"):
        FatSecretJsonlWriter(output_path)


def test_writer_persists_and_validates_the_month_checkpoint(tmp_path):
    output_path = tmp_path / "records.jsonl"
    writer = FatSecretJsonlWriter(output_path)
    assert writer.get_next_month("json", date(2024, 5, 8)) == date(2024, 5, 8)
    writer.set_next_month("json", date(2024, 4, 30))

    writer = FatSecretJsonlWriter(output_path)
    assert writer.get_next_month("json", date(2025, 1, 1)) == date(2024, 4, 30)
    with pytest.raises(ValueError, match="format does not match"):
        writer.get_next_month("xml", date(2025, 1, 1))
