import argparse,hmac
from os.path import join, dirname, abspath
from aiohttp import web, WSMsgType
from . import ser, sess,rproc
from .rproc import lua_table_to_list
THIS_DIR = dirname(abspath(__file__))
LUA_FILE = join(THIS_DIR, 'back.lua')
PROTO_VERSION = 5
PROTO_ERROR = b'C' + ser.serialize(b'protocol error', 'ascii')
def protocol(send, sess_cls=sess.CCSession):
    # handle first frame
    msg = yield
    msg = ser.dcmditer(msg)
    action = next(msg)
    if action != b'0':
        send(PROTO_ERROR)
        return
    password=next(msg).decode(errors="ignore")
    if not hmac.compare_digest(password,setpassword):
      send(b'C' + ser.serialize((
            'password mismatch'
            ' redownload py'
        ),"ascii"))
      return
    version = next(msg)
    if version != PROTO_VERSION:
        send(b'C' + ser.serialize((
            'protocol version mismatch'
            ' (expected {}, got {}),'
            ' redownload py'
        ).format(PROTO_VERSION, version), 'ascii'))
        return
    pyside=next(msg)
    # CC:T starts its "args" with 0, includes program name
    # but {...} works normally, starting from 1
    args = next(msg)
    args = lua_table_to_list(args, low_index=0 if 0 in args else 1)
    path, code = None, None
    try:
        path = next(msg)
        code = next(msg)
    except StopIteration:
        pass
    if pyside:
        if len(args) < 2:
            send(b'C' + ser.serialize(b'pyside: no program name', 'ascii'))
            return
        prog_name = args[1]
        try:
            with open(prog_name, 'r', encoding='utf-8') as f:
                code = f.read()
        except OSError as e:
            send(b'C' + ser.serialize(
                'pyside: {}'.format(e).encode('ascii'), 'ascii',
            ))
            return
        path = prog_name
    sess = sess_cls(send)
    if code is not None:
        sess.run_program(args, path, code)
    else:
        sess.run_repl()
    # handle the rest of frames
    while True:
        msg = yield
        msg = ser.dcmditer(msg)
        action = next(msg)
        if action == b'E':
            sess.on_event(next(msg), lua_table_to_list(next(msg)))
        elif action == b'T':
            sess.on_task_result(next(msg), next(msg))
        elif action == b'C':
            sess.throw_keyboard_interrupt()
        elif action == b'D':  # disconnection
            return
        elif action == b'P':
            call_id = next(msg)
            spec = rproc._decode_rec(sess._enc, next(msg))
            args = lua_table_to_list(spec['args'])
            sess.on_pyobj_call(call_id, spec['fid'], args)
        else:
            send(PROTO_ERROR)
            return
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument(
        '--port', type=int, default=8000,
        help='Web (for wget) & websocket (for computercraft) port')
    parser.add_argument(
        '--capture', type=str, default=None,
        help='Capture test data into a file')
    parser.add_argument(
        '--password', type=str, default="def password",
        help='setting password')
    parser.add_argument(
        '--disable-download',action='store_true',
        help='disable download port')
    return parser
async def ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    squeue = []
    pgen = request.app['protocol_factory'](squeue.append)
    next(pgen)
    mustquit = False
    async for msg in ws:
        if msg.type != WSMsgType.BINARY:
            continue
        try:
            pgen.send(msg.data)
        except StopIteration:
            mustquit = True
        for m in squeue:
            await ws.send_bytes(m)
        squeue.clear()
        if mustquit:
            break
    if not mustquit:  # sudden disconnect
        try:
            pgen.send(b'D')
        except StopIteration:
            pass
    return ws
def backdoor(request):
    with open(LUA_FILE, 'r') as f:
         fcont = f.read()
    webhost = '{}:{}'.format(request.url.host, request.url.port or request.app['port'])
    return web.Response(text=(
        fcont
        .replace('__url__', 'ws://{}/ws/'.format(webhost))
        .replace('__password__', setpassword)
        .replace('__log__', 'nil' if request.app["log"] is None else "'"+request.app["log"]+"'")
    ))
def main():
    global setpassword
    args = create_parser().parse_args()
    app = web.Application()
    app['port'] = args.port
    app['protocol_factory'] = protocol
    app["log"]=args.capture
    setpassword=args.password
    if not args.disable_download:
        app.router.add_get('/', backdoor)
    app.router.add_get('/ws/', ws)
    async def capture(app):
        with open(args.capture, 'wb') as f:
            def protocol_factory(send, sess_cls=sess.CCSession):
                def write_frame(t, m):
                    ln = str(len(m)).encode('ascii')
                    f.write(t + ln + b':' + m + b'\n')
                def send_wrap(m):
                    write_frame(b'S', m)
                    return send(m)
                class SessOverride(sess_cls):
                    _drop_command = sess_cls._sorted_drop_command
                p = protocol(send_wrap, sess_cls=SessOverride)
                def pgen():
                    next(p)
                    while True:
                        m = yield
                        write_frame(b'R', m)
                        try:
                            p.send(m)
                        except StopIteration as e:
                            return e.value
                return pgen()
            app['protocol_factory'] = protocol_factory
            yield
    if args.capture is not None:
        sess.python_version = lambda: '<VERSION>'
        app.cleanup_ctx.append(capture)
    with sess.patch_std_files():
        web.run_app(app, host=args.host, port=args.port)
if __name__ == '__main__':
    main()
# TODO: move greenlets into separate thread
# to prevent hanging
"""
import ctypes
import time
import threading
def thmain():
    # hangs
    while True:
        pass
th = threading.Thread(target=thmain)
th.start()
time.sleep(5)
ctypes.pythonapi.PyThreadState_SetAsyncExc(
    ctypes.c_long(th.ident),
    ctypes.py_object(TimeoutError))
time.sleep(3)
"""
