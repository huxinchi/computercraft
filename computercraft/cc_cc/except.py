# cc/expect.py
from ..sess import eval_lua


__all__ = ('expect', 'field', 'range')


from typing import Dict, TypeVar, Optional

T = TypeVar('T')


def expect(index: int, value: T, *types: str) -> T:
    """Expect value to be one of the given Lua types.

    Returns value unchanged on success; raises LuaException on failure.
    """
    return eval_lua(b'''
local m = require("cc.expect")
return m.expect(...)
''', index, value, *types).take()


def field(tbl: Dict[str, T], index: str, *types: str) -> T:
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