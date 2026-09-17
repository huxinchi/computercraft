from typing import Optional, Any, List

from .. import ser
from ..sess import eval_lua


__all__ = (
    'define',
    'undefine',
    'getDetails',
    'set',
    'get',
    'unset',
    'clear',
    'getNames',
    'load',
    'save',
)


def define(
    name: str,
    description: Optional[str] = None,
    default: Optional[Any] = None,
    value_type: Optional[str] = None,
) -> None:
    options = {}
    if description is not None:
        options[b'description'] = description
    if default is not None:
        options[b'default'] = default
    if value_type is not None:
        options[b'type'] = value_type
    return eval_lua(b'G:settings:M:define', name, options).take_none()


def undefine(name: str) -> None:
    return eval_lua(b'G:settings:M:undefine', name).take_none()


def getDetails(name: str) -> dict:
    return eval_lua(b'G:settings:M:getDetails', name).take_dict()


def set(name: str, value: Any) -> None:
    return eval_lua(b'G:settings:M:set', name, value).take_none()


def get(name: str, default: Optional[Any] = None) -> Any:
    r = eval_lua(b'G:settings:M:get', name, default).take()
    return r.decode(ser._CC_ENC) if isinstance(r, bytes) else r


def unset(name: str) -> None:
    return eval_lua(b'G:settings:M:unset', name).take_none()


def clear() -> None:
    return eval_lua(b'G:settings:M:clear').take_none()


def getNames() -> List[str]:
    return eval_lua(b'G:settings:M:getNames').take_list_of_strings()


def load(path: Optional[str] = None) -> bool:
    return eval_lua(b'G:settings:M:load', path).take_bool()


def save(path: Optional[str] = None) -> bool:
    return eval_lua(b'G:settings:M:save', path).take_bool()
