#!/usr/bin/env python3.10

import json
import sys
from KebaModbusClientClass import KebaModbusClient, KebaModbusClientConnectionException

# import logging
# logging.basicConfig()
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

try:
    k = KebaModbusClient(address="192.168.160.56")
except KebaModbusClientConnectionException as e:
    print(f"Error: {e}")
    sys.exit(1)

print(json.dumps(k.todict(), indent=4))
# print(k.firmwareVersion)
# print(k.enableChargingStation())
# print(k.disableChargingStation())
# print(k.unlockPlug())
