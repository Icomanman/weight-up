
from dataclasses import dataclass


@dataclass
class Weight:
    value: float
    unit: str = "kg"
