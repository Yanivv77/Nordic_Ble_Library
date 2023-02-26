"""utility class."""
from setup.__init__ import Settings
from pc_ble_driver_py.ble_driver import (
    BLEDriver,
    BLEConfig,
    BLEConfigConnGatt,
)
from pc_ble_driver_py.ble_adapter import BLEAdapter

Settings = Settings


def setup_adapter(
    port,
    auto_flash,
    baud_rate,
    retransmission_interval,
    response_timeout,
    driver_log_level,
):
    """
    Set up a BLE adapter.

    The Settings.current() call retrieves the current settings.
    The BLEDriver class is then initialized with the specified settings and a BLE adapter is created using the driver.
    Finally, the function sets the attributes of the connection GATT configuration using BLEConfigConnGatt
    and sets the adapter's configuration using adapter.driver.ble_cfg_set.
    The function then enables the BLE adapter and returns the adapter to the caller.
    """
    driver = BLEDriver(
        serial_port=port,
        auto_flash=auto_flash,
        baud_rate=baud_rate,
        retransmission_interval=retransmission_interval,
        response_timeout=response_timeout,
        log_severity_level=driver_log_level,
    )

    adapter = BLEAdapter(driver)
    adapter.driver.open()
    gatt_cfg = BLEConfigConnGatt()
    gatt_cfg.att_mtu = adapter.default_mtu
    adapter.driver.ble_cfg_set(BLEConfig.conn_gatt, gatt_cfg)
    adapter.driver.ble_enable()
    return adapter


def int_list_to_hex_string(int_list):
    """Covert received data form int array to hex string."""
    hex_list = [format(x, "02X") for x in int_list]
    hex_string = " ".join(hex_list)
    return hex_string
