import os
from dataclasses import dataclass
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv()


@dataclass
class RequestToken:
    token: str
    token_secret: str


def _request_token(oauth_session: OAuth1Session) -> RequestToken:
    auth_endpoint: str = os.environ["AUTH_ENDPOINT"].rstrip("/")
    token_resource: str = os.environ["TOKEN_RESOURCE"].lstrip("/")
    request_token_url = f"https://{auth_endpoint}/{token_resource}"
    token_data: dict[str, str] = oauth_session.fetch_request_token(
        request_token_url
    )
    return RequestToken(
        token=token_data["oauth_token"],
        token_secret=token_data["oauth_token_secret"],
    )


def _authorise_on_behalf(oauth_session: OAuth1Session) -> None:
    pass


def _get_access_token(oauth_session: OAuth1Session) -> str:
    return ""


def auth() -> dict[str, str]:
    session: OAuth1Session = OAuth1Session(
        client_key=os.environ["CONSUMER_KEY"],
        client_secret=os.environ["CONSUMER_SECRET"],
        callback_uri="oob",
        signature_type="BODY",
    )
    # Request Token
    _request_token(session)
    # Authorise on behalf

    # Get Access Token

    session.close()


if __name__ == "__main__":
    auth()


__all__ = ["RequestToken", "auth"]
