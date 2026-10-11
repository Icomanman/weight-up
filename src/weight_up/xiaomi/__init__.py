"""Xiaomi cloud access: login, signed API calls and scale weight history."""

from .auth import login, login_with_token
from .client import XiaomiScaleClient
from .errors import XiaomiApiError, XiaomiAuthError, XiaomiError
from .models import XiaomiAuthResult, XiaomiWeight

__all__ = [
    "XiaomiApiError",
    "XiaomiAuthError",
    "XiaomiAuthResult",
    "XiaomiError",
    "XiaomiScaleClient",
    "XiaomiWeight",
    "login",
    "login_with_token",
]
