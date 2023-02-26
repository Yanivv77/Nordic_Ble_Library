"""
Including here code snippet with two commands.

DCL command for SLEEP, should work as is.
BCP command for KV SET, may fail with different address.
Note that it might be needed to set BCP address to the MM unit (currently 0/80 in the example).
"""

import time

from MMBleNordicClient import MMBleClient

mac = "8453DFBF-12E8-4E9F-930C-6900CBC58BD7"
mm = "C6:D8:48:B4:61:7C"
bc = MMBleClient(mm, 5000, log_file="mm1.log")

bc.connect()

# this should work
dcl_req = bytes.fromhex("AA 0E 01 02 03 01 0E")
wr = bc.write(dcl_req)
print("wr:", wr)

dcl_res = bc.read(5)
print("dcl_res", dcl_res)
dcl_res = dcl_res + bc.read(20)
print("dcl_res", dcl_res)
dcl_res = bc.read_all()
print("dcl_res", dcl_res)

time.sleep(16)
long_queue_test = bc.read(60)
print("long_queue_test1:", long_queue_test)
long_queue_test = bc.read(3)
print("long_queue_test2:", long_queue_test)
long_queue_test = bc.read_all()
print("long_queue_test3:", long_queue_test)
bc.close()
