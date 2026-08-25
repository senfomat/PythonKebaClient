"""Modbus TCP client for KEBA KeContact wallboxes."""

from collections.abc import Sequence
from enum import IntEnum
from typing import Literal, Protocol, cast

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymodbus import pymodbus_apply_logging_config
from pymodbus.client import ModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin


class _RegistersResponse(Protocol):
    """The subset of a Modbus read response that `KebaModbusClient` relies on."""

    registers: list[int]


class ModbusConnection(Protocol):
    """Structural interface for the Modbus connection used by `KebaModbusClient`.

    Satisfied by `pymodbus.client.ModbusTcpClient` in production and by a
    lightweight test double in the test suite.
    """

    def connect(self) -> bool: ...

    def is_socket_open(self) -> bool: ...

    def read_holding_registers(
        self, address: int, /, *, count: int, device_id: int
    ) -> _RegistersResponse: ...

    def write_register(
        self, address: int, value: int, /, *, device_id: int
    ) -> object: ...

    def convert_from_registers(
        self,
        registers: Sequence[int],
        data_type: ModbusClientMixin.DATATYPE,
        word_order: Literal["big", "little"] = "big",
    ) -> int | float | str | list[bool] | list[int] | list[float]: ...


class KebaModbusClientConnectionError(Exception):
    """Raised when the Modbus TCP connection to the wallbox could not be established."""


class KebaModbusClientParamOorError(Exception):
    """Raised when a parameter passed to a setter is outside its supported range."""


class ChargingState(IntEnum):
    """Value of holding register 1000 ("State")."""

    STARTING_UP = 0
    NOT_READY = 1
    READY = 2
    CHARGING = 3
    ERROR = 4
    SUSPENDED = 5


_CHARGING_STATE_TEXT: dict[ChargingState, str] = {
    ChargingState.STARTING_UP: "Start-up of the charging station",
    ChargingState.NOT_READY: (
        "The charging station is not ready for charging. The charging station "
        "is not connected to an electric vehicle, it is locked by the "
        "authorization function or another mechanism."
    ),
    ChargingState.READY: (
        "The charging station is ready for charging and waits for a reaction "
        "from the electric vehicle."
    ),
    ChargingState.CHARGING: "A charging process is active.",
    ChargingState.ERROR: "An error has occurred.",
    ChargingState.SUSPENDED: (
        "The charging process is temporarily interrupted because the "
        "temperature is too high or the wallbox is in suspended mode."
    ),
}


class CableState(IntEnum):
    """Value of holding register 1004 ("Cable state")."""

    UNPLUGGED = 0
    PLUGGED_STATION = 1
    PLUGGED_STATION_LOCKED = 3
    PLUGGED_VEHICLE = 5
    PLUGGED_VEHICLE_LOCKED = 7


_CABLE_STATE_TEXT: dict[CableState, str] = {
    CableState.UNPLUGGED: "No cable is plugged",
    CableState.PLUGGED_STATION: (
        "Cable is connected to the charging station (not to the electric vehicle)."
    ),
    CableState.PLUGGED_STATION_LOCKED: (
        "Cable is connected to the charging station and locked "
        "(not to the electric vehicle)."
    ),
    CableState.PLUGGED_VEHICLE: (
        "Cable is connected to the charging station and the electric vehicle "
        "(not locked)."
    ),
    CableState.PLUGGED_VEHICLE_LOCKED: (
        "Cable is connected to the charging station and the electric vehicle "
        "and locked (charging)."
    ),
}


class KebaModbusClientSettings(BaseSettings):
    """Validated connection settings for `KebaModbusClient`.

    Values can also be supplied via environment variables prefixed with
    `KEBA_` (e.g. `KEBA_ADDRESS`, `KEBA_PORT`); explicit constructor
    arguments take precedence over those.
    """

    model_config = SettingsConfigDict(env_prefix="KEBA_")

    address: str = Field(min_length=1)
    port: int = Field(default=502, ge=1, le=65535)
    timeout: int = Field(default=10, gt=0)
    slaveid: int = Field(default=255, ge=0, le=255)
    debug: bool = False


