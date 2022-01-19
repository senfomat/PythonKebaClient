#!/usr/bin/env python3.10

from KebaModbusClientClass import KebaModbusClient

# import logging
# logging.basicConfig()
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

k = KebaModbusClient(address="192.168.161.103")
print(k.chargingState)
print(k.serialNumber)
print(k.cableState)
print(k.activePower)
print(k.totalEnergy)
