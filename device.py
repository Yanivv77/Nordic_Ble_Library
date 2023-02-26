"""This module provides functions for Bluetooth Low Energy device."""


from queue import Empty, Queue
from pc_ble_driver_py.ble_driver import (
    BLEGapScanParams,
    BLEGattStatusCode,
    BLEAdvData,
    BLEGapTimeoutSrc,
    BLEUUID,
)
from pc_ble_driver_py.exceptions import NordicSemiException
from pc_ble_driver_py.observers import BLEDriverObserver, BLEAdapterObserver
from uuid_handler import custom_uuid_base_builder, add_custom_uuid_to_ble
from func_timeout import func_timeout, FunctionTimedOut
import logging

logger = logging.getLogger(__name__)


class Device(BLEDriverObserver, BLEAdapterObserver):
    """

    Represents a Bluetooth Low Energy device.

    BLEDriverObserver defines the methods that should be implemented to receive notifications related to events in
    the BLE driver, such as when it is started or stopped, or when an error occurs.
    BLEAdapterObserver defines the methods that should be implemented to receive notifications related to events in the
    BLE adapter, such as when a new device is discovered, when a device is connected or disconnected, or when a
    characteristic value is read or written.

    :param mac_address: The MAC address of the device.
    :param ble_adapter: The BLE adapter used to communicate with the device.
    """

    def __init__(self, mac_address, ble_adapter=None):
        """Initialize a new instance of the Device class."""
        self.ble_adapter = ble_adapter
        self.ble_adapter.observer_register(self)
        self.ble_adapter.driver.observer_register(self)
        self.conn_handler = None
        self.disconnect_reason = None
        self.conn_q = Queue()
        self.notification_q = Queue()
        self.mac_address_to_connect = mac_address
        self.localName = ""
        self.advData = ""
        self.services = []
        self.characteristics = []
        self.descriptors = []
        self.device_services = {}



    def connect(self, timeout_in_millis: int):
        """
        Connect to a BLE device with a specified MAC address.

        :param timeout_in_millis: The time in milliseconds to scan and connect to the device.
        :return: True if the connection was successful, False otherwise.
        """
        timeout_in_secs = timeout_in_millis / 1000
        logger.info(f"Scan start, trying to find {self.mac_address_to_connect}")
        scan_duration = timeout_in_secs
        params = BLEGapScanParams(
            interval_ms=500, window_ms=500, timeout_s=timeout_in_millis
        )
        self.ble_adapter.driver.ble_gap_scan_start(scan_params=params)
        try:
            new_conn = self.conn_q.get(timeout=scan_duration)
            self.conn_handler = new_conn
            add_custom_uuid_to_ble(self.ble_adapter, self.device_services)
            self.ble_adapter.service_discovery(new_conn)
        except Empty:
            logger.info(
                f"No device advertising with name {self.mac_address_to_connect} found."
            )
        if self.conn_handler is not None:
            logger.info(f"New connection: {self.mac_address_to_connect}.")
            return True
        else:
            return False

    def disconnect(self, timeout_in_millis: int):
        """
        Disconnect from a BLE device.

        :param timeout_in_millis: The time in milliseconds to wait for the disconnection to complete.
        :return: True if the disconnect was successful, False otherwise.
        """
        try:
            if self.conn_handler is not None:
                func_timeout(
                    timeout_in_millis / 1000,
                    self.ble_adapter.driver.ble_gap_disconnect,
                    args=(self.conn_handler,),
                )
                self.conn_handler = None
        except FunctionTimedOut:
            logger.info("Disconnection request timed out.")
            return False
        except NordicSemiException as e:
            logger.info("Error occurred while disconnecting: ", str(e))
            return False
        logger.info(f"Disconnect: {self.mac_address_to_connect}.")
        return True

    def is_connected(self):
        """
        Check if the device is connected.

        :return: True if the device is connected, False otherwise.
        """
        if self.conn_handler is not None:
            return True
        else:
            return False

    def is_disconnected(self):
        """
        Check if the device is disconnected.

        :return: True if the device is disconnected, False otherwise.
        """
        if self.conn_handle is None:
            return True
        else:
            return False

    def discover_services(self):
        """
        Discover all the services, characteristics and descriptors of the connected device.

        :return: A List containing the discovered services, characteristics and descriptors.
        """
        result = []
        for service in self.ble_adapter.db_conns[self.conn_handler].services:
            result.append(str(service))
            for char in service.chars:
                result.append(f"    {str(char)}")
                for desc in char.descs:
                    result.append(f"       {str(desc)}")

        logger.info("Services discovered")
        return "\n".join(result)

    def read(self, uuid: str, timeout_in_millis: int):
        """
        Read data from a characteristic identified by the input UUID.

        :param uuid: The UUID of the characteristic as either a 16-bit integer or a string.
        :param timeout_in_millis: Timeout in milliseconds for the operation.
        :return: the data read from the characteristic, as a string.
        """
        if isinstance(uuid, str):
            uuid_type = BLEUUID.Standard.unknown
            uuid_base = custom_uuid_base_builder(uuid)
            self.ble_adapter.driver.ble_vs_uuid_add(uuid_base)
            uuid = BLEUUID(uuid_type, uuid_base)

        if isinstance(uuid, int):
            uuid = BLEUUID(uuid)

        try:
            data = func_timeout(
                timeout_in_millis / 1000,
                self.ble_adapter.read_req,
                args=(self.conn_handler, uuid),
            )
        except FunctionTimedOut as e:
            logger.info(e, " Timed out while reading from the characteristic")
            return False

        if data[0] == BLEGattStatusCode.success:
            data = bytearray(data[1]).decode("utf-8", errors="ignore")
            logger.info(f"Read: {data} from : {uuid} .")
            return data
        return False

    def write(self, uuid, write_params: bytes, timeout_in_millis: int):
        """
        Write a value to a BLE characteristic identified by UUID.

        :param uuid: The UUID of the characteristic as either a 16-bit integer or a string.
        :param write_params: The data to be written to the characteristic as a bytes object.
        :param timeout_in_millis: Timeout in milliseconds for the operation.
        :return: True if the write was successful, False otherwise.
        """
        if isinstance(uuid, str):
            uuid_type = BLEUUID.Standard.unknown
            uuid_base = custom_uuid_base_builder(uuid)
            self.ble_adapter.driver.ble_vs_uuid_add(uuid_base)
            uuid = BLEUUID(uuid_type, uuid_base)

        if isinstance(uuid, int):
            uuid = BLEUUID(uuid)

        try:
            func_timeout(
                timeout_in_millis / 1000,
                self.ble_adapter.write_req,
                args=(self.conn_handler, uuid, write_params),
            )
        except FunctionTimedOut:
            logger.error(
                f"Write operation timed out after {timeout_in_millis} ms for characteristic {uuid}."
            )
            return False
        except NordicSemiException as e:
            logger.error(
                f"Failed to write characteristic value {write_params !r} to characteristic {uuid !r}: {e !r}"
            )
            return False

        logger.info(f"Wrote {write_params !r} to characteristic {uuid}.")
        return True

    def start_notify(self, uuid):
        """
        Enable notifications for a specific characteristic identified by a given UUID.

        :param uuid: The UUID of the characteristic as either a 16-bit integer or a string.
        :return: True if notification enabling was successful, False otherwise.
        """
        if isinstance(uuid, str):
            uuid_type = BLEUUID.Standard.unknown
            uuid_base = custom_uuid_base_builder(uuid)
            self.ble_adapter.driver.ble_vs_uuid_add(uuid_base)
            uuid = BLEUUID(uuid_type, uuid_base)

        if isinstance(uuid, int):
            uuid = BLEUUID(uuid)

        try:
            self.ble_adapter.enable_notification(self.conn_handler, uuid)
            logger.info("Notification enabled.")
        except NordicSemiException as e:
            logger.info(f"Exception {e}")
            return False
        return True

    def stop_notify(self, uuid):
        """
        Stop notifications for a characteristic with the given UUID on the connected device.

        :param uuid: The UUID of the characteristic for which notifications should be stopped.
        :return: Returns True if the notifications were successfully stopped, otherwise False.
        """
        if isinstance(uuid, str):
            uuid_type = BLEUUID.Standard.unknown
            uuid_base = custom_uuid_base_builder(uuid)
            self.ble_adapter.driver.ble_vs_uuid_add(uuid_base)
            uuid = BLEUUID(uuid_type, uuid_base)

        if isinstance(uuid, int):
            uuid = BLEUUID(uuid)

        try:
            self.ble_adapter.disable_notification(self.conn_handler, uuid)
            logger.info("Notification disabled.")
        except NordicSemiException as e:
            logger.info(f"Exception {e}")
            return False
        return True

    def on_gap_evt_connected(
        self, ble_driver, conn_handle, peer_addr, role, conn_params
    ):
        """
        Event that called by the BLE driver when a new connection has been established adds connection to a queue.

        :param ble_driver: The BLE driver that called this method.
        :param conn_handle: The handle of the new connection.
        :param peer_addr: The address of the peer device.
        :param role: The role of the local device in the connection (central or peripheral).
        :param conn_params: The parameters used for the connection.
        """
        self.conn_q.put(conn_handle)

    def on_gap_evt_disconnected(self, ble_driver, conn_handle, reason):
        """
        Event that by the BLE driver when a connection has been disconnected removes connection adds disconnect reason.

        :param ble_driver: The BLE driver that called this method.
        :param conn_handle: The handle of the disconnected connection.
        :param reason: The reason for the disconnection.
        """
        self.conn_handler = None
        self.disconnect_reason = reason

    def on_gap_evt_timeout(self, ble_driver, conn_handle, src):
        """
        Event that called by the BLE driver when a timeout event has occurred.

        :param ble_driver: The BLE driver that called this method.
        :param conn_handle: The handle of the connection associated with the timeout event.
        :param src: The source of the timeout event.
        """
        if src == BLEGapTimeoutSrc.scan:
            ble_driver.ble_gap_scan_start()

    def on_gap_evt_adv_report(
        self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data
    ):
        """
        Event that called by the BLE driver when an advertising report is received.

        :param ble_driver: The BLE driver that called this method.
        :param conn_handle: The handle of the connection.
        :param peer_addr: The address of the peer device.
        :param rssi: The RSSI of the received signal.
        :param adv_type: The type of the advertising packet.
        :param adv_data: The data contained in the advertising packet.
        """
        if BLEAdvData.Types.complete_local_name in adv_data.records:
            dev_name_list = adv_data.records[BLEAdvData.Types.complete_local_name]
            dev_name = "".join(chr(e) for e in dev_name_list)
            if len(dev_name) > 0:
                self.localName = dev_name
        elif BLEAdvData.Types.short_local_name in adv_data.records:
            dev_name_list = adv_data.records[BLEAdvData.Types.short_local_name]
            dev_name = "".join(chr(e) for e in dev_name_list)
            if len(dev_name) > 0:
                self.localName = dev_name
        else:
            return

        if BLEAdvData.Types.manufacturer_specific_data in adv_data.records:
            if (
                adv_data.records.get(BLEAdvData.Types.manufacturer_specific_data)
                is None
            ):
                pass
            else:
                dev_adv_data = adv_data.records[
                    BLEAdvData.Types.manufacturer_specific_data
                ]
                dev_adv_data = "".join(f"{b:02X}" for b in dev_adv_data)
                self.advData = dev_adv_data

        address_string = ":".join(f"{b:02X}" for b in peer_addr.addr)
        if address_string == self.mac_address_to_connect:
            self.ble_adapter.connect(peer_addr)

    def on_notification(self, ble_adapter, conn_handle, uuid, data):
        """
        Event that called by the BLE adapter when a notification is received.

        :param ble_adapter: The BLE adapter that called this method.
        :param conn_handle: The handle of the connection.
        :param uuid: The UUID of the characteristic that sent the notification.
        :param data: The data contained in the notification.
        """
        self.notification_q.put(data)

    def on_gattc_evt_prim_srvc_disc_rsp(
        self, ble_driver, conn_handle, status, services
    ):
        """
        Handle the services discovery response event and append the discovered services' information.

        :param ble_driver: The BLE driver that called this method.
        :param conn_handle: The handle of the connection.
        :param status: The status of the request.
        :param services: The list of discovered services.

        """
        services_str = "\n ".join(str(s) for s in services)
        self.services.append(services_str)

    def on_gattc_evt_char_disc_rsp(
        self, ble_driver, conn_handle, status, characteristics
    ):
        """
        Handle the characteristics discovery response event and append the discovered characteristic information.

        :param ble_driver: The BLE driver that called this method.
        :param conn_handle: The handle of the connection.
        :param status: The status of the request.
        :param characteristics: The list of discovered characteristics.
        """
        chars_str = "\n ".join(str(c) for c in characteristics)
        if chars_str:
            self.characteristics.append(chars_str)

    def on_gattc_evt_desc_disc_rsp(self, ble_driver, conn_handle, status, descriptors):
        """
        Handle the descriptors discovery response event and append the discovered descriptors information.

        :param ble_driver: The BLE driver that called this method.
        :param conn_handle: The handle of the connection.
        :param status: The status of the request.
        :param descriptors: The list of discovered descriptors.
        """
        descs_str = "\n ".join(str(c) for c in descriptors)
        if descs_str:
            self.descriptors.append(descs_str)
