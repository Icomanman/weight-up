"""Thin client: fetch and parse one scale model's weight history."""

import requests

from .models import XiaomiAuthResult, XiaomiWeight
from .scale import fetch_scale_records, validate_scale_request
from .weights import parse_scale_records


class XiaomiScaleClient:
    """Weight history for one scale model, using existing credentials.

    Obtain auth_result from auth.login or auth.login_with_token. Region and
    model are validated on construction so a bad setting fails before any
    request is made.
    """

    def __init__(
        self,
        auth_result: XiaomiAuthResult,
        region: str,
        model: str,
        session: requests.Session | None = None,
    ) -> None:
        validate_scale_request(auth_result, region, model)
        self._auth_result = auth_result
        self._region = region
        self._model = model
        self._session = session

    def get_weights(self) -> list[XiaomiWeight]:
        """Return every weigh-in Xiaomi holds for the model, newest first."""
        records = fetch_scale_records(
            self._auth_result, self._region, self._model, session=self._session)
        return parse_scale_records(records)
