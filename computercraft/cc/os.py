from typing import Optional,cast,Any, Iterator

from ..lua import LuaNum
from ..sess import eval_lua
from ..sess import get_current_greenlet,CCGreenlet
__all__ = (
    'loadAPI', 'unloadAPI',
    'version', 'getComputerID', 'getComputerLabel',
    'setComputerLabel', 'run', 'captureEvent',
    'queueEvent', 'clock', 'time', 'day', 'epoch', 'date',
    'sleep', 'startTimer', 'cancelTimer',
    'setAlarm', 'cancelAlarm', 'shutdown', 'reboot',
)


def loadAPI(path: str) -> bool:
    """Load an API into the global environment.
    Deprecated: use require instead."""
    return eval_lua(b'G:os:M:loadAPI', path).take_bool()


def unloadAPI(name: str) -> None:
    """Unload an API loaded by os.loadAPI.
    Deprecated."""
    return eval_lua(b'G:os:M:unloadAPI', name).take_none()


def date(fmt: Optional[str] = None, time: Optional[LuaNum] = None):
    """Returns a date string or table using the specified format.
    New in version 1.83.0."""
    rp = eval_lua(b'G:os:M:date', fmt, time)
    return rp.take()


def version() -> str:
    return eval_lua(b'G:os:M:version').take_string()


def getComputerID() -> int:
    return eval_lua(b'G:os:M:getComputerID').take_int()


def getComputerLabel() -> Optional[str]:
    return eval_lua(b'G:os:M:getComputerLabel').take_option_string()


def setComputerLabel(label: Optional[str]) -> None:
    return eval_lua(b'G:os:M:setComputerLabel', label).take_none()


def run(environment: dict, programPath: str, *args: str) -> bool:
    return eval_lua(b'G:os:M:run', environment, programPath, *args,nopyobj="os.run").take_bool()


def captureEvent(event: Optional[str] = None, maxlen: Optional[int] = None)->Iterator[Any]:
    """Iterate over CC events.

    :param event: Event name to subscribe to. If ``None``, subscribe to
        all events (Lua side ``'*'`` wildcard). In that mode, each
        iteration yields a ``(name, params)`` tuple instead of just
        ``params``.
    :param maxlen: Bound on the queue length. When the queue is full,
        the oldest events are dropped. ``None`` means unbounded.

    Yields:
        - If ``event`` is given: ``params`` list for each matching event.
        - If ``event`` is ``None``: ``(name, params)`` tuple for every
          event.

    Note: subscribing to all events (``event=None``) will receive
    high-frequency events like ``mouse_move``, ``term_resize``, and
    ``peripheral``. This can flood the websocket and slow down the
    Minecraft server thread. Consider passing an explicit event name,
    or a small ``maxlen``, unless you really need the firehose.
    """
    glet= cast(CCGreenlet, getattr(get_current_greenlet(), 'cc_greenlet'))
    sess = glet._sess
    evr = sess._evr
    key = event if event is not None else '*'
    evr.sub(glet._task_id, key, maxlen=maxlen)
    try:
        while True:
            val = evr.get_from_stack(glet._task_id, key)
            if val is None:
                res = sess._server_greenlet.switch()
                assert res == 'event'
            else:
                yield val
    finally:
        evr.unsub(glet._task_id, key)


def queueEvent(event: str, *params) -> None:
    return eval_lua(b'G:os:M:queueEvent', event, *params).take_none()


def clock() -> LuaNum:
    # number of game ticks * 0.05, roughly seconds
    return eval_lua(b'G:os:M:clock').take_number()


# regarding ingame parameter below:
# python has great stdlib to deal with real current time
# we keep here only in-game time methods and parameters

def time(locale=b'ingame') -> LuaNum:
    # in hours 0..24
    return eval_lua(b'G:os:M:time', locale).take_number()


def day(locale=b'ingame') -> int:
    return eval_lua(b'G:os:M:day', locale).take_int()


def epoch(locale=b'ingame') -> int:
    return eval_lua(b'G:os:M:epoch', locale).take_int()


def sleep(seconds: LuaNum) -> None:
    return eval_lua(b'G:os:M:sleep', seconds).take_none()


def startTimer(timeout: LuaNum) -> int:
    return eval_lua(b'G:os:M:startTimer', timeout).take_int()


def cancelTimer(timerID: int) -> None:
    return eval_lua(b'G:os:M:cancelTimer', timerID).take_none()


def setAlarm(time: LuaNum) -> int:
    # takes time of the day in hours 0..24
    # returns integer alarmID
    return eval_lua(b'G:os:M:setAlarm', time).take_int()


def cancelAlarm(alarmID: int) -> None:
    return eval_lua(b'G:os:M:cancelAlarm', alarmID).take_none()


def shutdown() -> None:
    return eval_lua(b'G:os:M:shutdown').take_none()


def reboot() -> None:
    return eval_lua(b'G:os:M:reboot').take_none()
