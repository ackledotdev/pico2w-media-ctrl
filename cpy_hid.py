import time

import _bleio
import wifi
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.device_info import DeviceInfoService
from adafruit_ble.services.standard.hid import HIDService
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

print(_bleio.adapter)

ble = BLERadio()
hid = HIDService()
device_info = DeviceInfoService(software_revision="1.0", manufacturer="Pico")
advertisement = ProvideServicesAdvertisement(hid)
advertisement.appearance = 961  # HID keyboard

cc = ConsumerControl(hid.devices)

ble.start_advertising(advertisement)
print("Advertising...")

while True:
    while not ble.connected:
        pass
    print("Connected")
    while ble.connected:
        cc.send(ConsumerControlCode.PLAY_PAUSE)
        time.sleep(2)
    ble.start_advertising(advertisement)
