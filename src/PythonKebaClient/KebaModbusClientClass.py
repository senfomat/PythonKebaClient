from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder


class KebaModbusClientConnectionException(Exception):
    pass


class KebaModbusClientParamOorException(Exception):
    pass


class KebaModbusClient:
    """Class docstrings go here.

    Attributes
    ----------
        address : str
            IP-Address or name of the Keba-Client
        port : int, optional
            Modbus-Port of the Keba-Clients. Default: 502
        timeout : int, optional
            Read-Timeout. Default: 10
        slaveid : int, optional
            Keba-Slave-ID: Default: 255 (single-Installation)
        debug: bool, optional
            Debug-Mode for Class and Modbusclient-Module. Default: False

    Methods
    -------
        says(sound=None)
            Prints the animals name and what sound it makes

    Properties
    ----------
        aasd
        asd
        asd
        asd
    """

    __slots__ = ["connection", "address", "port", "timeout", "slaveid", "debug"]

    def __init__(self, **kwargs: dict) -> None:
        """Class method docstrings go here."""

        self.address = kwargs.get("address")
        if not self.address:
            raise ParameterException("'address' not given")

        self.port = kwargs.get("port", 502)
        self.timeout = kwargs.get("timeout", 10)
        self.slaveid = kwargs.get("slaveid", 255)

        self.debug = kwargs.get("debug", False)

        self.connection = self._connect()

    def _connect(self):
        """Tries to connect the Keba-Client via ModBus."""
        client = ModbusTcpClient(self.address, port=self.port, timeout=self.timeout)

        if self.debug:
            client.set_debug(True)

        client.connect()

        if not client.is_socket_open():
            raise KebaModbusClientConnectionException(
                f"Couldn't connect to ModbusClient at {self.address}:{self.port}"
            )

        return client

    def _readregisterUInt32(self, register: int, regnum: int = 2) -> int:
        resp = self.connection.read_holding_registers(register, regnum, unit=self.slaveid)

        decoder = BinaryPayloadDecoder.fromRegisters(
            resp.registers, byteorder=Endian.Big, wordorder=Endian.Big
        )

        return decoder.decode_32bit_uint()

    def _writeregisterUInt16(self, register: int, value: int) -> None:
        val = self.connection.write_register(register, value, unit=self.slaveid)

        return val

    @property
    def chargingStateRaw(self) -> int:
        """

        0: Start-up of the charging station
        1: The charging station is not ready for charging. The charging station is not connected to an electric vehicle, it is locked by the authorization function or another mechanism.
        2: The charging station is ready for charging and waits for a reaction from the electric vehicle.
        3: A charging process is active.
        4: An error has occurred.
        5: The charging process is temporarily interrupted because the temperature is too high or the wallbox is in suspended mode.

        """

        return self._readregisterUInt32(1000)

    @property
    def chargingState(self) -> dict:
        """

        0: Start-up of the charging station
        1: The charging station is not ready for charging. The charging station is not connected to an electric vehicle, it is locked by the authorization function or another mechanism.
        2: The charging station is ready for charging and waits for a reaction from the electric vehicle.
        3: A charging process is active.
        4: An error has occurred.
        5: The charging process is temporarily interrupted because the temperature is too high or the wallbox is in suspended mode.

        """

        value = self.chargingStateRaw

        ret = {"state": value}

        if value == 0:
            ret["text"] = "Start-up of the charging station"
        elif value == 1:
            ret[
                "text"
            ] = "The charging station is not ready for charging. The charging station is not connected to an electric vehicle, it is locked by the authorization function or another mechanism."
        elif value == 2:
            ret[
                "text"
            ] = "The charging station is ready for charging and waits for a reaction from the electric vehicle."
        elif value == 3:
            ret["text"] = "A charging process is active."
        elif value == 4:
            ret["text"] = "An error has occurred."
        elif value == 5:
            ret[
                "text"
            ] = "The charging process is temporarily interrupted because the temperature is too high or the wallbox is in suspended mode."

        return ret

    @property
    def cableStateRaw(self) -> int:
        """ """
        return self._readregisterUInt32(1004)

    @property
    def cableState(self) -> dict:
        """ """
        value = self.cableStateRaw

        ret = {"state": value}

        if value == 0:
            ret["text"] = "No cable is plugged"
        elif value == 1:
            ret[
                "text"
            ] = "Cable is connected to the charging station (not to the electric vehicle)."
        elif value == 3:
            ret[
                "text"
            ] = "Cable is connected to the charging station and locked (not to the electric vehicle)."
        elif value == 5:
            ret[
                "text"
            ] = "Cable is connected to the charging station and the electric vehicle (not locked)."
        elif value == 7:
            ret[
                "text"
            ] = "Cable is connected to the charging station and the electric vehicle and locked (charging)."

        return ret

    @property
    def serialNumber(self) -> int:
        """ """

        return self._readregisterUInt32(1014)

    @property
    def firmwareVersion(self) -> str:
        """ """

        val = self._readregisterUInt32(1018)

        hexval = f"{val:0>8X}"

        major = int(hexval[0:2], base=16)
        minor = int(hexval[2:4], base=16)
        subminor = int(hexval[4:6], base=16)

        return f"{major}.{minor}.{subminor}"

    @property
    def maxChargingCurrent(self) -> int:
        """1100,"""

        val = self._readregisterUInt32(1100)

        val = int(val / 1000)

        return val

    @property
    def maxSupportedCurrent(self) -> int:
        """1110, This register contains the maximum current value that can be supported by
        the hardware of the charging station. This value represents the minimum of
        the DIP switch settings, cable coding and temperature monitoring function."""

        val = self._readregisterUInt32(1110)

        val = int(val / 1000)

        return val

    @property
    def activePower(self) -> str:
        """ """

        val = self._readregisterUInt32(1020)

        val = float(val) / 1000

        return f"{val:.2f}"

    @property
    def totalEnergy(self) -> float:
        """ """

        val = self._readregisterUInt32(1036)

        val = float(val) / 10000

        return f"{val:.2f}"

    @property
    def RFIDcard(self) -> str:
        """ """

        val = self._readregisterUInt32(1500)

        return f"{val:0>8X}"

    @property
    def chargedEnergy(self) -> float:
        """1502, This register contains the transferred energy of the current charging session."""

        val = self._readregisterUInt32(1502)

        val = float(val) / 1000

        return f"{val:.2f}"

    ##
    ## Writer
    ##
    def setChargingCurrent(self, current: int) -> bool:
        """5004, uint16"""

        if 6 < current < 63:
            raise KebaModbusClientParamOorException(
                f"current-value '{current}' out of range (6-63)"
            )

        self._writeregisterUInt16(5004, current * 1000)

        return True

    def setChargingKilowattHours(self, kwh: int):
        """5010, uint16

        In this register, the energy transmission (in 10 watt-hours) for the current or the next charging session can be set. Once this value is reached, the charging session is terminated.

        Value=1: The charging session is terminated after an energy transmission of 10 Wh = 0.01 kWh

        """

        if 1 < kwh:
            raise KebaModbusClientParamOorException(f"kwh-value '{kwh}' cannot below 1")

        return self._writeregisterUInt16(5010, kwh * 100)

    def unlockPlug(self):
        """5012, uint16, 0"""

        return self._writeregisterUInt16(5012, 0)

    def enableChargingStation(self):
        """5014, uint16, 1"""

        return self._writeregisterUInt16(5014, 1)

    def disableChargingStation(self):
        """5014, uint16, 0"""

        return self._writeregisterUInt16(5014, 0)

    ##
    ## Output
    ##
    def todict(self) -> dict:
        """ """

        return {
            "chargingState": self.chargingState,
            "firmwareVersion": self.firmwareVersion,
            "maxSupportedCurrent": self.maxSupportedCurrent,
            "maxChargingCurrent": self.maxChargingCurrent,
            "cableState": self.cableState,
            "serialNumber": self.serialNumber,
            "activePower": self.activePower,
            "totalEnergy": self.totalEnergy,
            "chargedEnergy": self.chargedEnergy,
            "RFIDcard": self.RFIDcard,
        }
