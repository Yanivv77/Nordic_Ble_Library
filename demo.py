import time
from ble_nordic import BLE


def demo():
    mac_address_str = ["C6:D8:48:B4:61:7C"]
    connection_port = "COM5"

    services = {
                "MMP": [
                    "10000000-1000-1000-8000-00805f9baaaa",
                    "10000000-2000-1000-8000-00805f9baaaa",
                ],
                "BCP": [
                    "40000000-1000-1000-8000-00805f9baaaa",
                    "40000000-2000-1000-8000-00805f9baaaa",
                ],
            }


    # chars for testing
    read_characteristic = 0x2A00
    write_characteristic_uuid = "40000000-1000-1000-8000-00805F9BAAAA"
    write_characteristic_value = [110]
    notify_characteristic_uuid = "40000000-2000-1000-8000-00805F9BAAAA"

    ble = BLE(log_file_path="ble.log", port=connection_port)

    ble_queue = ble.Queue()

    scan_res = ble.scan_by_mac(mac_address_str, 5000)
    print("scan result", scan_res)

    for device in [x for x in scan_res]:
        device = ble.Device(device[0], device[1])
        device.device_services = services
        print("device", device)

        is_connection_successful = device.connect(5000)
        print("is_connection_successful", is_connection_successful)

        is_connected = device.is_connected()
        print("is_connected", is_connected)

        all_characteristics = device.discover_services()
        print("characters", all_characteristics)

        char_value = device.read(read_characteristic, 4000)
        print("char_value", char_value)

        is_write_successful = device.write(
            write_characteristic_uuid, write_characteristic_value, 5000
        )
        print("is_write_successful", is_write_successful)

        is_start_notify_successful = device.start_notify(notify_characteristic_uuid)
        print("is_start_notify_successful", is_start_notify_successful)

        time.sleep(10)

        is_stop_notify_successful = device.stop_notify(notify_characteristic_uuid)
        print("is_stop_notify_successful", is_stop_notify_successful)

        is_disconnected = device.disconnect(5000)
        print("is_disconnected", is_disconnected)

        is_connected = device.is_connected()
        print("is_connected", is_connected)

    ble_queue.show_que_log()


if __name__ == "__main__":
    demo()
