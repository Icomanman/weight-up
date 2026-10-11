"""Exceptions raised by the Xiaomi cloud modules."""


class XiaomiError(Exception):
    """Base class for every Xiaomi cloud failure."""


class XiaomiAuthError(XiaomiError):
    """Login failed; the message names the step and what Xiaomi returned."""


class XiaomiApiError(XiaomiError):
    """A signed API call failed or its reply could not be decrypted."""
