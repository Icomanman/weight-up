import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv()


def _required_environment_variable(name: str) -> str:
    value: str | None = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {name}")
    return value


@dataclass(slots=True)
class OauthFlow:
    session: OAuth1Session

    endpoint: str = field(init=False)
    request_token_resource: str = field(init=False)
    authorisation_resource: str = field(init=False)
    access_token_resource: str = field(init=False)

    _access_token: str | None = None
    _authorisation_url: str | None = None
    _request_token: str | None = None
    _request_token_secret: str | None = None
    _unauthorised: bool = False

    def __post_init__(self):
        self.endpoint = _required_environment_variable(
            "AUTH_ENDPOINT").rstrip("/")
        self.request_token_resource = _required_environment_variable(
            "REQUEST_TOKEN_RESOURCE"
        ).rstrip("/")
        self.authorisation_resource = _required_environment_variable(
            "AUTHORISATION_RESOURCE"
        ).rstrip("/")
        self.access_token_resource = _required_environment_variable(
            "ACCESS_TOKEN_RESOURCE"
        ).rstrip("/")

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

    def get_access_token(self, oauth_verifier: dict[str, str]) -> dict[str, str]:
        request_url: str = f"https://{self.endpoint}/{self.access_token_resource}"
        access_token: dict[str, str] = self.session.fetch_access_token(
            url=request_url,
            verifier=oauth_verifier["oauth_verifier"],
        )
        return access_token


def auth() -> dict[str, str]:
    session: OAuth1Session = OAuth1Session(
        client_key=os.environ["CONSUMER_KEY"],
        client_secret=os.environ["CONSUMER_SECRET"],
        callback_uri="oob",
        signature_type="BODY",
    )
    oauth_flow: OauthFlow = OauthFlow(session=session)
    # Get Access Token
    access_token: dict[str, str] = oauth_flow.get_access_token(
        oauth_verifier={
            "oauth_verifier": input(
                f"Enter the verifier for {oauth_flow.authorisation_url}: ")
        }
    )
    session.close()
    return access_token


if __name__ == "__main__":
    print(auth())


__all__ = ["auth"]
