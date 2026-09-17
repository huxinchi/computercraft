# cc_peripherals/fluid_storage.py
from typing import Dict, List, Optional

from ._base import BasePeripheral


__all__ = ('FluidStoragePeripheral', )


class FluidStoragePeripheral(BasePeripheral):
    TYPE = 'fluid_storage'

    def tanks(self) -> Dict[int, dict]:
        """Get all tanks in this fluid storage.
        Returns a sparse table mapping tank index to fluid info.
        Empty tanks are nil — use pairs() semantics."""
        return self._call(b'tanks').take_dict()

    def pushFluid(
        self, toName: str,
        limit: Optional[int] = None,
        fluidName: Optional[str] = None,
    ) -> int:
        """Move fluid to another connected fluid container.
        Returns the amount of fluid moved."""
        return self._call(
            b'pushFluid', toName, limit, fluidName,
        ).take_int()

    def pullFluid(
        self, fromName: str,
        limit: Optional[int] = None,
        fluidName: Optional[str] = None,
    ) -> int:
        """Move fluid from a connected fluid container into this one.
        Returns the amount of fluid moved."""
        return self._call(
            b'pullFluid', fromName, limit, fluidName,
        ).take_int()