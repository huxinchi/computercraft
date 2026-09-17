# cc/audio/dfpwm.py
from ..lua import LuaFunction
from ..sess import eval_lua


__all__ = ('encode', 'decode', 'make_encoder', 'make_decoder')


def encode(input: list) -> bytes:
    """Encode a complete PCM sample list into a DFPWM byte string.

    :param input: PCM sample list (integers, typically -128..127).
    :return: DFPWM-encoded bytes.
    """
    return eval_lua(
        b'local m = require("cc.audio.dfpwm")\n'
        b'return m.encode(...)',
        input,
    ).take_bytes()


def decode(input: bytes) -> list:
    """Decode a complete DFPWM byte string into a PCM sample list.

    :param input: DFPWM-encoded bytes.
    :return: PCM sample list.
    """
    return eval_lua(
        b'local m = require("cc.audio.dfpwm")\n'
        b'return m.decode(...)',
        input,
    ).take_list()


def make_encoder() -> LuaFunction:
    """Create a streaming DFPWM encoder.

    Returns a LuaFunction that takes a PCM sample list and returns the
    corresponding DFPWM byte string. The encoder keeps internal state
    across calls, so feed the input in the same order as playback.
    """
    return eval_lua(
        b'local m = require("cc.audio.dfpwm")\n'
        b'return m.make_encoder()'
    ).take_decoded()


def make_decoder() -> LuaFunction:
    """Create a streaming DFPWM decoder.

    Returns a LuaFunction that takes a DFPWM byte string and returns a
    PCM sample list. The decoder keeps internal state across calls, so
    feed the input in the same order as playback.
    """
    return eval_lua(
        b'local m = require("cc.audio.dfpwm")\n'
        b'return m.make_decoder()'
    ).take_decoded()