import asyncio
from weight_up.scale import connect_to_scale, scan_for_scales, BleakClient


def main() -> None:
    scales = asyncio.run(scan_for_scales())
    bt_client: BleakClient = connect_to_scale(scales[0].address)
    print(bt_client)
    bt_client.close()


if __name__ == "__main__":
    main()
