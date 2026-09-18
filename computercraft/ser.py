from typing import Any, Tuple
from uuid import UUID

from . import lua


__all__ = (
    '_CC_ENC',
    'cc_dirty_encode',
    'serialize',
    'deserialize',
)


_CC_ENC = 'latin1'

# encoding fast check
assert [bytes([i]) for i in range(256)] == [
    chr(i).encode(_CC_ENC) for i in range(256)]


def cc_dirty_encode(s: str) -> bytes:
    return s.encode(_CC_ENC, errors='replace')


def serialize(v, encoding, session=None,nopyobj=None):
    if v is None:
        return b'N'
    if v is False:
        return b'F'
    if v is True:
        return b'T'
    if isinstance(v, (int, float)):
        return '[{}]'.format(v).encode('ascii')
    if isinstance(v, bytes):
        return '<{}>'.format(len(v)).encode('ascii') + v
    if isinstance(v, UUID):
        return serialize(str(v).encode('ascii'), encoding, session)
    if isinstance(v, str):
        return serialize(v.encode(encoding), encoding, session)
    if isinstance(v, (list, tuple)):
        items = []
        for k, x in enumerate(v, start=1):
            items.append(
                b':' + serialize(k, encoding, session,nopyobj=nopyobj)
                + serialize(x, encoding, session,nopyobj=nopyobj))
        return b'{' + b''.join(items) + b'}'
    if isinstance(v, dict):
        items = []
        for k, x in v.items():
            items.append(
                b':' + serialize(k, encoding, session,nopyobj=nopyobj)
                + serialize(x, encoding, session,nopyobj=nopyobj))
        return b'{' + b''.join(items) + b'}'
    if isinstance(v, lua.LuaFunction):
        return b'K[' + str(v._fid).encode('ascii') + b']'
    if isinstance(v, lua.LuaThread):
        return b'Y[' + str(v._fid).encode('ascii') + b']'
    if isinstance(v, lua.LuaObject):
        return b'O[' + str(v._fid).encode('ascii') + b']'
    if isinstance(v, lua.LuaExpr):
        code = v.get_expr_code()
        return 'E{}>'.format(len(code)).encode('ascii') + code
    if isinstance(v, lua.TempObject):
        return 'X{}>'.format(len(v._fid)).encode('ascii') + v._fid
    if nopyobj is not None:
        raise TypeError(
            "{}: Python callable/object not allowed here".format(nopyobj)
        )
    if session is None:
        from .sess import get_current_session
        session = get_current_session()

    if lua.is_function(v):
        fid = session.register_pyobj(v)
        return b'P[' + str(fid).encode('ascii') + b']'
    fid = session.register_pyobj(v)
    mt = lua.make_mt_spec(v)
    payload = serialize({b'fid': fid, b'mt': mt}, encoding, session)
    return b'I' + payload

    # 不可序列化
    #raise ValueError('Value can\'t be serialized: {}'.format(repr(v)))


def _deserialize(b: bytes, _idx: int):
    tok = b[_idx]
    _idx += 1
    if tok == 78:  # N
        return None, _idx
    elif tok == 75:  # K
        newidx = b.index(b']', _idx)
        fid = int(b[_idx + 1:newidx])
        return lua.LuaFunction(fid), newidx + 1
    elif tok == 89:  # Y
        newidx = b.index(b']', _idx)
        fid = int(b[_idx + 1:newidx])
        return lua.LuaThread(fid), newidx + 1
    elif tok == 79:  # O
        newidx = b.index(b']', _idx)
        fid = int(b[_idx + 1:newidx])
        return lua.LuaObject(fid), newidx + 1
    elif tok == 80:  # P — Python function proxy, returned
        newidx = b.index(b']', _idx)
        fid = int(b[_idx + 1:newidx])
        _idx = newidx + 1
        try:
            from .sess import get_current_session
            return get_current_session()._pyfuncs[fid], _idx
        except (RuntimeError, KeyError):
            return lua.LuaFunction(fid), _idx
    elif tok == 73:  # I
        payload, _idx = _deserialize(b, _idx)
        fid = payload[b'fid']
        try:
            from .sess import get_current_session
            return get_current_session()._pyfuncs[fid], _idx
        except (RuntimeError, KeyError):
            return lua.LuaObject(fid), _idx
    elif tok == 70:  # F
        return False, _idx
    elif tok == 84:  # T
        return True, _idx
    elif tok == 91:  # [
        newidx = b.index(b']', _idx)
        f = float(b[_idx:newidx])
        if f.is_integer():
            f = int(f)
        return f, newidx + 1
    elif tok == 60:  # <
        newidx = b.index(b'>', _idx)
        ln = int(b[_idx:newidx])
        return b[newidx + 1:newidx + 1 + ln], newidx + 1 + ln
    elif tok == 123:  # {
        r = {}
        while True:
            tok = b[_idx]
            _idx += 1
            if tok == 125:  # }
                break
            key, _idx = _deserialize(b, _idx)
            value, _idx = _deserialize(b, _idx)
            r[key] = value
        return r, _idx
    else:
        raise ValueError


def deserialize(b: bytes) -> Any:
    return _deserialize(b, 0)[0]


def dcmditer(b: bytes):
    yield b[0:1]
    idx = 1
    while idx < len(b):
        chunk, idx = _deserialize(b, idx)
        yield chunk
