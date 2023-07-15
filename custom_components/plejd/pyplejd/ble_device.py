"""
Wrapper class for BLEDevice with RSSI from AdvertisementData.
"""

from bleak.backends.device import BLEDevice

class BLEDeviceWithRssi:
    def __init__(self, device: BLEDevice, rssi: int):
        self.device = device
        self.rssi = rssi

    def __str__(self):
        return self.device.__str__()

    def __repr__(self):
        return self.device.__repr__()

    def __eq__(self, other):
        if isinstance(other, BLEDeviceWithRssi):
            return self.device == other.device
        return False
