# cc_peripherals/redstone_relay.py
from ._base import BasePeripheral


__all__ = ('RedstoneRelayPeripheral', )


class RedstoneRelayPeripheral(BasePeripheral):
    TYPE = 'redstone_relay'

    def setOutput(self, side: str, on: bool) -> None:
        """Turn the redstone signal of a specific side on or off."""
        return self._call(b'setOutput', side, on).take_none()

    def getOutput(self, side: str) -> bool:
        """Get the current redstone output of a specific side."""
        return self._call(b'getOutput', side).take_bool()

    def getInput(self, side: str) -> bool:
        """Get the current redstone input of a specific side."""
        return self._call(b'getInput', side).take_bool()

    def setAnalogOutput(self, side: str, value: int) -> None:
        """Set the redstone signal strength for a specific side."""
        return self._call(b'setAnalogOutput', side, value).take_none()

    def setAnalogueOutput(self, side: str, value: int) -> None:
        """British spelling alias of setAnalogOutput."""
        return self.setAnalogOutput(side, value)

    def getAnalogOutput(self, side: str) -> int:
        """Get the redstone output signal strength for a specific side."""
        return self._call(b'getAnalogOutput', side).take_int()

    def getAnalogueOutput(self, side: str) -> int:
        """British spelling alias of getAnalogOutput."""
        return self.getAnalogOutput(side)

    def getAnalogInput(self, side: str) -> int:
        """Get the redstone input signal strength for a specific side."""
        return self._call(b'getAnalogInput', side).take_int()

    def getAnalogueInput(self, side: str) -> int:
        """British spelling alias of getAnalogInput."""
        return self.getAnalogInput(side)

    def setBundledOutput(self, side: str, output: int) -> None:
        """Set the bundled cable output for a specific side."""
        return self._call(b'setBundledOutput', side, output).take_none()

    def getBundledOutput(self, side: str) -> int:
        """Get the bundled cable output for a specific side."""
        return self._call(b'getBundledOutput', side).take_int()

    def getBundledInput(self, side: str) -> int:
        """Get the bundled cable input for a specific side."""
        return self._call(b'getBundledInput', side).take_int()

    def testBundledInput(self, side: str, mask: int) -> bool:
        """Test if specific colours are on for the given side."""
        return self._call(b'testBundledInput', side, mask).take_bool()