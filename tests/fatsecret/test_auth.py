from urllib.parse import parse_qs, urlsplit

import requests

from weight_up.fatsecret import auth


def test_create_authenticated_session_uses_access_credentials_and_query_signing(
    monkeypatch,
):
    expected = {
        "CONSUMER_KEY": "consumer-key",
        "CONSUMER_SECRET": "consumer-secret",
        "FAT_ACCESS_TOKEN": "access-token",
        "FAT_ACCESS_TOKEN_SECRET": "access-token-secret",
    }
    for name, value in expected.items():
        monkeypatch.setenv(name, value)

    captured = {}

    def fake_oauth1_session(**kwargs):
        captured.update(kwargs)
        return captured

    monkeypatch.setattr(auth, "OAuth1Session", fake_oauth1_session)

    assert auth.create_authenticated_session() is captured
    assert captured == {
        "client_key": "consumer-key",
        "client_secret": "consumer-secret",
        "resource_owner_key": "access-token",
        "resource_owner_secret": "access-token-secret",
        "signature_method": "HMAC-SHA1",
        "signature_type": "QUERY",
    }


def test_authenticated_session_signs_the_get_query(monkeypatch):
    monkeypatch.setenv("CONSUMER_KEY", "consumer-key")
    monkeypatch.setenv("CONSUMER_SECRET", "consumer-secret")
    monkeypatch.setenv("FAT_ACCESS_TOKEN", "access-token")
    monkeypatch.setenv("FAT_ACCESS_TOKEN_SECRET", "access-token-secret")

    session = auth.create_authenticated_session()
    try:
        request = session.prepare_request(requests.Request(
            "GET",
            "https://platform.fatsecret.com/rest/food-entries/month/v1",
            params={"format": "json"},
        ))
    finally:
        session.close()

    query = parse_qs(urlsplit(request.url).query)
    assert query["format"] == ["json"]
    assert query["oauth_consumer_key"] == ["consumer-key"]
    assert query["oauth_token"] == ["access-token"]
    assert query["oauth_signature_method"] == ["HMAC-SHA1"]
    assert query["oauth_version"] == ["1.0"]
    assert query["oauth_timestamp"]
    assert query["oauth_nonce"]
    assert query["oauth_signature"]
