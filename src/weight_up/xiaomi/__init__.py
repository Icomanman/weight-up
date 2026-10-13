"""Xiaomi cloud access: login, signed API calls and scale weight history."""

from .api import fetch_weights
from .auth import login, login_with_token
from .models import (
    XiaomiApiError,
    XiaomiAuthError,
    XiaomiAuthResult,
    XiaomiError,
    XiaomiWeight,
)

__all__ = [
    "XiaomiApiError",
    "XiaomiAuthError",
    "XiaomiAuthResult",
    "XiaomiError",
    "XiaomiWeight",
    "fetch_weights",
    "login",
    "login_with_token",
]