class KebaModbusClient:
    """Client for reading and controlling a KEBA KeContact wallbox via Modbus TCP.

    Attributes
    ----------
    address : str
        IP address or hostname of the wallbox.
    port : int
        Modbus TCP port of the wallbox. Default: 502.
    timeout : int
        Read timeout in seconds. Default: 10.
    slaveid : int
        Modbus device/slave ID. Default: 255 (single-station installation).
    debug : bool
        Enable pymodbus debug logging. Default: False.

    """

    __slots__ = ["address", "connection", "debug", "port", "slaveid", "timeout"]

    address: str
    connection: ModbusConnection
    debug: bool
    port: int
    slaveid: int
    timeout: int

    def __init__(
        self,
        *,
        address: str,
        port: int = 502,
        timeout: int = 10,
        slaveid: int = 255,
        debug: bool = False,
    ) -> None:
        """Validate the connection settings and connect to the wallbox.

        Connection settings are validated by `KebaModbusClientSettings`
        (raises `pydantic.ValidationError` on invalid input), then
        `_connect` is called (raises `KebaModbusClientConnectionError` on
        failure).
        """
        settings = KebaModbusClientSettings(
            address=address,
            port=port,
            timeout=timeout,
            slaveid=slaveid,
            debug=debug,
        )

        self.address = settings.address
        self.port = settings.port
        self.timeout = settings.timeout
        self.slaveid = settings.slaveid
        self.debug = settings.debug

        self.connection = self._connect()

    def _connect(self) -> ModbusTcpClient:
        """Try to connect to the wallbox via Modbus TCP.

        Returns
        -------
        ModbusTcpClient
            The connected Modbus TCP client.

        Raises
        ------
        KebaModbusClientConnectionError
            If the socket could not be opened.

        """
        client = ModbusTcpClient(self.address, port=self.port, timeout=self.timeout)

        if self.debug:
            pymodbus_apply_logging_config(level="DEBUG")

        client.connect()

        if not client.is_socket_open():
            msg = f"Couldn't connect to ModbusClient at {self.address}:{self.port}"
            raise KebaModbusClientConnectionError(msg)

        return client

    def _readregister_uint32(self, register: int, regnum: int = 2) -> int:
        """Read `regnum` holding registers starting at `register` as a uint32.

        Returns
        -------
        int
            The decoded uint32 value.

        """
        resp = self.connection.read_holding_registers(
            register, count=regnum, device_id=self.slaveid
        )

        return cast(
            int,
            self.connection.convert_from_registers(
                resp.registers, ModbusClientMixin.DATATYPE.UINT32, word_order="big"
            ),
        )

    def _writeregister_uint16(self, register: int, value: int) -> None:
        """Write a uint16 `value` to a single holding `register`."""
        self.connection.write_register(register, value, device_id=self.slaveid)

    @property
    def charging_state_raw(self) -> int:
        """Raw value of holding register 1000 ("State"). See `ChargingState`."""
        return self._readregister_uint32(1000)

    @property
    def charging_state(self) -> dict:
        """Charging state as `{"state": ChargingState | int, "text": str | None}`.

        `text` is `None` if the raw register value does not map to a known
        `ChargingState` member.
        """
        value = self.charging_state_raw

        try:
            state = ChargingState(value)
        except ValueError:
            return {"state": value, "text": None}

        return {"state": state, "text": _CHARGING_STATE_TEXT[state]}

    @property
    def _cable_state_raw(self) -> int:
        """Raw value of holding register 1004 ("Cable state"). See `CableState`."""
        return self._readregister_uint32(1004)

    @property
    def cable_state(self) -> dict:
        """Cable state as `{"state": CableState | int, "text": str | None}`.

        `text` is `None` if the raw register value does not map to a known
        `CableState` member.
        """
        value = self._cable_state_raw

        try:
            state = CableState(value)
        except ValueError:
            return {"state": value, "text": None}

        return {"state": state, "text": _CABLE_STATE_TEXT[state]}

    @property
    def serial_number(self) -> int:
        """Serial number of the wallbox (holding register 1014)."""
        return self._readregister_uint32(1014)

    @property
    def firmware_version(self) -> str:
        """Firmware version of the wallbox as `"major.minor.subminor"` (register 1018)."""
        val = self._readregister_uint32(1018)

        hexval = f"{val:0>8X}"

        major = int(hexval[0:2], base=16)
        minor = int(hexval[2:4], base=16)
        subminor = int(hexval[4:6], base=16)

        return f"{major}.{minor}.{subminor}"

    @property
    def max_charging_current(self) -> int:
        """Currently configured maximum charging current in A (register 1100)."""
        val = self._readregister_uint32(1100)

        return int(val / 1000)

    @property
    def max_supported_current(self) -> int:
        """Maximum current in A supported by the hardware (register 1110).

        This is the minimum of the DIP switch settings, cable coding and
        temperature monitoring function.
        """
        val = self._readregister_uint32(1110)

        return int(val / 1000)

    @property
    def active_power(self) -> float:
        """Current active power in W (register 1020)."""
        val = self._readregister_uint32(1020)

        val = float(val) / 1000

        return float(f"{val:.2f}")

    @property
    def total_energy(self) -> float:
        """Total energy consumption of the wallbox in kWh (register 1036)."""
        val = self._readregister_uint32(1036)

        val = float(val) / 10000

        return float(f"{val:.2f}")

    @property
    def rfidcard(self) -> str:
        """UID of the last used RFID card, as hex (register 1500)."""
        val = self._readregister_uint32(1500)

        return f"{val:0>8X}"

    @property
    def charged_energy(self) -> float:
        """Energy transferred during the current charging session in kWh (register 1502)."""
        val = self._readregister_uint32(1502)

        val = float(val) / 1000

        return float(f"{val:.2f}")

    ##
    # Writer
    ##
    def set_charging_current(self, current: int) -> None:
        """Set the charging current in A (register 5004).

        Parameters
        ----------
        current : int
            Charging current in A. Must be between 6 and 63.

        Raises
        ------
        KebaModbusClientParamOorError
            If `current` is outside the supported range (6-63).

        """
        if current < 6 or current > 63:
            msg = f"current-value '{current}' out of range (6-63)"
            raise KebaModbusClientParamOorError(msg)

        self._writeregister_uint16(5004, current * 1000)

    def set_charging_kilowatthours(self, kwh: int) -> None:
        """Set the energy limit for the current/next charging session (register 5010).

        Once the transferred energy reaches this value, the charging session
        is terminated.

        Parameters
        ----------
        kwh : int
            Energy limit in units of 0.01 kWh (10 Wh). E.g. `1` terminates the
            session after 10 Wh = 0.01 kWh.

        Raises
        ------
        KebaModbusClientParamOorError
            If `kwh` is smaller than 1.

        """
        if kwh < 1:
            msg = f"kwh-value '{kwh}' cannot below 1"
            raise KebaModbusClientParamOorError(msg)

        self._writeregister_uint16(5010, kwh * 100)

    def unlock_plug(self) -> None:
        """Unlock the plug (register 5012). Only possible while charging is suspended."""
        self._writeregister_uint16(5012, 0)

    def enable_chargingstation(self) -> None:
        """Enable the charging station (register 5014 = 1)."""
        self._writeregister_uint16(5014, 1)

    def disable_chargingstation(self) -> None:
        """Disable the charging station (register 5014 = 0).

        Note: on some wallbox configurations, this does not reliably stop an
        already active charging session over Modbus TCP; see the KEBA
        Modbus TCP Programmers Guide and your wallbox's DIP switch settings
        (in particular DSW2.5, "communication hub mode").
        """
        self._writeregister_uint16(5014, 0)

    ##
    # Output
    ##
    def todict(self) -> dict:
        """Return all wallbox readings as a single dict.

        Returns
        -------
        dict
            All wallbox readings, keyed by name.

        """
        return {
            "chargingState": self.charging_state,
            "firmwareVersion": self.firmware_version,
            "maxSupportedCurrent": self.max_supported_current,
            "maxChargingCurrent": self.max_charging_current,
            "cableState": self.cable_state,
            "serialNumber": self.serial_number,
            "activePower": self.active_power,
            "totalEnergy": self.total_energy,
            "chargedEnergy": self.charged_energy,
            "RFIDcard": self.rfidcard,
        }
