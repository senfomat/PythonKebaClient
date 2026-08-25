"""Tests for `KebaModbusClientSettings` validation."""

import pytest
from pydantic import ValidationError

from python_keba_client.keba_modbus_client import KebaModbusClientSettings


def test_defaults_are_applied() -> None:
    settings = KebaModbusClientSettings(address="192.0.2.1")

    assert settings.port == 502
    assert settings.timeout == 10
    assert settings.slaveid == 255
    assert settings.debug is False


def test_empty_address_is_rejected() -> None:
    with pytest.raises(ValidationError):
        KebaModbusClientSettings(address="")


@pytest.mark.parametrize("port", [0, -1, 65536, 99999])
def test_port_out_of_range_is_rejected(port: int) -> None:
    with pytest.raises(ValidationError):
        KebaModbusClientSettings(address="192.0.2.1", port=port)


@pytest.mark.parametrize("port", [1, 502, 65535])
def test_valid_ports_are_accepted(port: int) -> None:
    settings = KebaModbusClientSettings(address="192.0.2.1", port=port)

    assert settings.port == port


@pytest.mark.parametrize("timeout", [0, -1])
def test_non_positive_timeout_is_rejected(timeout: int) -> None:
    with pytest.raises(ValidationError):
        KebaModbusClientSettings(address="192.0.2.1", timeout=timeout)


@pytest.mark.parametrize("slaveid", [-1, 256])
def test_slaveid_out_of_range_is_rejected(slaveid: int) -> None:
    with pytest.raises(ValidationError):
        KebaModbusClientSettings(address="192.0.2.1", slaveid=slaveid)
