# cc/require.py
from ..sess import eval_lua

__all__ = ('make',)


def make(env: dict, dir: str) -> dict:
    """Build a package library and require function for env.
    Returns a table containing the new require and package."""
    return eval_lua(b'''
local m = require("cc.require")
return m.make(...)
''', env, dir).take_dict()