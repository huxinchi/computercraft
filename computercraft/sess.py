import asyncio
import string
import sys
from code import InteractiveConsole
from collections import deque
from contextlib import contextmanager
from functools import partial
from importlib import import_module
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from itertools import count
from platform import python_version
from traceback import format_exc
from types import ModuleType

from greenlet import greenlet, getcurrent as get_current_greenlet

from . import rproc, ser, lua


__all__ = (
    'CCSession',
    'get_current_session',
    'eval_lua',
    'lua_context_object',
)


def debug(*args):
    sys.__stdout__.write(' '.join(map(str, args)) + '\n')
    sys.__stdout__.flush()


DIGITS = (string.digits + string.ascii_lowercase).encode('ascii')


def base36(n: int) -> bytes:
    r = bytearray()
    while n:
        r.append(DIGITS[n % 36])
        n //= 36
    return bytes(r)


def _is_global_greenlet():
    return not hasattr(get_current_greenlet(), 'cc_greenlet')


def get_current_session():
    try:
        return get_current_greenlet().cc_greenlet._sess
    except AttributeError:
        raise RuntimeError('Computercraft function was called outside context')


class StdFileProxy:
    def __init__(self, native, err):
        self._native = native
        self._err = err

    def read(self, size=-1):
        if _is_global_greenlet():
            return self._native.read(size)
        else:
            raise RuntimeError(
                "Computercraft environment doesn't support stdin read method")

    def readline(self, size=-1):
        if _is_global_greenlet():
            return self._native.readline(size)
        else:
            if size is not None and size >= 0:
                raise RuntimeError(
                    "Computercraft environment doesn't support "
                    "stdin readline method with parameter")
            r = eval_lua(b'G:io:M:read')
            if r.peek() is False:
                r.take()   # press ctrl+C
                eval_lua(
                    b'io.stderr:write(...)',
                    r.take_bytes(),
                    immediate=True)
                return ''
            return r.take_string() + '\n'

    def write(self, s):
        if _is_global_greenlet():
            return self._native.write(s)
        else:
            s = s.encode(get_current_session()._enc, errors='replace')
            if self._err:
                return eval_lua(b'io.stderr:write(...)', s).take_none()
            else:
                return eval_lua(b'io.write(...)', s).take_none()

    def fileno(self):
        if _is_global_greenlet():
            return self._native.fileno()
        else:
            # preventing use of gnu readline here
            # https://github.com/python/cpython/blob/master/Python/bltinmodule.c#L1970
            return -1

    def __getattr__(self, name):
        return getattr(self._native, name)

import importlib.util
import os
from importlib import import_module
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from types import ModuleType


# 虚拟前缀 → 候选真实前缀列表（后注册的优先）
_EXTRA_ROUTES: dict = {}


def register_route(virtual: str, real: str) -> None:
    """往 `_EXTRA_ROUTES[virtual]` 末尾追加一条候选。

    virtual: 'cc'、'cc.cc'、'myext'
    real:    'computercraft.cc'、'computercraft.cc_cc'、'usermod'

    同一 virtual 可注册多个 real，后注册的优先。
    """
    _EXTRA_ROUTES.setdefault(virtual.rstrip('.'), []).append(
        real.rstrip('.'),
    )


def unregister_route(virtual: str, real: str = None) -> None:
    virtual = virtual.rstrip('.')
    if real is None:
        _EXTRA_ROUTES.pop(virtual, None)
        return
    real = real.rstrip('.')
    lst = _EXTRA_ROUTES.get(virtual, [])
    try:
        lst.remove(real)
    except ValueError:
        return
    if not lst:
        _EXTRA_ROUTES.pop(virtual, None)


def list_routes() -> dict:
    return {k: list(v) for k, v in _EXTRA_ROUTES.items()}


# ===== 内建映射，手写 =====
register_route('cc',           'computercraft.cc')
register_route('cc.cc',        'computercraft.cc_cc')
register_route('cc.cc.image',  'computercraft.cc_cc_image')
register_route('cc.cc.shell',  'computercraft.cc_cc_shell')
register_route('cc.cc.audio',  'computercraft.cc_cc_audio')


def _try_routes(fullname: str):
    """最长前缀匹配 + 后注册优先。找不到返回 None。"""
    parts = fullname.split('.')
    for depth in range(len(parts), 0, -1):
        prefix = '.'.join(parts[:depth])
        candidates = _EXTRA_ROUTES.get(prefix)
        if not candidates:
            continue
        rest = parts[depth:]
        for target in reversed(candidates):
            real = target + (('.' + '.'.join(rest)) if rest else '')
            try:
                if importlib.util.find_spec(real) is not None:
                    return real
            except (ImportError, ValueError, ModuleNotFoundError):
                continue
    return None


