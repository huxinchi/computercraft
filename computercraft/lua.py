from typing import Union
LuaTable = Union[list, dict]
LuaNum = Union[int, float]
import types
DUNDER_TO_MT = {
    '__call__':    '__call',
    '__str__':     '__tostring',
    '__len__':     '__len',
    '__eq__':      '__eq',
    '__lt__':      '__lt',
    '__le__':      '__le',
    '__add__':     '__add',
    '__sub__':     '__sub',
    '__mul__':     '__mul',
    '__truediv__': '__div',
    '__mod__':     '__mod',
    '__pow__':     '__pow',
    '__neg__':     '__unm',
    '__and__':     '__band',
    '__or__':      '__bor',
    '__xor__':     '__bxor',
    '__lshift__':  '__shl',
    '__rshift__':  '__shr',
    '__invert__':  '__bnot',
}
_FUNCTION_TYPES = (
    types.FunctionType,
    types.LambdaType,
    types.BuiltinFunctionType,
    types.MethodType,
    types.BuiltinMethodType,
)
def is_function(v):
    return isinstance(v, _FUNCTION_TYPES)
def _make_handler(obj, dunder):
    method = getattr(obj, dunder)
    def handler(_, *args):
        return method(*args)
    return handler
def _getattr_handler(obj):
    def handler(_, k):
        return getattr(obj, k, None)
    return handler
def _setattr_handler(obj):
    def handler(_, k, v):
        setattr(obj, k, v)
    return handler
def _has_dunder(t, name):
    """t 是否"自己"定义了 dunder（不含 object 的默认实现）。"""
    for klass in t.__mro__:
        if klass is object:
            return False
        if name in klass.__dict__:
            return True
    return False
def make_mt_spec(obj):
    t = type(obj)
    mt = {
        '__index':    _getattr_handler(obj),
        '__newindex': _setattr_handler(obj),
    }
    for dunder, mt_key in DUNDER_TO_MT.items():
        if _has_dunder(t, dunder):
            mt[mt_key] = _make_handler(obj, dunder)
    return mt
def _collect(rp):
    values = []
    while not rp.isend():
        values.append(rp.take_decoded())
    if len(values) == 0:
        return None
    if len(values) == 1:
        return values[0]
    return tuple(values)
class LuaExpr:
    def get_expr_code(self):
        raise NotImplementedError
class TempObject:
    def __init__(self, fid: bytes):
        self._fid = fid
class _LuaRefMixin:
    __slots__ = ('_fid', '_closed', '_str_cache')
    def __init__(self, fid: int):
        self._fid = fid
        self._closed = False
        self._str_cache = None
    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            from .sess import get_current_session
            sess = get_current_session()
        except Exception:
            return
        sess._pending_luaobj_free.add(self._fid)
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self.close()
    def _fetch_str(self):
        if self._closed:
            return '{}(closed)'.format(type(self).__name__)
        try:
            from .sess import (
                eval_lua, get_current_session, get_current_greenlet,
            )
            sess = get_current_session()
            if get_current_greenlet() is sess._server_greenlet:
                return '{}({})'.format(type(self).__name__, self._fid)
            return eval_lua(
                b'return tostring(__py__.luaobjs[...])', self._fid,
            ).take_decoded()
        except Exception:
            return '{}({})'.format(type(self).__name__, self._fid)
    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self._fid)
    def __str__(self):
        if self._str_cache is None:
            self._str_cache = self._fetch_str()
        return self._str_cache
