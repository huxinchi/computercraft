# cc/colours.py
from typing import List

from ..sess import eval_lua


__all__ = (
    'white', 'orange', 'magenta', 'lightBlue',
    'yellow', 'lime', 'pink', 'grey',       # 英式：grey
    'lightGrey', 'cyan', 'purple', 'blue',
    'brown', 'green', 'red', 'black',
    'combine', 'subtract', 'test',
    'packRGB', 'unpackRGB',
    'toBlit', 'fromBlit',
    'chars', 'iter_colors',
)


white = 0x1
orange = 0x2
magenta = 0x4
lightBlue = 0x8
yellow = 0x10
lime = 0x20
pink = 0x40
grey = 0x80          # 英式拼写
lightGrey = 0x100    # 英式拼写
cyan = 0x200
purple = 0x400
blue = 0x800
brown = 0x1000
green = 0x2000
red = 0x4000
black = 0x8000


def combine(*colors: int) -> int:
    return eval_lua(b'G:colours:M:combine', *colors).take_int()


def subtract(color_set: int, *colors: int) -> int:
    return eval_lua(b'G:colours:M:subtract', color_set, *colors).take_int()


def test(colors: int, color: int) -> bool:
    return eval_lua(b'G:colours:M:test', colors, color).take_bool()


def packRGB(r: float, g: float, b: float) -> int:
    return eval_lua(b'G:colours:M:packRGB', r, g, b).take_int()


def unpackRGB(rgb: int) -> tuple:
    rp = eval_lua(b'G:colours:M:unpackRGB', rgb)
    return tuple(rp.take_number() for _ in range(3))


def toBlit(color: int) -> str:
    """Convert a colour to its blit hex character (0-9a-f).
    New in version 1.94.0."""
    return eval_lua(b'G:colours:M:toBlit', color).take_string()


def fromBlit(hex_char: str) -> int:
    """Convert a blit hex character (0-9a-f) to a colour.
    New in version 1.105.0."""
    return eval_lua(b'G:colours:M:fromBlit', hex_char).take_int()


# 英式 blit 字符映射
chars = {
    '0': white, '1': orange, '2': magenta, '3': lightBlue,
    '4': yellow, '5': lime, '6': pink, '7': grey,
    '8': lightGrey, '9': cyan, 'a': purple, 'b': blue,
    'c': brown, 'd': green, 'e': red, 'f': black,
}


def iter_colors():
    for c in chars.values():
        yield c