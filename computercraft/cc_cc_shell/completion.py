# cc/shell/completion.py
from ..sess import eval_lua

__all__ = ('build_and_set',)


from typing import Dict, Any


def build_and_set(program_path: str, *arg_specs: Dict[str, Any]):
    """在 Lua 侧构建 completion 并注册到 shell。

    arg_specs 每个元素是一个 dict，格式：
      {'fn': 'choice'|'dir'|'file'|'program'|'help'|...,
       'args': [...],       # 传给 fn 的额外参数，如 choice 的 choices
       'many': bool}        # 是否允许多个
    """
    lua_parts = []
    for spec in arg_specs:
        fn = spec['fn']
        if fn in ('choice',):
            lua_parts.append(
                '{completion.' + fn + ', ' + repr(spec['args'][0]) + '}'
            )
        else:
            lua_parts.append(
                '{completion.' + fn + ', many=' + str(spec.get('many', False)).lower() + '}'
            )
    code = (
        'local completion = require("cc.shell.completion")\n'
        'local complete = completion.build(' + ', '.join(lua_parts) + ')\n'
        'shell.setCompletionFunction("' + program_path + '", complete)\n'
    )
    return eval_lua(code.encode('utf-8')).take_none()