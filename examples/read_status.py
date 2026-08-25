#!/usr/bin/env python3
"""Connect to a KEBA wallbox and print its current status as JSON."""

import json
import sys

from python_keba_client import KebaModbusClient, KebaModbusClientConnectionError


try:
    client = KebaModbusClient(address="192.168.160.56")
except KebaModbusClientConnectionError as e:
    print(f"Error: {e}")
    sys.exit(1)

print(json.dumps(client.todict(), indent=2))
