#!/usr/bin/env python3
"""Set the charging current on a KEBA wallbox and enable charging.

Requires the `examples` extra: uv run --extra examples examples/set_charging_current.py 16

Rough current-to-power reference for a 3-phase connection:
    6A  -> ~4.0 kW
    9A  -> ~5.9 kW
    10A -> ~6.6 kW
    16A -> ~10.5 kW
"""

import json
import sys
import time

import click

from python_keba_client import KebaModbusClient, KebaModbusClientConnectionError


@click.command
@click.argument("current", type=int)
def main(current: int) -> None:
    """Set the charging current to CURRENT amperes and enable charging."""
    try:
        client = KebaModbusClient(address="192.168.160.56")
    except KebaModbusClientConnectionError as e:
        print(f"Error: {e}")
        sys.exit(1)

    client.set_charging_current(current)
    client.enable_chargingstation()
    time.sleep(3)
    print(json.dumps(client.todict(), indent=2))


if __name__ == "__main__":
    main()
