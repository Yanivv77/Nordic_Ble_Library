# MSD.Ble.MMClient

## 1. MMClient

The MSD.BLE.MMClient provide communication with MilkMeter devices using the MSD.Ble library.
It communicates with the device's two BLE services
* MMP
* BCP

## 2. The MMBleClient class:
This Class includes methods for communicating with a MilkMeter device through BLE
The client has two "services" (MMP,BCP) coded in the "services" attribute and an async queue
coded in the 'output' attribute.
On connection both service notifications will get forwarded to the output queue until the connection is terminated
Class initialisation parameters:
* mac: the MAC Address of the MilkMeter Device
* timeout: The duration in seconds the methods read and read_all waits for data. when timeout=0
the read will halt until the 'output' queue gets data. default 0
* log_file: the path for the log file (passed to MSD.Ble). default 'MMBleClient.log'

The class was design to be compatible with "old" serial communication scripts.

## 3. The MMBleClient class methods:

### connect()
Connects to the device (self.device).
will throw an Exception if it cannot be connected.
On success registers for both services notifications.

### close()
Terminates the current connection

### read(n: int = 1) -> bytes:
Read number of bytes from the ble device.
If a timeout is set it may return fewer characters as requested.
With no timeout it will block until the requested number of bytes is read.
Params:
* n: number of bytes to read. default: 1

returns the data that was read (bytes)

### read_all() -> bytes:
Reads all the data stored in the output queue.
If there is data in the output queue it will fetch it if not it will wait for data for the duration of the timeout.
returns All the data that was read (bytes)

### write(data: bytes) -> int:
Write data to a service write characteristic
It concludes the service to be writen to from the written data.
Params:
* data: the data to be written.

returns the length of the data written.

## Remarks:
The class also includes the 'flush' method which do nothing.
(for backward compatibility with old serial communication scripts)
