import json

from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


class FatSecretJsonlWriter:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.checkpoint_path = self.path.with_suffix(
            f"{self.path.suffix}.checkpoint.json"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = []
        self._dates: set[tuple[int, int, int]] = set()
        self._read_records()

    def get_next_month(self, response_format: str, initial_date: date) -> date | None:
        if not self.checkpoint_path.exists():
            self.set_next_month(response_format, initial_date)
            return initial_date

        checkpoint = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint["response_format"] != response_format:
            raise ValueError("Checkpoint response format does not match")
        value = checkpoint["next_month"]
        return date.fromisoformat(value) if value is not None else None

    def set_next_month(
        self,
        response_format: str,
        next_month: date | None,
    ) -> None:
        checkpoint = {
            "response_format": response_format,
            "next_month": next_month.isoformat() if next_month else None,
        }
        self.checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

    def write_records(self, records: Iterable[Any]) -> None:
        new_records = []
        for record in records:
            data = asdict(record) if is_dataclass(record) else record
            record_date = data["date"]
            key = (record_date["year"], record_date["month"], record_date["day"])
            if key not in self._dates:
                self._dates.add(key)
                new_records.append(data)

        with self.path.open("a", encoding="utf-8") as output:
            for record in new_records:
                output.write(json.dumps(record, separators=(",", ":")) + "\n")
            output.flush()
        self.records.extend(new_records)

    def _read_records(self) -> None:
        if not self.path.exists():
            return

        lines = self.path.read_bytes().splitlines(keepends=True)
        valid_size = 0
        truncated = False
        for index, line in enumerate(lines):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                if index == len(lines) - 1 and not line.endswith(b"\n"):
                    with self.path.open("r+b") as output:
                        output.truncate(valid_size)
                    truncated = True
                    break
                raise ValueError(f"Invalid JSON Lines record at line {index + 1}")

            self.records.append(record)
            record_date = record["date"]
            self._dates.add(
                (record_date["year"], record_date["month"], record_date["day"])
            )
            valid_size += len(line)

        if lines and not truncated and valid_size == self.path.stat().st_size:
            if not lines[-1].endswith(b"\n"):
                with self.path.open("ab") as output:
                    output.write(b"\n")


__all__ = ["FatSecretJsonlWriter"]
