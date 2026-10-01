
from bleak import BleakClient, BleakScanner
from bleak import BLEDevice


async def scan_for_scales():
    devices: list[BLEDevice] = await BleakScanner.discover()
    print(devices)
    scales: list[BLEDevice] = [
        device for device in devices if "scale" in device.name.lower()
    ]
    return scales

if __name__ == "__main__":
    import asyncio

    async def main():
        scales = await scan_for_scales()
        for scale in scales:
            print(scale)

    asyncio.run(main())
