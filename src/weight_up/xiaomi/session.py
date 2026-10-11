"""Small HTTP helpers shared by the Xiaomi login modules."""

import json
import random
import string
from typing import Any

import requests


def generate_user_agent() -> str:
    """Build a Mi Home style user agent, matching the reference extractor."""
    agent_id = "".join(random.choices("ABCDE", k=13))
    random_text = "".join(random.choices(string.ascii_lowercase, k=18))
    return f"{random_text}-{agent_id} APP/com.xiaomi.mihome APPV/10.5.201"


def form_headers(user_agent: str) -> dict[str, str]:
    return {
        "User-Agent": user_agent,
        "Content-Type": "application/x-www-form-urlencoded",
    }


def start_login_session() -> requests.Session:
    """Return a session carrying the device cookies Xiaomi expects at login."""
    session = requests.Session()
    device_id = "".join(random.choices(string.ascii_lowercase, k=6))
    for domain in ("mi.com", "xiaomi.com"):
        session.cookies.set("sdkVersion", "accountsdk-18.8.15", domain=domain)
        session.cookies.set("deviceId", device_id, domain=domain)
    return session


def parse_response(text: str) -> dict[str, Any]:
    """Parse Xiaomi JSON, which is prefixed with a '&&&START&&&' guard.

    Raises ValueError if the body is not a JSON object.
    """
    parsed = json.loads(text.replace("&&&START&&&", ""))
    if not isinstance(parsed, dict):
        raise ValueError("expected a JSON object")
    return parsed


def find_cookie(session: requests.Session, name: str) -> str | None:
    """Return the first non-empty cookie called name, whatever its domain.

    cookies.get() raises when several domains set the same name.
    """
    for cookie in session.cookies:
        if cookie.name == name and cookie.value:
            return cookie.value
    return None


def text_or_none(value: Any) -> str | None:
    return None if value is None else str(value)
