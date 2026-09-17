# cc_peripherals/energy_storage.py
from ._base import BasePeripheral


__all__ = ('EnergyStoragePeripheral', )


class EnergyStoragePeripheral(BasePeripheral):
    TYPE = 'energy_storage'

    def getEnergy(self) -> int:
        """Get the energy stored in this block, in FE."""
        return self._call(b'getEnergy').take_int()

    def getEnergyCapacity(self) -> int:
        """Get the maximum amount of energy this block can store, in FE."""
        return self._call(b'getEnergyCapacity').take_int()