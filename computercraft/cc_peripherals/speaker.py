from ._base import BasePeripheral
from typing import Optional


__all__ = ('SpeakerPeripheral', )


class SpeakerPeripheral(BasePeripheral):
    TYPE = 'speaker'

    def playNote(
        self, instrument: str, volume: int = 1, pitch: int = 1,
    ) -> bool:
        # instrument:
        # https://minecraft.gamepedia.com/Note_Block#Instruments
        # bass
        # basedrum
        # bell
        # chime
        # flute
        # guitar
        # hat
        # snare
        # xylophone
        # iron_xylophone
        # pling
        # banjo
        # bit
        # didgeridoo
        # cow_bell

        # volume 0..3
        # pitch 0..24
        return self._call(b'playNote', instrument, volume, pitch).take_bool()

    def playSound(self, sound: str, volume: int = 1, pitch: int = 1) -> bool:
        # volume 0..3
        # pitch 0..2
        return self._call(b'playSound', sound, volume, pitch).take_bool()
    def playAudio(self, audio: bytes, volume: Optional[float] = None) -> bool:
        """Attempt to stream some audio data to the speaker.
        This accepts a list of audio samples as a byte buffer.
        Returns: boolean (whether the audio could be played)."""
        return self._call(b'playAudio', audio, volume).take_bool()

    def stop(self) -> None:
        """Stop all audio being played by this speaker."""
        return self._call(b'stop').take_none()