"""This Module includes methods for communicating with a MilkMeter device through BLE."""
import asyncio
from queue import Empty

from ble_nordic import BLE
from asyncio import TimeoutError

import time

_connection_timeout = 10000


class BLEException(Exception):
    """Raised for all Exceptions caught within the class."""

    pass


class MMBleClient:
    """
    The client is programmed with two services for BLE communication, which are defined in the "services" attribute.

    Additionally, the client has a queue that is coded in the "output" attribute. Upon establishing a connection,
    notifications from both services will be directed to the output queue. This will continue to occur until the
    connection is ended.

    :param mac: the MAC Address of the MilkMeter Device.
    :param timeout: The duration in seconds the methods read and read_all waits for data when timeout=0
    the read will halt until data output. default 0.
    :log_file: the path for the log file. default 'MMBleClient.log'.
    """

    def __init__(self, mac: str, timeout: float = 0, log_file: str = "MMBleClient.log"):
        """Initialize MilkMeter device."""
        self.mac = mac
        self.timeout = int(timeout * 1000)
        ble = BLE(log_file, "COM5")
        self.output = ble.Queue().queue
        self.device = ble.Device(mac, ble.ble_adapter)
        self.services = {
            "MMP": [
                "10000000-1000-1000-8000-00805f9baaaa",
                "10000000-2000-1000-8000-00805f9baaaa",
            ],
            "BCP": [
                "40000000-1000-1000-8000-00805f9baaaa",
                "40000000-2000-1000-8000-00805f9baaaa",
            ],
        }
        self.device.device_services = self.services

    def start_notify(self):
        """Start listening for MMP and BCP services notifications."""
        self.device.start_notify(self.services["MMP"][1])
        self.device.start_notify(self.services["BCP"][1])

    def stop_notify(self):
        """Stop listening for MMP and BCP services notifications."""
        self.device.stop_notify(self.services["MMP"][1])
        self.device.stop_notify(self.services["BCP"][1])

    def connect(self):
        """
        Connect to ble device with current settings. This may throw an Exception.

        if it cannot be connected.
        On success registers for services notifications.
        """
        is_connected = self.device.connect(_connection_timeout)
        if is_connected:
            self.start_notify()
        return is_connected

    def close(self):
        """Terminate the connection."""
        try:
            self.device.stop_notify(self.services["MMP"][1])
            self.device.stop_notify(self.services["BCP"][1])
        except BLEException:
            pass
        if self.device.is_connected():
            return self.device.disconnect(_connection_timeout)
        else:
            return False

    async def async_read(self, n: int = 1) -> bytes:
        """Read size bytes from the ble device."""
        ret = bytearray()
        bdata = bytearray()
        data = b""
        start_time = time.time()
        remainder = n
        is_break = False

        try:
            while remainder > 0:
                if self.timeout <= 0:
                    data = await self.output.get()
                else:
                    etime = time.time()
                    etime = etime * 100000 - start_time * 100000
                    if etime <= self.timeout:
                        try:
                            data = self.output.get_nowait()
                            is_break = True
                        except Empty:
                            is_break = True
                    else:
                        try:
                            data = self.output.get_nowait()
                        except Empty:
                            is_break = True
                if len(data) > 0:
                    bdata = bytearray(data)
                    length = min([remainder, len(data)])
                    for i in range(length):
                        ret.append(bdata[0])
                        del bdata[0]
                    remainder -= length
                if is_break:
                    break
        except TimeoutError:
            # print("TIMEOUT")
            pass

        if len(bdata) > 0:
            new_queue = BLE.Queue().queue
            new_queue.put_nowait(bdata)
            while not self.output.empty():
                qdata = self.output.get_nowait()
                new_queue.put_nowait(qdata)
            self.output = new_queue
        return bytes(ret)

    def read(self, n: int = 1) -> bytes:
        """
        Read size bytes from the ble device.

        :param n: number of bytes to read. default: 1
        :return: the data that was read (bytes)
        """
        loop = asyncio.get_event_loop()
        ret = loop.run_until_complete(self.async_read(n))
        return ret

    async def async_read_all(self):
        """Read all the data stored in the output queue."""
        first = True
        ret = bytearray()
        try:
            while True:
                if first:
                    data = self.output.get_nowait()
                    print(data)
                    first = False
                    for b in data:
                        ret.append(b)
                else:
                    data = self.output.get_nowait()
                    for b in data:
                        ret.append(b)
        except asyncio.QueueEmpty:
            pass
        except TimeoutError:
            pass
        finally:
            return bytes(ret)

    def read_all(self):
        """
        Read all the data stored in the output queue.

        If there is data in the output queue it will fetch it.
            if not it will wait for data for the duration of the timeout.

        :return: All the data that was read (bytes)
        """
        loop = asyncio.get_event_loop()
        ret = loop.run_until_complete(self.async_read_all())
        return ret

    def write(self, data: bytes) -> int:
        """
        Write to the service write characteristic.

        :param data: the data to be written
        :return: the length of the data written
        """
        service = "MMP"
        if data[0:9] == b"\x04\x0f\x00\x0d\x60\x00\x00\x1f":
            service = "BCP"
        self.device.write(self.services[service][0], data, 5000)
        return len(data)
