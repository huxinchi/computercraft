# computercraft/cc/coroutine.py
from typing import Any, List,Union

from ..errors import LuaException
from ..lua import LuaFunction, LuaThread
from ..sess import eval_lua
__all__ = (
    'create',
    'resume',
    'yield_',
    'status',
    'running',
    'isyieldable',
    'wrap',
)


def create(func: LuaFunction) -> LuaThread:
    return eval_lua(b'return coroutine.create(...)', func).take_decoded()


def status(co: LuaThread) -> str:
    return eval_lua(b'return coroutine.status(...)', co).take_decoded()


def running():
    """返回 (当前 coroutine, 是否主 coroutine)。

    Lua 5.1 下主线程没有 coroutine，只返回 nil——这时 is_main 视为 True。
    Lua 5.2+ 下返回 (co, is_main)。
    """
    rp = eval_lua(b'''
    local a, b = coroutine.running()
    if b == nil then
        return a, a == nil
    end
    return a, b
    ''')
    co = rp.take_decoded()
    is_main = rp.take_bool()
    return co, is_main


def isyieldable() -> bool:
    return eval_lua(b'return coroutine.isyieldable()').take_decoded()


def wrap(func: LuaFunction) -> LuaFunction:
    return eval_lua(b'return coroutine.wrap(...)', func).take_decoded()


def resume(co: LuaThread, *args: Any) -> List[Any]:
    """恢复 co，返回 Lua 侧所有返回值。

    """
    rp = eval_lua(b'return coroutine.resume(...)', co, *args)
    values = []
    while not rp.isend():
        values.append(rp.take_decoded())
    return values