from typing import Optional, List, Union

from .. import ser
from ..lua import LuaNum
from ..sess import eval_lua


__all__ = (
    'slowWrite', 'slowPrint',
    'formatTime', 'tabulate', 'pagedTabulate', 'pagedPrint',
    'serialize', 'unserialize',
    'serializeJSON', 'unserializeJSON',
    'urlEncode', 'splitString',
    'empty_json_array', 'json_null',
    'complete',
)

# JSON 空数组和空对象的区分标记
empty_json_array = eval_lua(b'return textutils.empty_json_array').take()
json_null = eval_lua(b'return textutils.json_null').take()


def serialize(t, opts: Optional[dict] = None) -> str:
    return eval_lua(b'G:textutils:M:serialize', t, opts).take_string()


def unserialize(s: str):
    return eval_lua(b'G:textutils:M:unserialize', s).take()


def serializeJSON(*args) -> str:
    return eval_lua(b'G:textutils:M:serializeJSON', *args).take_string()


def unserializeJSON(s: str, options: Optional[dict] = None):
    return eval_lua(b'G:textutils:M:unserializeJSON', s, options).take()


def urlEncode(s: str) -> str:
    return eval_lua(
        b'G:textutils:M:urlEncode', ser.cc_dirty_encode(s),
    ).take_string()


def splitString(s: str) -> List[str]:
    """Split a string into a list of lines.
    New in version 1.110.0."""
    return eval_lua(
        b'G:textutils:M:splitString', ser.cc_dirty_encode(s),
    ).take_list_of_strings()


def slowWrite(text: str, rate: Optional[LuaNum] = None) -> None:
    return eval_lua(
        b'G:textutils:M:slowWrite', ser.cc_dirty_encode(text), rate,
    ).take_none()


def slowPrint(text: str, rate: Optional[LuaNum] = None) -> None:
    return eval_lua(
        b'G:textutils:M:slowPrint', ser.cc_dirty_encode(text), rate,
    ).take_none()


def formatTime(time: LuaNum, twentyFourHour: Optional[bool] = None) -> str:
    return eval_lua(
        b'G:textutils:M:formatTime', time, twentyFourHour,
    ).take_string()


def _prepareTab(rows_and_colors):
    r = []
    for item in rows_and_colors:
        if isinstance(item, int):
            r.append(item)
        else:
            r.append([ser.cc_dirty_encode(x) for x in item])
    return r


def tabulate(*rows_and_colors: Union[List[str], int]) -> None:
    return eval_lua(
        b'G:textutils:M:tabulate', *_prepareTab(rows_and_colors),
    ).take_none()


def pagedTabulate(*rows_and_colors: Union[List[str], int]) -> None:
    return eval_lua(
        b'G:textutils:M:pagedTabulate', *_prepareTab(rows_and_colors),
    ).take_none()


def pagedPrint(text: str, freeLines: Optional[int] = None) -> int:
    return eval_lua(
        b'G:textutils:M:pagedPrint', ser.cc_dirty_encode(text), freeLines,
    ).take_int()


def complete(partial: str, possible: List[str]) -> List[str]:
    return [p[len(partial):] for p in possible if p.startswith(partial)]


