"""Immutable data shared across the Xiaomi cloud modules."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class XiaomiAuthResult:
    """Credentials for signed Xiaomi cloud calls.

    ssecurity is the base64 session key used to sign and encrypt requests.
    service_token identifies the session to the API host. pass_token can
    re-issue both without a 2FA code. Secrets are hidden from repr so the
    object is safe to log.
    """

    ssecurity: str = field(repr=False)
    service_token: str = field(repr=False)
    user_id: str | None
    c_user_id: str | None
    pass_token: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class XiaomiWeight:
    """One weigh-in reported by a Xiaomi scale.

    date is timezone-aware UTC. weight is in kilograms (the C# reference
    client names it WeightKg). The other measurements are passed through as
    Xiaomi reports them; their units are not yet verified. Missing values
    are 0 or an empty string.
    """

    date: datetime | None = None
    weight: float = 0.0
    bmi: float = 0.0
    body_fat: float = 0.0
    body_water: float = 0.0
    bone_mass: float = 0.0
    metabolic_age: int = 0
    muscle_mass: float = 0.0
    physique_rating: int = 0
    protein_mass: float = 0.0
    visceral_fat: int = 0
    basal_metabolism: int = 0
    body_score: int = 0
    heart_rate: int = 0
    height: float = 0.0
    skeletal_muscle_mass: float = 0.0
    user: str = ""
    source: str = ""
