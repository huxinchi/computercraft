# cc/strings.py
from typing import List, Optional
from ..sess import eval_lua

__all__ = ('wrap', 'ensure_width', 'split')


def wrap(text: str, width: Optional[int] = None) -> List[str]:
    """Wrap text so each line fits within width.
    Defaults to terminal width."""
    return eval_lua(b'''
local m = require("cc.strings")
return m.wrap(...)
''', text, width).take_list_of_strings()


def ensure_width(line: str, width: Optional[int] = None) -> str:
    """Truncate or pad line to a fixed width."""
    return eval_lua(b'''
local m = require("cc.strings")
return m.ensure_width(...)
''', line, width).take_string()


def split(
    s: str, deliminator: str,
    plain: Optional[bool] = None, limit: Optional[int] = None,
) -> List[str]:
    """Split a string into parts.
    By default deliminator is a Lua pattern; pass plain=True for literal."""
    return eval_lua(b'''
local m = require("cc.strings")
return m.split(...)
''', s, deliminator, plain, limit).take_list_of_strings()