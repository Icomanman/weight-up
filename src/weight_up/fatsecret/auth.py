import os
from dataclasses import dataclass
from dotenv import load_dotenv
from http.client import HTTPConnection, HTTPResponse

load_dotenv()


@dataclass
class DevAccount:
    api_key: str
    api_secret: str


def _request_token(connection: HTTPConnection) -> None:
    resource: str = os.getenv("TOKEN_RESOURCE")
    consumer_key: str = os.getenv("CONSUMER_KEY")
    sign_method: str = "HMAC-SHA1"
    connection.request(
        "POST",
        f"{resource}??oauth_consumer_key={consumer_key}"
    )
    response: HTTPResponse = connection.getresponse()
    print(response.status, response.reason)


def _authorise_on_behalf(connection: HTTPConnection) -> None:
    pass


def _get_access_token(connection: HTTPConnection) -> str:
    return ""


def auth() -> None:
    auth_endpoint: str = os.getenv("AUTH_ENDPOINT")
    connection: HTTPConnection = HTTPConnection(host=auth_endpoint)

    # request token
    _request_token(connection)

    # authorise on behalf of the user

    # access token

    connection.close()


if __name__ == "__main__":
    auth()

__all__ = ["DevAccount", "auth"]
