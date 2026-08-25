"""Shared pytest fixtures for the python_keba_client test suite."""

from types import SimpleNamespace

import pytest
from pymodbus.client.mixin import ModbusClientMixin

from python_keba_client.keba_modbus_client import KebaModbusClient


SLAVE_ID = 255

# Default register values, matching a real KEBA KeContact P30 c-series
# reading (firmware 3.10.80, 16A hardware max, standalone installation).
DEFAULT_REGISTERS: dict[int, int] = {
    1000: 3,  # State: charging
    1004: 7,  # Cable state: plugged into vehicle and locked
    1014: 34840522,  # Serial number
    1018: 0x030A5000,  # Firmware version 3.10.80
    1020: 4000000,  # Active power: 4000 W
    1036: 133200,  # Total energy: 13.32 kWh
    1100: 16000,  # Max charging current: 16 A
    1110: 16000,  # Max supported current: 16 A
    1500: 0,  # RFID card UID
    1502: 10190,  # Charged energy: 10.19 kWh
}


def _to_registers(value: int) -> list[int]:
    """Split a uint32 value into two big-endian 16-bit Modbus registers.

    Returns
    -------
    list[int]
        `[high_word, low_word]`.

    """
    return [(value >> 16) & 0xFFFF, value & 0xFFFF]


class FakeModbusConnection:
    """Minimal stand-in for `pymodbus.client.ModbusTcpClient` used in tests.

    Serves reads from an in-memory register map and records writes, without
    touching the network. Uses the real `convert_from_registers` decoding
    logic from pymodbus so tests exercise the same code path as production.
    """

    convert_from_registers = staticmethod(ModbusClientMixin.convert_from_registers)

    def __init__(self, registers: dict[int, int] | None = None) -> None:
        self.registers = dict(DEFAULT_REGISTERS if registers is None else registers)
        self.writes: list[tuple[int, int, int]] = []

    def connect(self) -> bool:
        return True

    def is_socket_open(self) -> bool:
        return True

    def read_holding_registers(
        self, register: int, *, count: int, device_id: int
    ) -> SimpleNamespace:
        assert device_id == SLAVE_ID
        assert count == 2
        return SimpleNamespace(registers=_to_registers(self.registers[register]))

    def write_register(self, register: int, value: int, *, device_id: int) -> None:
        assert device_id == SLAVE_ID
        self.writes.append((register, value, device_id))


@pytest.fixture
def fake_connection() -> FakeModbusConnection:
    """A fresh `FakeModbusConnection` with default register values.

    Returns
    -------
    FakeModbusConnection
        A connection double seeded with `DEFAULT_REGISTERS`.

    """
    return FakeModbusConnection()


@pytest.fixture
def keba_client(fake_connection: FakeModbusConnection) -> KebaModbusClient:
    """A `KebaModbusClient` wired to a `fake_connection`, without any real I/O.

    Returns
    -------
    KebaModbusClient
        A client instance with its Modbus connection replaced by `fake_connection`.

    """
    client = KebaModbusClient.__new__(KebaModbusClient)
    client.address = "192.0.2.1"
    client.port = 502
    client.timeout = 10
    client.slaveid = SLAVE_ID
    client.debug = False
    client.connection = fake_connection

    return client
