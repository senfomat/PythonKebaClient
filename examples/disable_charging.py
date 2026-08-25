#!/usr/bin/env python3
"""Disable charging on a KEBA wallbox and print the resulting status."""

import json
import sys
import time

from python_keba_client import KebaModbusClient, KebaModbusClientConnectionError


try:
    client = KebaModbusClient(address="192.168.160.56")
except KebaModbusClientConnectionError as e:
    print(f"Error: {e}")
    sys.exit(1)

client.disable_chargingstation()
time.sleep(3)
print(json.dumps(client.todict(), indent=2))
