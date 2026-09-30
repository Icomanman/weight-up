import os
from dataclasses import dataclass
from dotenv import load_dotenv
from http.client import HTTPConnection, HTTPResponse

load_dotenv()


@dataclass
class DevAccount:
    api_key: str
    api_secret: str


def authorise_on_behalf() -> None:
    auth_endpoint: str = os.getenv("AUTH_ENDPOINT")
    resource: str = os.getenv("AUTH_RESOURCE")
    connection: HTTPConnection = HTTPConnection(host=auth_endpoint)
    connection.request("GET", f"{auth_endpoint}/{resource}")
    response: HTTPResponse = connection.getresponse()
    print(response.status, response.reason)


if __name__ == "__main__":
    authorise_on_behalf()

__all__ = ["DevAccount", "authorise_on_behalf"]
