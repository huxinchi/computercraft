# cc/expect.py
from ..sess import eval_lua
from typing import Optional

__all__ = ('expect', 'field', 'range')


def expect(index: int, value, *types: str):
    """Expect value to be one of the given Lua types.
    Returns value on success, raises LuaException on failure."""
    return eval_lua(b'''
local m = require("cc.expect")
return m.expect(...)
''', index, value, *types).take()


def field(tbl: dict, index: str, *types: str):
    """Expect tbl[index] to be one of the given types."""
    return eval_lua(b'''
local m = require("cc.expect")
return m.field(...)
''', tbl, index, *types).take()


def range(num: float, min: Optional[float] = None, max: Optional[float] = None) -> float:
    """Expect num to be within [min, max]."""
    return eval_lua(b'''
local m = require("cc.expect")
return m.range(...)
''', num, min, max).take_number()