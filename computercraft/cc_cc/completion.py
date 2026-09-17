# cc/completion.py
from typing import Optional, List
from ..sess import eval_lua

__all__ = ('choice', 'peripheral', 'side', 'setting', 'command')


def choice(text: str, choices: List[str], add_space: Optional[bool] = None) -> List[str]:
    return eval_lua(b'''
local m = require("cc.completion")
return m.choice(...)
''', text, choices, add_space).take_list_of_strings()


def peripheral(text: str, add_space: Optional[bool] = None) -> List[str]:
    return eval_lua(b'''
local m = require("cc.completion")
return m.peripheral(...)
''', text, add_space).take_list_of_strings()


def side(text: str, add_space: Optional[bool] = None) -> List[str]:
    return eval_lua(b'''
local m = require("cc.completion")
return m.side(...)
''', text, add_space).take_list_of_strings()


def setting(text: str, add_space: Optional[bool] = None) -> List[str]:
    return eval_lua(b'''
local m = require("cc.completion")
return m.setting(...)
''', text, add_space).take_list_of_strings()


def command(text: str, add_space: Optional[bool] = None) -> List[str]:
    return eval_lua(b'''
local m = require("cc.completion")
return m.command(...)
''', text, add_space).take_list_of_strings()