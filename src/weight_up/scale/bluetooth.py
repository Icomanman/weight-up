
from bleak import BleakClient, BleakScanner
from bleak import BLEDevice


def on_disconnect(client: BleakClient) -> None:
    raise ConnectionError(f"> Client {client} disconnected unexpectedly.")


async def scan_for_scales() -> list[BLEDevice]:
    devices: list[BLEDevice] = await BleakScanner.discover()
    scales: list[BLEDevice] = [
        device for device in devices if device.name is not None and "scale" in device.name.lower()
    ]
    return scales


async def connect_to_scale(address: str) -> BleakClient:
    client: BleakClient = BleakClient(
        address_or_ble_device=address,
        disconnected_callback=on_disconnect
    )
    return client


if __name__ == "__main__":
    import asyncio

    async def main():
        scales = await scan_for_scales()
        for scale in scales:
            print(scale)

    asyncio.run(main())

__all__ = ["connect_to_scale", "scan_for_scales", "BleakClient"]
