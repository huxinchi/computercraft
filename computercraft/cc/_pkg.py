# cc/_pkg.py
from types import ModuleType
from typing import Any, List, Optional

from .. import ser
from ..errors import LuaException
from ..lua import LuaNum,LuaFunction,LuaObject,LuaThread
from ..sess import eval_lua,register_route, unregister_route, list_routes

__all__ = (
    'import_file',
    'is_commands',
    'is_multishell',
    'is_turtle',
    'is_pocket',
    'eval_lua',
    'LuaException',
    'sleep',
    'write',
    'print',
    'printError',
    'read',
    'LuaFunction',
    'register_route',
    'unregister_route',
    'list_routes',
    'LuaObject',
    'LuaThread',
)


def import_file(path: str, relative_to: Optional[str] = None):
    source = eval_lua(b'''
local p, rel = ...
if rel ~= nil then
p = fs.combine(fs.getDir(rel), p)
end
if not fs.exists(p) then return nil end
if fs.isDir(p) then return nil end
f = fs.open(p, "r")
local src = f.readAll()
f.close()
return src
'''.strip(), path, relative_to).take_option_string()
    if source is None:
        raise ImportError('File not found: {}'.format(path))
    mod = ModuleType(path)
    mod.__file__ = path
    cc = compile(source, mod.__name__, 'exec')
    exec(cc, vars(mod))
    return mod


def is_commands() -> bool:
    return eval_lua(b'return commands ~= nil').take_bool()


def is_multishell() -> bool:
    return eval_lua(b'return multishell ~= nil').take_bool()


def is_turtle() -> bool:
    return eval_lua(b'return turtle ~= nil').take_bool()


def is_pocket() -> bool:
    return eval_lua(b'return pocket ~= nil').take_bool()


# ---------- _G 全局环境（bios.lua）绑定 ----------
# https://tweaked.cc/module/_G.html

def sleep(time: LuaNum = 0) -> None:
    """Pause execution for the specified number of seconds.

    Time is rounded up to the nearest multiple of 0.05 s. Only pauses
    the current thread. Events during sleep are discarded.
    """
    return eval_lua(b'sleep(...)', time).take_none()


def write(text: str) -> int:
    """Write text to the screen without a trailing newline.

    Returns the number of lines written.
    """
    return eval_lua(
        b'return write(...)', ser.cc_dirty_encode(text),
    ).take_int()


def print(*args: Any) -> int:
    """Print values to the screen, separated by spaces.

    Returns the number of lines written.

    Note: shadows the Python builtin when imported as
    ``from cc import print``. Use ``import cc; cc.print(...)`` if you
    need the builtin.
    """
    return eval_lua(b'return print(...)', *args).take_int()


def printError(*args: Any) -> int:
    """Print values to the screen in red.

    Returns the number of lines written.
    """
    return eval_lua(b'return printError(...)', *args).take_int()


def read(
    replace_char: Optional[str] = None,
    history: Optional[List[str]] = None,
    default: Optional[str] = None,
) -> str:
    """Read user input from the terminal.

    :param replace_char: Character to display in place of typed input
        (for passwords, pass ``"*"``).
    :param history: List of history items for up/down arrow scrolling.
        Oldest item is at index 0.
    :param default: Default text pre-filled into the prompt.

    Note: CC:T's ``read`` also accepts a ``completeFn`` parameter in
    the 3rd position. The current serialization protocol cannot pass
    Lua functions, so that argument is not exposed here.
    """
    return eval_lua(
        b'return read(...)', replace_char, history, None, default,
    ).take_string()


def __getattr__(name):
    """PEP 562: expose _HOST and _CC_DEFAULT_SETTINGS on attribute access.

    They are module-level variables on the Lua side, not functions,
    so we proxy them lazily. Deliberately not in __all__, so
    ``from cc import *`` does not trigger a Lua round-trip.
    """
    if name == '_HOST':
        return eval_lua(b'return _HOST').take_string()
    if name == '_CC_DEFAULT_SETTINGS':
        return eval_lua(b'return _CC_DEFAULT_SETTINGS').take_string()
    raise AttributeError(
        'module {!r} has no attribute {!r}'.format(__name__, name),
    )