class LuaFunction(_LuaRefMixin):
    __slots__ = ()
    @classmethod
    def from_code(cls, code: Union[str, bytes]) -> 'LuaFunction':
        """用一段 Lua 源码构造 LuaFunction。
        code 必须是一个**表达式**，求值结果是一个函数。例如：
            fn = LuaFunction.from_code('function(x) return x * 2 end')
            fn(21)   # 42
            fn = LuaFunction.from_code('''
                function(text, index)
                    return {"apple", "banana", "cherry"}
                end
            ''')
        """
        if isinstance(code, str):
            code_bytes = code.encode('utf-8')
        elif isinstance(code, bytes):
            code_bytes = code
        else:
            raise TypeError(
                'code must be str or bytes, got {}'.format(
                    type(code).__name__,
                )
            )
        from .sess import eval_lua
        result = eval_lua(b'return ' + code_bytes).take_decoded()
        if not isinstance(result, cls):
            raise TypeError(
                'code did not evaluate to a function, got {}'.format(
                    type(result).__name__,
                )
            )
        return result
    def __call__(self, *args):
        if self._closed:
            raise RuntimeError('LuaFunction is closed')
        from .sess import eval_lua
        rp = eval_lua(
            b'return(function(n,...)'
            b'local f = __py__.luaobjs[n] '
            b'if f == nil then error("stale function ref") end '
            b'return f(...) end)(...)',
            self._fid, *args,
        )
        return _collect(rp)
class LuaThread(_LuaRefMixin):
    __slots__ = ()
_OBJ_GET = (
    b'return(function(n,k) '
    b'local o = __py__.luaobjs[n] '
    b'if o == nil then error("stale lua object ref") end '
    b'return o[k] end)(...)'
)
_OBJ_SET = (
    b'return(function(n,k,v) '
    b'local o = __py__.luaobjs[n] '
    b'if o == nil then error("stale lua object ref") end '
    b'o[k] = v end)(...)'
)
_OBJ_CALL = (
    b'return(function(n,...) '
    b'local o = __py__.luaobjs[n] '
    b'if o == nil then error("stale lua object ref") end '
    b'return o(...) end)(...)'
)
class LuaObject(_LuaRefMixin):
    __slots__ = ()
    def _check(self):
        if self._closed:
            raise RuntimeError('LuaObject is closed')
    def __getattr__(self, name):
        self._check()
        from .sess import eval_lua
        r = _collect(eval_lua(_OBJ_GET, self._fid, name))
        if r is None:
            raise AttributeError(name)
        return r
    def __setattr__(self, name, value):
        if name in ('_fid', '_closed', '_str_cache'):
            object.__setattr__(self, name, value)
            return
        self._check()
        from .sess import eval_lua
        eval_lua(_OBJ_SET, self._fid, name, value)
    def __getitem__(self, key):
        self._check()
        from .sess import eval_lua
        return _collect(eval_lua(_OBJ_GET, self._fid, key))
    def __setitem__(self, key, value):
        self._check()
        from .sess import eval_lua
        eval_lua(_OBJ_SET, self._fid, key, value)
    def __call__(self, *args):
        self._check()
        from .sess import eval_lua
        return _collect(eval_lua(_OBJ_CALL, self._fid, *args))
    def _binop(self, other, op):
        self._check()
        from .sess import eval_lua
        return _collect(eval_lua(
            b'return(function(n,o) '
            b'local a = __py__.luaobjs[n] '
            b'if a == nil then error("stale lua object ref") end '
            b'return a ' + op + b' o end)(...)',
            self._fid, other,
        ))
    def _unop(self, op):
        self._check()
        from .sess import eval_lua
        return _collect(eval_lua(
            b'return(function(n) '
            b'local a = __py__.luaobjs[n] '
            b'if a == nil then error("stale lua object ref") end '
            b'return ' + op + b'a end)(...)',
            self._fid,
        ))
    def __add__(self, other): return self._binop(other, b'+')
    def __sub__(self, other): return self._binop(other, b'-')
    def __mul__(self, other): return self._binop(other, b'*')
    def __truediv__(self, other): return self._binop(other, b'/')
    def __mod__(self, other): return self._binop(other, b'%')
    def __pow__(self, other): return self._binop(other, b'^')
    def __eq__(self, other): return self._binop(other, b'==')
    def __lt__(self, other): return self._binop(other, b'<')
    def __le__(self, other): return self._binop(other, b'<=')
    def __neg__(self): return self._unop(b'-')
    def __len__(self): return self._unop(b'#')
    def __hash__(self):
        return hash(('LuaObject', self._fid))