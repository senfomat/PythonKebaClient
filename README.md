# PythonKebaClient

A Python client library for reading and controlling [KEBA KeContact](https://www.keba.com/en/emobility/products-solutions/charging-stations) wallboxes (P30 series) over Modbus TCP.

## Installation

```bash
uv add keba-modbus-client
```

Requires Python 3.10+. The wallbox's Modbus TCP interface must be enabled (DIP switch DSW1.3 = ON; see the "KEBA KeContact P20/P30 Installation Manual").

## Usage

```python
from python_keba_client import KebaModbusClient

client = KebaModbusClient(address="192.168.1.50")

print(client.charging_state)
# {"state": <ChargingState.CHARGING: 3>, "text": "A charging process is active."}

print(client.active_power)  # W
print(client.total_energy)  # kWh

client.set_charging_current(16)  # A
client.enable_chargingstation()
client.disable_chargingstation()
```

`client.todict()` returns a single dict with all readings, ready for `json.dumps(...)`.

See [`examples/`](examples/) for complete, runnable scripts (reading status, setting the charging current via a CLI, disabling charging).

### Configuration via environment variables

Connection settings can also be supplied via `KEBA_`-prefixed environment variables (`KEBA_ADDRESS`, `KEBA_PORT`, `KEBA_TIMEOUT`, `KEBA_SLAVEID`, `KEBA_DEBUG`) instead of constructor arguments, via the underlying `pydantic-settings` model.

### A note on `disable_chargingstation()`

On some wallboxes/firmware versions, writing to the enable/disable register (5014) over Modbus TCP does not reliably stop a charging session that is already in progress, even though the write is acknowledged without error. If you hit this:

- Check the wallbox's DIP switch DSW2.5 ("communication hub mode"). It should be OFF unless the wallbox is a client behind an x-series master, a KeContact C10 hub, or an OCPP backend — otherwise the wallbox may defer session control to a higher-ranking system that isn't actually present.
- The Modbus TCP and UDP interfaces are mutually exclusive on the wallbox (enabling one disables the other via the same DIP switch), so this cannot be worked around by also speaking the older KEBA UDP protocol without giving up Modbus TCP.

## Development

```bash
uv sync --all-extras --all-groups
uv run pytest
uvx ruff format .
uvx ruff check .
uvx ty check .
```

See [RELEASING.md](RELEASING.md) for how to publish a new version to PyPI.

## License

MIT, see [LICENSE](LICENSE).
