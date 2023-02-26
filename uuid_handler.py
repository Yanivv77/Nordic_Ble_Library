"""uuid handler class."""
from pc_ble_driver_py.ble_driver import BLEUUID, BLEUUIDBase


def string_to_hex_list(uuid_string):
    """
    Take a string representation of a UUID as an argument and returns a list of its hexadecimal values.

    The function first removes any dashes ("-") from the UUID string using the `replace` method,
    and then iterates through the string two characters at a time, converting each pair of characters to its
    corresponding hexadecimal value using the `int` function with a base of 16.

    :param uuid_string: A string representation of a UUID.
    :return: A list of hexadecimal values extracted from the given UUID string.
    """
    uuid_string = uuid_string.replace("-", "")
    return [int(uuid_string[i : i + 2], 16) for i in range(0, len(uuid_string), 2)]


def custom_uuid_base_builder(uuid_string):
    """
    Take a string representation of a UUID as an argument and returns a `BLEUUIDBase` object built from that UUID.

    The function first converts the UUID string to a list of hexadecimal values using the
    `string_to_hex_list` function, and then creates a `BLEUUIDBase` object from that list.

    :param uuid_string: A string representation of a UUID.
    :return: A `BLEUUIDBase` object built from the given UUID.
    """
    custom_uuid_base = BLEUUIDBase(string_to_hex_list(uuid_string))
    return custom_uuid_base


def custom_uuid_builder(uuid_string):
    """
    Take a string representation of a 16-bit UUID that includes a custom UUID base as an argument and returns a `BLEUUID` object built from that UUID.

     The function first extracts the custom UUID base using the
    `custom_uuid_base_builder` function and then creates a `BLEUUID` object using that base and the
    `BLEUUID.Standard.unknown` UUID type.

    :param uuid_string: A string representation of a 16-bit UUID that includes a custom UUID base.
    :return: A `BLEUUID` object built from the given UUID.
    """
    custom_uuid_base = custom_uuid_base_builder(uuid_string)
    custom_uuid = BLEUUID(BLEUUID.Standard.unknown, custom_uuid_base)
    return custom_uuid


def standard_uuid_builder(uuid):
    """
    Build a standard uuid.

    :param uuid: 16-bit UUID int representation.
    :return: standard_uuid object built from a standard 16-bit UUID  without any modification to the base.
    """
    standard_uuid = BLEUUID(uuid)
    return standard_uuid


def add_custom_uuid_to_ble(adapter, devices):
    """
    Add custom UUIDs to the BLE adapter.

    :param adapter: The BLE adapter to add the UUIDs to.
    :param devices: A dictionary containing device names and corresponding UUIDs to add to the adapter.
    :return: A boolean indicating whether or not all UUIDs were successfully added to the adapter.
    """
    success = True
    for key, values in devices.items():
        for value in values:
            try:
                hex_list = string_to_hex_list(value)
                base_uuid = BLEUUIDBase(hex_list)
                adapter.driver.ble_vs_uuid_add(base_uuid)
            except Exception as e:
                success = False
                print(f"Failed to add {value}: {e}")
    return success
