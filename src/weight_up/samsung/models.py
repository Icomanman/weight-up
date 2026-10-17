
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class SamsungDate:
    year: int
    month: int
    day: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StepRecord:
    count: int
    calories: int
    date: SamsungDate

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "calories": self.calories,
            "date": self.date.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class WorkRecord:
    calories: int
    duration: str
    date: SamsungDate

    def to_dict(self) -> dict:
        return {
            "calories": self.calories,
            "duration": self.duration,
            "date": self.date.to_dict(),
        }


__all__ = ["SamsungDate", "StepRecord", "WorkRecord"]
