import sys

sys.path.append("")

from micropython import const
import asyncio
import aioble
import aioble.security
import bluetooth
import struct

import machine

led = machine.Pin("LED", machine.Pin.OUT)

# HID Service
_HID_SERVICE_UUID = bluetooth.UUID(0x1812)
_HID_REPORT_UUID = bluetooth.UUID(0x2A4D)
_HID_REPORT_MAP_UUID = bluetooth.UUID(0x2A4B)
_HID_INFO_UUID = bluetooth.UUID(0x2A4A)
_HID_CONTROL_POINT_UUID = bluetooth.UUID(0x2A4C)

_APPEARANCE_HID_KEYBOARD = const(0x03C1)
_INTERVAL_MS = const(1000)

# Consumer Control HID report descriptor
_HID_REPORT_MAP = bytes(
    [
        0x05,
        0x0C,  # Usage Page (Consumer)
        0x09,
        0x01,  # Usage (Consumer Control)
        0xA1,
        0x01,  # Collection (Application)
        0x85,
        0x01,  #   Report ID (1)
        0x09,
        0xCD,  #   Usage (Play/Pause)
        0x15,
        0x00,  #   Logical Minimum (0)
        0x25,
        0x01,  #   Logical Maximum (1)
        0x75,
        0x01,  #   Report Size (1)
        0x95,
        0x01,  #   Report Count (1)
        0x81,
        0x06,  #   Input (Data, Variable, Relative)
        0x75,
        0x07,  #   Report Size (7) - padding
        0x95,
        0x01,  #   Report Count (1)
        0x81,
        0x03,  #   Input (Constant)
        0xC0,  # End Collection
    ]
)

service = aioble.Service(_HID_SERVICE_UUID)

report_map = aioble.Characteristic(service, _HID_REPORT_MAP_UUID, read=True)
hid_info = aioble.Characteristic(service, _HID_INFO_UUID, read=True)
control_pt = aioble.Characteristic(service, _HID_CONTROL_POINT_UUID, write=True)
hid_report = aioble.Characteristic(service, _HID_REPORT_UUID, read=True, notify=True)

_HID_REPORT_REF_UUID = bluetooth.UUID(0x2908)
report_ref = aioble.Descriptor(hid_report, _HID_REPORT_REF_UUID, read=True)
report_ref.write(struct.pack("<BB", 0x01, 0x01))  # Report ID 1, Input report

_HID_PROTOCOL_MODE_UUID = bluetooth.UUID(0x2A4E)
protocol_mode = aioble.Characteristic(
    service, _HID_PROTOCOL_MODE_UUID, read=True, write_no_response=True
)

aioble.register_services(service)

_ble = bluetooth.BLE()
_ble.active(True)


async def _patched_pair(connection, bond=False, mitm=False, io=2, timeout_ms=20000):
    _ble.config(addr_mode=0x00, le_secure=False)
    import asyncio

    connection._pair_event = asyncio.ThreadSafeFlag()
    _ble.gap_pair(connection._conn_handle)
    with connection.timeout(timeout_ms):
        await connection._pair_event.wait()


aioble.security.pair = _patched_pair

protocol_mode.write(struct.pack("<B", 0x01))
report_map.write(_HID_REPORT_MAP)
hid_info.write(
    struct.pack("<HBB", 0x0111, 0x00, 0x02)
)  # HID v1.11, not localized, remote wakeH


async def send_play(connection):
    if connection is None or not connection.is_connected():
        return
    await hid_report.notify(connection, struct.pack("<BB", 0x01, 0x01))


async def send_pause(connection):
    if connection is None or not connection.is_connected():
        return
    await hid_report.notify(connection, struct.pack("<BB", 0x01, 0x00))


async def main():
    while True:
        led.on()
        print("Advertising...")
        connection = await aioble.advertise(
            _INTERVAL_MS,
            name="Pico Remote",
            services=[_HID_SERVICE_UUID],
            appearance=_APPEARANCE_HID_KEYBOARD,
        )
        led.off()
        print("Connected:", connection)
        # try:
        await connection.pair()
        # except Exception as e:
        # print("Pairing failed:", e)
        # continue
        try:
            async with connection:
                while True:
                    await asyncio.sleep_ms(2000)  # replace with actual button input
                    await send_play(connection)
                    await asyncio.sleep_ms(2000)  # replace with actual button input
                    await send_pause(connection)
        except Exception as e:
            print("Connection error:", e)


asyncio.run(main())
