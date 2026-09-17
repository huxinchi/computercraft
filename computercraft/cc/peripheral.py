import inspect
from typing import Any, Dict, List, Optional, Type, TypeVar

from ..lua import LuaObject
from ..sess import eval_lua
from ..cc_peripherals import register_std_peripherals
from ..cc_peripherals._base import BasePeripheral


__all__ = (
    'UnknownPeripheralError',
    'isPresent', 'getType', 'getNames',
    'hasType', 'getMethods',
    'wrap', 'find', 'registerType',
)


P = TypeVar('P', bound=BasePeripheral)
type_map: Dict[str, Type[BasePeripheral]] = {}


class UnknownPeripheralError(TypeError):
    pass




def hasType(side: str, peripheral_type: str) -> bool:
    """..."""
    return eval_lua(
        b'G:peripheral:M:hasType', side, peripheral_type,
    ).take_bool()


def getMethods(side: str) -> List[str]:
    """..."""
    return eval_lua(
        b'G:peripheral:M:getMethods', side,
    ).take_list_of_strings()


def find(peripheral_type: str) -> List[str]:
    """..."""
    return eval_lua(
        b'G:peripheral:M:find', peripheral_type,
    ).take_list_of_strings()


def isPresent(side: str) -> bool:
    return eval_lua(b'G:peripheral:M:isPresent', side).take_bool()


def getType(side: str) -> Optional[str]:
    return eval_lua(b'G:peripheral:M:getType', side).take_option_string()


def getNames() -> List[str]:
    return eval_lua(b'G:peripheral:M:getNames').take_list_of_strings()





def wrap(side: str):
    """Wrap the peripheral on the given side.

    - Known type: returns the registered Python peripheral class.
    - Unknown type: returns a LuaObject that proxies method calls
      through the Lua-side metatable. No Python-side stub, but works.
    - No peripheral on the side: returns None.
    """
    ptype = getType(side)
    if ptype is None:
        return None

    cls = type_map.get(ptype)
    if cls is None:
        # 未注册类型：直接让 Lua 返回带 metatable 的 wrapper，
        # 序列化时会被引用化成 LuaObject，方法调用走 metatable 动态解析。
        return eval_lua(b'return peripheral.wrap(...)', side).take()

    if inspect.isclass(cls):
        return cls(side)
    else:
        def _call(method, *args):
            return eval_lua(b'G:peripheral:M:call', side, method, *args)
        return cls(side, ptype, _call)


def registerType(peripheralType: str, pcls: Type[P]) -> None:
    type_map[peripheralType] = pcls


register_std_peripherals(registerType)