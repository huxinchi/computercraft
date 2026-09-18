# cc/base64.py
from ..sess import eval_lua
from typing import Optional

__all__ = ('encode', 'decode')


def encode(data: str, alt_chars: Optional[str] = None) -> str:
    """Encode binary data to Base64.
    alt_chars is a 2-char string, default '+/'."""
    return eval_lua(b'''
local m = require("cc.base64")
return m.encode(...)
''', data, alt_chars).take_string()


def decode(data: str, alt_chars: Optional[str] = None)->str:
    """Decode Base64. Returns str, or raises LuaException on invalid input."""
    return eval_lua(b'''
local m = require("cc.base64")
return m.decode(...)
''', data, alt_chars).take_string()