# cc/pretty.py
from typing import Optional, Any
from ..sess import eval_lua

__all__ = (
    'empty', 'space', 'line', 'space_line',
    'text', 'concat', 'nest', 'group',
    'write', 'print', 'render',
    'pretty', 'pretty_print',
)


def text(s: str, color: Optional[str] = None) -> dict:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.text(...)
''', s, color).take_dict()


def concat(*docs) -> dict:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.concat(...)
''', *docs).take_dict()


def nest(depth: int, doc: dict) -> dict:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.nest(...)
''', depth, doc).take_dict()


def group(doc: dict) -> dict:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.group(...)
''', doc).take_dict()


def write(doc: dict, ribbon_frac: float = 0.6) -> None:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.write(...)
''', doc, ribbon_frac).take_none()


def print(doc: dict, ribbon_frac: float = 0.6) -> None:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.print(...)
''', doc, ribbon_frac).take_none()


def render(doc: dict, width: Optional[int] = None, ribbon_frac: float = 0.6) -> str:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.render(...)
''', doc, width, ribbon_frac).take_string()


def pretty(obj: Any, options: Optional[dict] = None) -> dict:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.pretty(...)
''', obj, options).take_dict()


def pretty_print(obj: Any, options: Optional[dict] = None, ribbon_frac: float = 0.6) -> None:
    return eval_lua(b'''
local m = require("cc.pretty")
return m.pretty_print(...)
''', obj, options, ribbon_frac).take_none()