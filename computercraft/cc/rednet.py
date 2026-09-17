# cc/rednet.py
import sys
from types import ModuleType
from typing import Any, List, Optional, Tuple, Union

from ..lua import LuaNum
from ..sess import eval_lua


# 注意：CHANNEL_BROADCAST / CHANNEL_REPEAT / MAX_ID_CHANNELS
# 故意不放在 __all__ 里。它们是动态代理，import * 时不应触发。
# 使用时请显式 rednet.CHANNEL_BROADCAST。
__all__ = (
    'open', 'close', 'send', 'broadcast', 'receive',
    'isOpen', 'host', 'unhost', 'lookup',
)


# ---------- 函数 API ----------

def open(side: str) -> None:
    return eval_lua(b'G:rednet:M:open', side).take_none()


def close(side: Optional[str] = None) -> None:
    return eval_lua(b'G:rednet:M:close', side).take_none()


def send(receiverID: int, message: Any, protocol: Optional[str] = None) -> bool:
    return eval_lua(
        b'G:rednet:M:send', receiverID, message, protocol,
    ).take_bool()


def broadcast(message: Any, protocol: Optional[str] = None) -> None:
    return eval_lua(b'G:rednet:M:broadcast', message, protocol).take_none()


def receive(
    protocolFilter: Optional[str] = None, timeout: Optional[LuaNum] = None,
) -> Optional[Tuple[int, Any, Optional[str]]]:
    rp = eval_lua(b'G:rednet:M:receive', protocolFilter, timeout)
    if rp.peek() is None:
        return None
    return (rp.take_int(), rp.take(), rp.take_option_string())


def isOpen(side: Optional[str] = None) -> bool:
    return eval_lua(b'G:rednet:M:isOpen', side).take_bool()


def host(protocol: str, hostname: str) -> None:
    return eval_lua(b'G:rednet:M:host', protocol, hostname).take_none()


def unhost(protocol: str) -> None:
    return eval_lua(b'G:rednet:M:unhost', protocol).take_none()


def lookup(
    protocol: str, hostname: Optional[str] = None,
) -> Union[Optional[int], List[int]]:
    rp = eval_lua(b'G:rednet:M:lookup', protocol, hostname)
    if hostname is None:
        r = []
        while rp.peek() is not None:
            r.append(rp.take_int())
        return r
    else:
        return rp.take_option_int()


# ---------- 可变常量代理 ----------

class _RednetModule(ModuleType):
    _PROXIED = frozenset({
        'CHANNEL_BROADCAST',
        'CHANNEL_REPEAT',
        'MAX_ID_CHANNELS',
    })

    _DEFAULTS = {
        'CHANNEL_BROADCAST': 65535,
        'CHANNEL_REPEAT': 65533,
        'MAX_ID_CHANNELS': 65500,
    }

    def __getattr__(self, name):
        if name in _RednetModule._PROXIED:
            key = b'"' + name.encode('ascii') + b'"'
            try:
                rp = eval_lua(b'return rednet[' + key + b']')
            except RuntimeError as e:
                raise RuntimeError(
                    'rednet.{!r} can only be read inside a '
                    'Computercraft session'.format(name)
                ) from e
            if rp.peek() is None:
                return _RednetModule._DEFAULTS[name]
            return rp.take_int()

        raise AttributeError(
            'module {!r} has no attribute {!r}'.format(self.__name__, name),
        )

    def __setattr__(self, name, value):
        if name in _RednetModule._PROXIED:
            key = b'"' + name.encode('ascii') + b'"'
            try:
                eval_lua(
                    b'rednet[' + key + b'] = ...',
                    value,
                ).take_none()
            except RuntimeError as e:
                raise RuntimeError(
                    'rednet.{!r} can only be assigned inside a '
                    'Computercraft session'.format(name)
                ) from e
            return
        super().__setattr__(name, value)

# 关键一行：把当前模块的 class 换成上面这个子类
sys.modules[__name__].__class__ = _RednetModule