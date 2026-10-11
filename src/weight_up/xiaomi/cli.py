"""Command-line front end for the Xiaomi cloud login and scale fetch.

This is the only module that prompts, prints or writes captcha files.
Run with: python -m weight_up.xiaomi EMAIL -r sg
"""

import argparse
import getpass
import logging
import os
import time
from pathlib import Path

from .auth import login, login_with_token
from .cloud_api import api_host, verify_tokens
from .constants import API_REGIONS
from .errors import XiaomiError
from .models import XiaomiAuthResult
from .scale import fetch_scale_records
from .weights import parse_scale_records

CAPTCHA_DIR = Path(__file__).resolve().parent / "captcha"
PASS_TOKEN_ENV_VAR = "XIAOMI_PASS_TOKEN"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    try:
        auth_result = _log_in(args)
        _print_credentials(auth_result, args.show_pass_token)
        verify_tokens(auth_result, args.region)
        print(f"verification:  PASS - {api_host(args.region)} accepted the tokens")
        if args.model:
            _print_scale_summary(auth_result, args.region, args.model)
    except XiaomiError as error:
        print(f"FAIL - {error}")
        return 1
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Xiaomi cloud login.")
    parser.add_argument(
        "email", nargs="?", help="account email; omit when using --user-id")
    parser.add_argument("-p", "--password", help="prompted for if omitted")
    parser.add_argument(
        "--user-id",
        help="log in with a saved passToken instead of email and password; "
        f"the token is read from {PASS_TOKEN_ENV_VAR} or prompted for")
    parser.add_argument(
        "-r", "--region", choices=API_REGIONS, default="sg",
        help="API region used for verification and data (default: sg)")
    parser.add_argument(
        "--model", help="scale model; also fetches and parses scale records")
    parser.add_argument(
        "--show-pass-token", action="store_true",
        help="print the full passToken so it can be saved (treat as a password)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    if bool(args.email) == bool(args.user_id):
        parser.error("give either an email or --user-id")
    return args


def _log_in(args: argparse.Namespace) -> XiaomiAuthResult:
    if args.user_id:
        pass_token = (
            os.environ.get(PASS_TOKEN_ENV_VAR) or getpass.getpass("passToken: "))
        return login_with_token(args.user_id, pass_token)
    password = args.password or getpass.getpass("Password: ")
    return login(
        args.email,
        password,
        code_provider=lambda: input("Email 2FA code: "),
        captcha_provider=_prompt_captcha,
    )


def _prompt_captcha(image: bytes) -> str:
    CAPTCHA_DIR.mkdir(exist_ok=True)
    image_path = CAPTCHA_DIR / f"captcha_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
    image_path.write_bytes(image)
    print(f"Captcha image saved at: {image_path}")
    return input("Captcha text (case-sensitive): ")


def _mask(value: str | None) -> str:
    if not value:
        return "<missing>"
    return f"{value[:4]}... ({len(value)} chars)"


def _print_credentials(auth_result: XiaomiAuthResult, show_pass_token: bool) -> None:
    print(f"ssecurity:     {_mask(auth_result.ssecurity)}")
    print(f"service_token: {_mask(auth_result.service_token)}")
    print(f"user_id:       {auth_result.user_id}")
    print(f"c_user_id:     {auth_result.c_user_id}")
    print(f"pass_token:    {_mask(auth_result.pass_token)}")
    if show_pass_token and auth_result.pass_token:
        print(f"pass_token (full): {auth_result.pass_token}")


def _print_scale_summary(
    auth_result: XiaomiAuthResult, region: str, model: str
) -> None:
    """Print counts and the date range only, never the measurements."""
    records = fetch_scale_records(auth_result, region, model)
    unique_times = {record.get("createTime") for record in records}
    weights = parse_scale_records(records)
    print(f"scale records: {len(records)} (unique createTime: {len(unique_times)})")
    print(f"parsed weights: {len(weights)}")
    dates = [weight.date for weight in weights if weight.date]
    if dates:
        print(f"date range:    {min(dates):%Y-%m-%d} to {max(dates):%Y-%m-%d} (UTC)")
