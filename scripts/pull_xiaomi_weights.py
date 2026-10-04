import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

from weight_up.xiaomi.client import Client


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Xiaomi Mi Fitness weight history as JSON."
    )
    parser.add_argument(
        "--region",
        choices=("cn", "de", "i2", "ru", "sg", "us"),
        default="sg",
        help="Xiaomi account region (default: sg)",
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

    env_path = Path(__file__).resolve().parents[1] / ".env"
    credentials = dotenv_values(env_path)
    username = credentials.get("xiaomi_user")
    password = credentials.get("xiaomi_password")
    if not username or not password:
        parser.error(
            "set xiaomi_user and xiaomi_password in the repository .env file"
        )

    client = Client()
    try:
        client.login(username, password)
        weights = client.get_filter_weights(args.region)
    finally:
        client.close()

    records = []
    for weight in weights:
        record = asdict(weight)
        record["date"] = weight.date.isoformat() if weight.date else None
        records.append(record)

    document = {
        "source": "xiaomi_mi_fitness",
        "region": args.region,
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
