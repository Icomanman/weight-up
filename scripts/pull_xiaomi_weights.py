import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

from weight_up.xiaomi import XiaomiError, XiaomiScaleClient, login_with_token
from weight_up.xiaomi.constants import SCALE_REGIONS

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Xiaomi scale weight history as JSON."
    )
    parser.add_argument(
        "--region",
        choices=SCALE_REGIONS,
        default="sg",
        help="Xiaomi account region (default: sg)",
    )
    parser.add_argument(
        "--model",
        help="Scale model, e.g. yunmai.scales.ms104 (default: XIAOMI_SCALE_MODEL in .env)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/xiaomi_weights.json"),
        help="Output JSON path (default: data/xiaomi_weights.json)",
    )
    args = parser.parse_args()

    if args.output.exists():
        parser.error(
            f"output already exists; refusing to overwrite: {args.output}")

    settings = dotenv_values(ENV_PATH)
    user_id = settings.get("XIAOMI_USER_ID")
    pass_token = settings.get("XIAOMI_PASS_TOKEN")
    model = args.model or settings.get("XIAOMI_SCALE_MODEL")
    if not user_id or not pass_token or not model:
        parser.error(
            "set XIAOMI_USER_ID and XIAOMI_PASS_TOKEN in the repository .env "
            "file, and XIAOMI_SCALE_MODEL there or pass --model; obtain the "
            "token with: python -m weight_up.xiaomi EMAIL --show-pass-token"
        )

    try:
        auth_result = login_with_token(user_id, pass_token)
        weights = XiaomiScaleClient(auth_result, args.region, model).get_weights()
    except XiaomiError as error:
        parser.exit(1, f"Xiaomi request failed: {error}\n")

    records = []
    for weight in weights:
        record = asdict(weight)
        record["date"] = weight.date.isoformat() if weight.date else None
        records.append(record)

    document = {
        "source": "xiaomi_home_scale",
        "region": args.region,
        "model": model,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output_file:
        json.dump(document, output_file, indent=2)
        output_file.write("\n")

    print(f"Saved {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
