# cc/image/nft.py
from typing import Optional
from ..sess import eval_lua

__all__ = ('parse', 'load', 'draw')


def parse(image: str) -> dict:
    """Parse an nft image from a string. Returns the parsed image table."""
    return eval_lua(b'''
local m = require("cc.image.nft")
return m.parse(...)
''', image).take_dict()


def load(path: str) -> Optional[dict]:
    """Load an nft image from a file.
    Returns None if the file doesn't exist or can't be loaded."""
    rp = eval_lua(b'''
local m = require("cc.image.nft")
local img, err = m.load(...)
if img == nil then return nil, err end
return img
''', path)
    if rp.peek() is None:
        rp.take()
        return None
    return rp.take_dict()


def draw(image: dict, xPos: int, yPos: int, target=None) -> None:
    """Draw an nft image. target is a term.Redirect."""
    return eval_lua(b'''
local m = require("cc.image.nft")
return m.draw(...)
''', image, xPos, yPos, target).take_none()