def _resolve(fullname: str) -> str:
    real = _try_routes(fullname)
    if real is not None:
        return real
    raise ImportError('cc: no mapping for ' + fullname)


def _should_handle(fullname: str) -> bool:
    parts = fullname.split('.')
    for depth in range(len(parts), 0, -1):
        if '.'.join(parts[:depth]) in _EXTRA_ROUTES:
            return True
    return False


class ComputerCraftFinder(MetaPathFinder):
    @staticmethod
    def find_spec(fullname, path, target=None):
        if not _should_handle(fullname):
            return None

        try:
            real_name = _resolve(fullname)
        except ImportError:
            return None

        try:
            real_spec = importlib.util.find_spec(real_name)
        except (ImportError, ValueError, ModuleNotFoundError):
            return None
        if real_spec is None:
            return None

        is_pkg = real_spec.submodule_search_locations is not None
        spec = ModuleSpec(fullname, ComputerCraftLoader, is_package=is_pkg)
        if is_pkg:
            spec.submodule_search_locations = list(
                real_spec.submodule_search_locations,
            )
        spec.origin = real_spec.origin
        return spec


class ComputerCraftLoader(Loader):
    @staticmethod
    def create_module(spec):
        real = _resolve(spec.name)
        mod = ModuleType(spec.name)

        if spec.submodule_search_locations is not None:
            # 包：合并 __init__.py 和 _pkg.py 的 __all__
            pkgmod = import_module(real)
            for k in getattr(pkgmod, '__all__', ()):
                setattr(mod, k, getattr(pkgmod, k))

            try:
                pkgmod2 = import_module(real + '._pkg')
            except ImportError:
                pass
            else:
                for k in getattr(pkgmod2, '__all__', ()):
                    setattr(mod, k, getattr(pkgmod2, k))

            if type(pkgmod) is not ModuleType:
                mod.__class__ = type(pkgmod)
            return mod
        else:
            rawmod = import_module(real)
            for k in getattr(rawmod, '__all__', ()):
                setattr(mod, k, getattr(rawmod, k))
            if type(rawmod) is not ModuleType:
                mod.__class__ = type(rawmod)
            return mod

    @staticmethod
    def exec_module(module):
        pass


def install_import_hook():
    import sys
    sys.meta_path.insert(0, ComputerCraftFinder)

install_import_hook()


@contextmanager
def patch_std_files():
    pin, pout, perr = sys.stdin, sys.stdout, sys.stderr
    sys.stdin = StdFileProxy(pin, False)
    sys.stdout = StdFileProxy(pout, False)
    sys.stderr = StdFileProxy(perr, True)
    try:
        yield
    finally:
        sys.stdin, sys.stdout, sys.stderr = pin, pout, perr

def eval_lua(lua_code, *params, immediate=False,nopyobj=None):
    sess = get_current_session()
    sess._flush_pending_luaobjs()
    assert isinstance(lua_code, bytes)
    request = (
        (b'I' if immediate else b'T')
        + ser.serialize(lua_code, sess._enc, session=sess,nopyobj=nopyobj)
        + ser.serialize(params, sess._enc, session=sess,nopyobj=nopyobj)
    )
    result = sess._server_greenlet.switch(request)
    rp = rproc.ResultProc(ser.deserialize(result), sess._enc)
    if not immediate:
        rp.check_bool_error()
    return rp


@contextmanager
def lua_context_object(
    create_expr: bytes,
    create_params: tuple,
    finalizer_template: bytes = b'',
    prefix: bytes = b'',
):
    sess = get_current_session()
    fid = sess.create_task_id()
    r = eval_lua(
        prefix
        + b'return(function(n,...)local o,e='
        + create_expr
        + b';if o then temp[n]=o;return true;end'
        + b';return o,e;end)(...)', fid, *create_params)
    r.check_nil_error()
    assert r.take_bool() is True
    try:
        yield fid
    finally:
        f = finalizer_template.replace(b'{e}', b'temp[n]')
        if f:
            f += b';'  # important to not have ;;
        eval_lua(
            b'local n=...;' + f + b'temp[n]=nil', fid)


class _TempObjectExt:
    CALL_OP = b'.'
    _fid: bytes
    def _call(self, method: bytes, *args):
        return eval_lua(
            b'return(function(n,...)return temp[n]'
            + self.CALL_OP
            + method
            + b'(...);end)(...)', self._fid, *args)


class ContextObject(_TempObjectExt, lua.TempObject):
    pass


class ReferenceObject(_TempObjectExt, lua.TempObject):
    def __init__(self, lua_context_gen):
        self._g = lua_context_gen  # keep the reference
        self._fid = self._g.__enter__()


