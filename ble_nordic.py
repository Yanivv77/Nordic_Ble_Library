"""interface to interact with a Bluetooth Low Energy (BLE) adapter."""

from util import setup_adapter, int_list_to_hex_string
from pc_ble_driver_py.observers import BLEAdapterObserver, BLEDriverObserver
from queue import Queue, Empty
from device import Device
import logging
from pc_ble_driver_py.ble_driver import BLEGapScanParams

logger = logging.getLogger(__name__)


class BLE(BLEDriverObserver):
    """
    This class provides an interface to interact with a Bluetooth Low Energy (BLE) adapter.

    :param log_file_path: the path to the log file.
    :param port: the serial port to which the BLE adapter is connected.

    :raises ValueError: if the inputted port is not a string or is not a valid serial port.

    :ivar ble_adapter: the BLE adapter instance.
    :ivar conn_q: the connection queue for handling connection events.
    :ivar Device: the Device class for creating BLE devices.
    :ivar Devices: a list of the BLE devices discovered.
    :ivar connect_with: the BLE device to connect with.
    :ivar found_devices: a list of the found BLE devices.
    :ivar mac_address_to_connect: the MAC address of the BLE device to connect to.
    :ivar conn_handler: the connection handler for handling connection events.
    """

    ble_adapter = None
    log_file_path = None

    def __init__(self, log_file_path="ble.log", port=None):
        """Initialize the BLE adapter and set up the necessary variables and observers."""
        if not isinstance(port, str) or not port.lower().startswith("com"):
            raise ValueError("Add valid connection port.")

        self.log_file = log_file_path
        logging.basicConfig(
            filename=self.log_file, format="%(asctime)s %(message)s", level=logging.INFO
        )
        BLE.ble_adapter = setup_adapter(
            port=port,
            auto_flash=False,
            baud_rate=1000000,
            retransmission_interval=300,
            response_timeout=1500,
            driver_log_level="fatal",
        )
        self.conn_q = Queue()
        self.Device = Device
        self.Devices = []
        self.connect_with = ""
        self.found_devices = []
        self.mac_address_to_connect = ""
        self.conn_handler = None


    def scan_by_mac(self, mac_addresses_connect_with: list, timeout_in_millis: int):
        """
        Scan for devices with the given MAC addresses and retrieve their metadata.

        :param mac_addresses_connect_with: A list of strings representing the MAC addresses of the devices to search for.
        :param timeout_in_millis: An integer representing the maximum amount of time to search for devices, in milliseconds.
        :return: A list of tuples, where each tuple contains a string representing the address of a device and
                 a dictionary representing the metadata associated with that device.
        """
        timeout_in_secs = timeout_in_millis / 1000
        logging.info(f"Scanning for {mac_addresses_connect_with}")
        for address in mac_addresses_connect_with:
            if self.ble_adapter:
                self.ble_adapter.driver.observer_register(self)
                self.mac_address_to_connect = address

                params = BLEGapScanParams(interval_ms=500, window_ms=500, timeout_s=20)
                self.ble_adapter.driver.ble_gap_scan_start(scan_params=params)
                try:
                    self.conn_handler = self.conn_q.get(timeout=timeout_in_secs)
                    self.ble_adapter.service_discovery(self.conn_handler)

                except Empty:
                    logging.info("Scan done")

                if self.conn_handler is not None:
                    self.ble_adapter.disconnect(self.conn_handler)

                if not self.found_devices:
                    logging.info("No devices found")

        return self.found_devices

    def on_gap_evt_adv_report(
        self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data
    ):
        """
        Event that is called when a Bluetooth Low Energy advertising packet is received.

        :param ble_driver: A BLEDriver object.
        :param conn_handle: An integer representing the connection handle.
        :param peer_addr: A BLEGapAddr object representing the address of the device sending the advertising packet.
        :param rssi: An integer representing the received signal strength indicator (RSSI) in dBm.
        :param adv_type: An integer representing the type of the advertising packet.
        :param adv_data: A bytes object representing the data in the advertising packet.
        """
        address_string = ":".join(f"{b:02X}" for b in peer_addr.addr)
        metadata = {
            "peer_addr": address_string,
            "rssi": rssi,
            "adv_type": adv_type,
            "adv_data": adv_data,
            "conn_handle": conn_handle,
        }

        if address_string == self.mac_address_to_connect:
            if address_string not in [device[0] for device in self.found_devices]:
                device_found = (address_string, self.ble_adapter, metadata)
                self.found_devices.append(device_found)
                logging.info(f"Device found : {device_found}")
                self.ble_adapter.connect(peer_addr)

    def on_gap_evt_connected(
        self, ble_driver, conn_handle, peer_addr, role, conn_params
    ):
        """
        Event that is called when a Bluetooth Low Energy connection is established adds connection to queue.

        :param ble_driver: A BLEDriver object.
        :param conn_handle: An integer representing the connection handle.
        :param peer_addr: A BLEGapAddr object representing the address of the device that has been connected to.
        :param role: An integer representing the role of the device in the connection.
        :param conn_params: A BLEGapConnParams object representing the connection parameters of the connection.
        """
        self.conn_q.put(conn_handle)

    def on_gap_evt_disconnected(self, ble_driver, conn_handle, reason):
        """
        Event that is called when a Bluetooth Low Energy connection is disconnected.

        :param ble_driver: A BLEDriver object.
        :param conn_handle: An integer representing the connection handle.
        :param reason: An integer representing the reason for disconnection.
        """
        self.conn_handler = None

    class Queue(BLEAdapterObserver):
        """
        A class representing a queue for notifications.

        :ivar ble_adapter: A BLEAdapter object.
        :ivar queue: A queue for storing notifications.
        """

        def __init__(self):
            """Initialize queue that receives notifications  ."""
            self.ble_adapter = BLE.ble_adapter
            self.ble_adapter.observer_register(self)
            self.queue = Queue()

        def on_notification(self, ble_adapter, conn_handle, uuid, data):
            """
            Handle a notification received event.

            :param ble_adapter: A BLEDriver object.
            :param conn_handle: An integer representing the connection handle.
            :param uuid: The UUID of the notification.
            :param data: The data contained in the notification.
            """
            data_hex = int_list_to_hex_string(data)
            logging.info(f" Notification received :  {uuid} = {data_hex}.")
            self.queue.put(data)

        def show_que_log(self):
            """Log the notifications in the queue."""
            logging.info("Notifications Queue")
            while not self.queue.empty():
                item = self.queue.get()
                logging.info(item)
