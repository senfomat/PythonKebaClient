"""Tests for `KebaModbusClient` reads, writes and state mapping."""

import pytest

from python_keba_client.keba_modbus_client import (
    CableState,
    ChargingState,
    KebaModbusClient,
    KebaModbusClientParamOorError,
)
from tests.conftest import FakeModbusConnection


def test_firmware_version(keba_client: KebaModbusClient) -> None:
    assert keba_client.firmware_version == "3.10.80"


def test_serial_number(keba_client: KebaModbusClient) -> None:
    assert keba_client.serial_number == 34840522


def test_active_power_is_a_float(keba_client: KebaModbusClient) -> None:
    assert keba_client.active_power == pytest.approx(4000.0)
    assert isinstance(keba_client.active_power, float)


def test_total_energy(keba_client: KebaModbusClient) -> None:
    assert keba_client.total_energy == pytest.approx(13.32)


def test_charged_energy(keba_client: KebaModbusClient) -> None:
    assert keba_client.charged_energy == pytest.approx(10.19)


def test_max_charging_current(keba_client: KebaModbusClient) -> None:
    assert keba_client.max_charging_current == 16


def test_max_supported_current(keba_client: KebaModbusClient) -> None:
    assert keba_client.max_supported_current == 16


def test_charging_state_known_value(keba_client: KebaModbusClient) -> None:
    state = keba_client.charging_state

    assert state["state"] is ChargingState.CHARGING
    assert state["text"] == "A charging process is active."


def test_charging_state_unknown_value_has_no_text(
    fake_connection: FakeModbusConnection, keba_client: KebaModbusClient
) -> None:
    fake_connection.registers[1000] = 42

    state = keba_client.charging_state

    assert state["state"] == 42
    assert state["text"] is None


def test_cable_state_known_value(keba_client: KebaModbusClient) -> None:
    state = keba_client.cable_state

    assert state["state"] is CableState.PLUGGED_VEHICLE_LOCKED
    assert "locked (charging)" in state["text"]


def test_cable_state_unknown_value_has_no_text(
    fake_connection: FakeModbusConnection, keba_client: KebaModbusClient
) -> None:
    fake_connection.registers[1004] = 2

    state = keba_client.cable_state

    assert state["state"] == 2
    assert state["text"] is None


def test_set_charging_current_writes_milliamps(
    fake_connection: FakeModbusConnection, keba_client: KebaModbusClient
) -> None:
    keba_client.set_charging_current(16)

    assert fake_connection.writes == [(5004, 16000, 255)]


@pytest.mark.parametrize("current", [0, 5, 64, 100])
def test_set_charging_current_out_of_range_raises(
    keba_client: KebaModbusClient, current: int
) -> None:
    with pytest.raises(KebaModbusClientParamOorError):
        keba_client.set_charging_current(current)


def test_set_charging_kilowatthours_writes_value(
    fake_connection: FakeModbusConnection, keba_client: KebaModbusClient
) -> None:
    keba_client.set_charging_kilowatthours(60)

    assert fake_connection.writes == [(5010, 6000, 255)]


def test_set_charging_kilowatthours_below_one_raises(
    keba_client: KebaModbusClient,
) -> None:
    with pytest.raises(KebaModbusClientParamOorError):
        keba_client.set_charging_kilowatthours(0)


def test_enable_chargingstation_writes_one(
    fake_connection: FakeModbusConnection, keba_client: KebaModbusClient
) -> None:
    keba_client.enable_chargingstation()

    assert fake_connection.writes == [(5014, 1, 255)]


def test_disable_chargingstation_writes_zero(
    fake_connection: FakeModbusConnection, keba_client: KebaModbusClient
) -> None:
    keba_client.disable_chargingstation()

    assert fake_connection.writes == [(5014, 0, 255)]


def test_unlock_plug_writes_zero(
    fake_connection: FakeModbusConnection, keba_client: KebaModbusClient
) -> None:
    keba_client.unlock_plug()

    assert fake_connection.writes == [(5012, 0, 255)]


def test_todict_contains_all_readings(keba_client: KebaModbusClient) -> None:
    result = keba_client.todict()

    assert result.keys() == {
        "chargingState",
        "firmwareVersion",
        "maxSupportedCurrent",
        "maxChargingCurrent",
        "cableState",
        "serialNumber",
        "activePower",
        "totalEnergy",
        "chargedEnergy",
        "RFIDcard",
    }