class CCGreenlet:
    def __init__(self, body_fn, sess=None):
        if sess is None:
            self._sess = get_current_session()
        else:
            self._sess = sess

        self._task_id = self._sess.create_task_id()
        self._sess._greenlets[self._task_id] = self

        parent_g = get_current_greenlet()
        if parent_g is self._sess._server_greenlet:
            self._parent = None
        else:
            self._parent = parent_g.cc_greenlet
            self._parent._children.add(self._task_id)
            self._sess._new_greenlets.append(self._task_id)

        self._children = set()
        self._g = greenlet(body_fn)
        self._g.cc_greenlet = self

    def detach_children(self):
        if self._children:
            ch = list(self._children)
            self._children.clear()
            self._sess.drop(ch)

    def _on_death(self, error=None):
        self._sess._greenlets.pop(self._task_id, None)
        self.detach_children()
        if error is not None:
            if error is True:
                error = None
            else:
                error = error.encode(self._sess._enc, errors='replace')
            self._sess._sender(b'C' + ser.serialize(error, self._sess._enc))
        if self._parent is not None:
            self._parent._children.discard(self._task_id)

    def defer_switch(self, *args, **kwargs):
        asyncio.get_running_loop().call_soon(
            partial(self.switch, *args, **kwargs))

    def switch(self, *args, **kwargs):
        # switch must be called from server greenlet
        assert get_current_greenlet() is self._sess._server_greenlet
        try:
            task = self._g.switch(*args, **kwargs)
        except SystemExit:
            self._on_death(True)
            return
        except Exception:
            self._on_death(format_exc(limit=None, chain=False))
            return

        # lua_eval call or simply idle
        if isinstance(task, bytes):
            x = self
            while x._g.dead:
                x = x._parent
            self._sess._sender(
                task[0:1] + ser.serialize(x._task_id, 'ascii') + task[1:])

        if self._g.dead:
           if self is self._sess._program_greenlet:
               self._on_death(True)
           else:
               self._on_death()

    def throw(self, exc):
        self._g.throw(exc)


class CCEventRouter:
    def __init__(self, on_first_sub, on_last_unsub, resume_task,
                 default_maxlen=None):
        self._stacks = {}
        self._active = {}
        self._default_maxlen = default_maxlen
        self._on_first_sub = on_first_sub
        self._on_last_unsub = on_last_unsub
        self._resume_task = resume_task

    def sub(self, task_id, event,maxlen=None):
        if event not in self._stacks:
            self._stacks[event] = {}
            self._on_first_sub(event)
        se = self._stacks[event]
        if task_id in se:
            raise Exception('Same task subscribes to the same event twice')
        if maxlen is None:
            maxlen = self._default_maxlen
        se[task_id] = deque(maxlen=maxlen)

    def unsub(self, task_id, event):
        if event not in self._stacks:
            return
        self._stacks[event].pop(task_id, None)
        if len(self._stacks[event]) == 0:
            self._on_last_unsub(event)
            del self._stacks[event]
    def on_event(self, event, params):
        dispatched = False

        # 精确订阅
        if event in self._stacks:
            dispatched = True
            for task_id, queue in self._stacks[event].items():
                
                queue.append(params)
                if self._active.get(task_id) == event:
                    self._set_task_status(task_id, event, False)
                    self._resume_task(task_id)

        # 通配订阅 '*'：payload 是 (event_name, params) 元组
        if '*' in self._stacks:
            dispatched = True
            for task_id, queue in self._stacks['*'].items():
                
                   
                queue.append((event, params))
                if self._active.get(task_id) == '*':
                    self._set_task_status(task_id, '*', False)
                    self._resume_task(task_id)

        if not dispatched:
            self._on_last_unsub(event)

    def get_from_stack(self, task_id, event):
        queue = self._stacks[event][task_id]
        try:
            return queue.popleft()
        except IndexError:
            self._set_task_status(task_id, event, True)
            return None

    def _set_task_status(self, task_id, event, waits: bool):
        if waits:
            self._active[task_id] = event
        else:
            self._active.pop(task_id, None)


