import os
from dataclasses import dataclass
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv()


@dataclass(slots=True)
class OauthFlow:
    session: OAuth1Session

    endpoint: str = os.getenv("AUTH_ENDPOINT").rstrip("/")
    request_token_resource: str = os.getenv(
        "REQUEST_TOKEN_RESOURCE"
    ).rstrip("/")
    authorisation_resource: str = os.getenv(
        "AUTHORISATION_RESOURCE"
    ).rstrip("/")
    access_token_resource: str = os.getenv(
        "ACCESS_TOKEN_RESOURCE"
    ).rstrip("/")

    _access_token: str | None = None
    _authorisation_url: str | None = None
    _request_token: str | None = None
    _request_token_secret: str | None = None
    _unauthorised: bool = False

    def __post_init__(self):
        if self._authorisation_url is None:
            self._get_request_token()
            self._authorise_request_token()

    @property
    def authorisation_url(self) -> str | None:
        return self._authorisation_url

    def _get_request_token(self):
        _request_url: str = f"https://{self.endpoint}/{self.request_token_resource}"
        token_data: dict[str, str] = self.session.fetch_request_token(
            _request_url
        )
        self._request_token = token_data["oauth_token"]
        self._request_token_secret = token_data["oauth_token_secret"]

    def _authorise_request_token(self) -> None:
        _request_url: str = f"https://{self.endpoint}/{self.authorisation_resource}"
        self._authorisation_url = self.session.authorization_url(
            url=_request_url,
            request_token=self._request_token,
        )

    def get_access_token(self, oauth_verifier: dict[str, str]):
        request_url: str = f"https://{self.endpoint}/{self.access_token_resource}"
        access_token: dict[str, str] = self.session.fetch_access_token(
            url=request_url,
            verifier=oauth_verifier["oauth_verifier"],
        )
        return access_token


def auth() -> str:
    session: OAuth1Session = OAuth1Session(
        client_key=os.environ["CONSUMER_KEY"],
        client_secret=os.environ["CONSUMER_SECRET"],
        callback_uri="oob",
        signature_type="BODY",
    )
    oauth_flow: OauthFlow = OauthFlow(session=session)
    # Get Access Token
    access_token: dict[str, str] = oauth_flow.get_access_token(
        oauth_verifier={"oauth_verifier": input(
            f"Enter the verifier for {oauth_flow.authorisation_url}: ")}
    )
    session.close()
    print(f"Access Token: {access_token}")
    return access_token


if __name__ == "__main__":
    auth()


__all__ = ["auth"]
