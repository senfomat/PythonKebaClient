from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder


class KebaModbusClient:
    __slots__ = ["address", "port", "timeout", "slaveid", "debug"]

    def __init__(self, **kwargs):
        self.address = kwargs.get("address")
        if not self.address:
            raise ParameterException("'address' not given")

        self.port = kwargs.get("port", 502)
        self.timeout = kwargs.get("timeout", 10)
        self.slaveid = 255

        self.debug = kwargs.get("debug", False)

    def _connect(self):
        client = ModbusTcpClient(self.address, port=self.port, timeout=self.timeout)

        if self.debug:
            client.set_debug(True)

        client.connect()

        if client.is_socket_open():
            return client
        else:
            raise Exception("Fehler")

    def _readregister(self, register, regnum=2):
        client = self._connect()

        resp = client.read_holding_registers(register, regnum, unit=self.slaveid)

        decoder = BinaryPayloadDecoder.fromRegisters(
            resp.registers, byteorder=Endian.Big, wordorder=Endian.Big
        )

        return decoder.decode_32bit_uint()

    @property
    def chargingState(self):
        return self._readregister(1000)

    @property
    def chargingState(self):
        return self._readregister(1000)

    @property
    def cableState(self):
        cableState = self._readregister(1004)

        ret = {"state": cableState}

        if cableState == 0:
            ret["text"] = "No cable is plugged"
        elif cableState == 1:
            ret[
                "text"
            ] = "Cable is connected to the charging station (not to the electric vehicle)."
        elif cableState == 3:
            ret[
                "text"
            ] = "Cable is connected to the charging station and locked (not to the electric vehicle)."
        elif cableState == 5:
            ret[
                "text"
            ] = "Cable is connected to the charging station and the electric vehicle (not locked)."
        elif cableState == 7:
            ret[
                "text"
            ] = "Cable is connected to the charging station and the electric vehicle and locked (charging)."

        return ret

    @property
    def serialNumber(self):
        return self._readregister(1014)

    @property
    def activePower(self):
        val = self._readregister(1020)

        val = float(val) / 1000

        return f"{val:.2f}"

    @property
    def totalEnergy(self):
        val = self._readregister(1036)

        val = float(val) / 10000

        return f"{val:.2f}"