class CCSession:
    EVENT_QUEUE_MAXLEN = 256
    def __init__(self, sender):
        self._tid_allocator = map(base36, count(start=1))
        self._sender = sender
        self._pending_luaobj_free = set()
        self._enc = ser._CC_ENC
        self._greenlets = {}
        self._pyfuncs = {}
        self._next_pyfunc_id = 1
        self._server_greenlet = get_current_greenlet()
        self._program_greenlet = None
        self._evr = CCEventRouter(
            lambda event: self._sender(b'S' + ser.serialize(event, self._enc)),
            lambda event: self._sender(b'U' + ser.serialize(event, self._enc)),
            lambda task_id: self._greenlets[task_id].switch('event'),
            default_maxlen=self.EVENT_QUEUE_MAXLEN,
        )
        self._new_greenlets = []
    def _flush_pending_luaobjs(self):
        if not self._pending_luaobj_free:
            return
        ids = sorted(self._pending_luaobj_free)
        self._pending_luaobj_free.clear()
        self._sender(b'F' + b''.join(
            ser.serialize(i, self._enc) for i in ids
        ))
    def on_task_result(self, task_id, result):
        assert get_current_greenlet() is self._server_greenlet
        if task_id not in self._greenlets:
            # ignore for dropped tasks
            return
        self._greenlets[task_id].switch(result)
        self._run_new_greenlets()

    def on_event(self, event, params):
        self._evr.on_event(event.decode(self._enc), params)
        self._run_new_greenlets()

    def create_task_id(self):
        return next(self._tid_allocator)

    def _drop_command(self, all_tids):
        return b'D' + b''.join(
            ser.serialize(tid, self._enc) for tid in all_tids)

    def _sorted_drop_command(self, all_tids):
        # use instead _drop_command in tests
        all_tids = sorted(set(all_tids))
        return b'D' + b''.join(
            ser.serialize(tid, self._enc) for tid in all_tids)

    def drop(self, task_ids):
        def collect(task_id):
            yield task_id
            g = self._greenlets.pop(task_id)
            for tid in g._children:
                yield from collect(tid)

        all_tids = []
        for task_id in task_ids:
            all_tids.extend(collect(task_id))

        self._sender(self._drop_command(all_tids))

    def _run_new_greenlets(self):
        while self._new_greenlets:
            ng, self._new_greenlets = self._new_greenlets, []
            for tid in ng:
                self._greenlets[tid].switch()

    def throw_keyboard_interrupt(self):
        self._program_greenlet.throw(EOFError())

    def _run_sandboxed_greenlet(self, fn):
        self._program_greenlet = CCGreenlet(fn, sess=self)
        self._program_greenlet.switch()

    def run_program(self, args, path, code):
        def _run_program():
            cc = compile(code, path, 'exec')
            exec(cc, {'__file__': path,"__name__":"__main__", 'args': args})

        self._run_sandboxed_greenlet(_run_program)

    def run_repl(self):
        def _repl():
            InteractiveConsole(locals={}).interact(
                banner='Python {}'.format(python_version()),
                exitmsg='',
            )

        self._run_sandboxed_greenlet(_repl)
    def register_pyobj(self, obj):
        fid = self._next_pyfunc_id
        self._next_pyfunc_id += 1
        self._pyfuncs[fid] = obj
        return fid


    def release_pyobj(self, fid):
        self._pyfuncs.pop(fid, None)
    def on_pyobj_call(self, call_id, fid, op, args):
        obj = self._pyfuncs.get(fid)
        if obj is None:
            self._reply_pyobj(call_id, False, 'stale python object ref')
            return
        fn = _OPS.get(op)
        if fn is None:
            self._reply_pyobj(call_id, False, 'unsupported op: ' + op)
            return

        def _runner():
            try:
                result = fn(obj, args)
            except Exception as e:
                self._reply_pyobj(call_id, False, str(e))
                return
            self._reply_pyobj(call_id, True, result)

        CCGreenlet(_runner, sess=self).switch()


    def _reply_pyobj(self, call_id, ok, result):
        self._sender(
            b'R'
            + ser.serialize(call_id, self._enc)
            + (b'T' if ok else b'F')
            + ser.serialize(result, self._enc, session=self)
        )
_OPS = {
    'call':    lambda o, a: o(*a),
    'getattr': lambda o, a: getattr(o, a[0], None),
    'setattr': lambda o, a: setattr(o, a[0], a[1]),
    'str':     lambda o, a: str(o),
    'len':     lambda o, a: len(o),
    'eq':      lambda o, a: o == a[0],
    'lt':      lambda o, a: o < a[0],
    'le':      lambda o, a: o <= a[0],
    'add':     lambda o, a: o + a[0],
    'sub':     lambda o, a: o - a[0],
    'mul':     lambda o, a: o * a[0],
    'div':     lambda o, a: o / a[0],
    'mod':     lambda o, a: o % a[0],
    'pow':     lambda o, a: o ** a[0],
    'neg':     lambda o, a: -o,
    'and':     lambda o, a: o & a[0],
    'or':      lambda o, a: o | a[0],
    'xor':     lambda o, a: o ^ a[0],
    'shl':     lambda o, a: o << a[0],
    'shr':     lambda o, a: o >> a[0],
    'invert':  lambda o, a: ~o,
}


