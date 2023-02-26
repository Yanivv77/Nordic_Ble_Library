# MSD.Nordic.Ble

## 1. API Doc: MSD.Nordic BLE

The MSD.Nordic.Ble library is created to provide a Python API for interacting with BLE devices functioning as GATT servers. It is built on the pc-ble-driver-py library and allows communication with a BLE device through a defined interface. The library includes methods for scanning the BLE environment to search for devices.

## 2. BLE device class methods:

#### 2.1 connect(timeout_in_millis: int)
Establish a connection to a device.
:param timeout_in_millis: timeout.
:return: True if successful /False.

#### 2.2 disconnect(timeout_in_millis: int):
Ends a connection to a device.
:param timeout_in_millis: timeout.
:return: True/False.

#### 2.3 discover_services():
Returns all device services and characteristics
:return: A dictionary of all the device services and characteristics.
key: a service tuple: (service.uuid, service.description)
value: an array of characteristics tuple: [(ch.description, ch.properties, ch.uuid)]

{
(service.uuid, service.description) = [(ch.description, ch.properties, ch.uuid)]
...
}

#### 2.4 read(char_uuid: str, timeout_in_millis: int)
Reads a value from a readable characteristic.
:param char_uuid: the identifier of the characteristic needed to be read.
:param timeout_in_millis: timeout
:return: the value that is read / ""

#### 2.5 write(char_uuid, data: bytes, timeout_in_millis: int):
Write data to a writeable characteristic.
:param char_uuid: the identifier of the characteristic needed to be written.
:param data: the data to be written
:param timeout_in_millis: timeout
:return: True if successful /False

#### 2.6 start_notify(char_uuid):
Register for a characteristic notifications. pushing notification arrives from the registered characteristic.
:param char_uuid: the identifier of the characteristic for registration
:return: True if successful /False

#### 2.7 stop_notify(char_uuid):
Stop characteristic notification.
:param char_uuid: the identifier of the characteristic to be unregistered
:return: True if successful /False

#### 2.8 is_connected():
Query the device connection
:return: True if successful /False

## 3. BLE Nordic Central CLass:

#### 3.3 connect(mac_address: str, timeout_in_millis: int):
Test device connection
:param mac_address: The tested device mac address
:param timeout_in_millis: timeout
:return: True/False

## 4. Queue
The BLE Queue class queue for notifications from all connected devices.
notification pushed into the queue on receive notification event

### 5.1 BLE Instance initialization parameters

#### 5.1.1 log_file
This parameter enables the settings of the log file path.
(see example code)
If omitted the default log file will reside in the current directory and be called ble.log.

#### 5.1.2 Communication port
BLE Communication port

### 5.2 BLE.Device initialization parameters

#### 5.1.1 mac_address
The Device mac address

#### 5.1.2 ble adapter
The Device adapter

## 6. Sample script:

    def demo():
        mac_address_str = ["C6:D8:48:B4:61:7C"]
        communication port = "COM5"

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
