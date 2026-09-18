from ..sess import CCGreenlet, get_current_greenlet


__all__ = (
    'waitForAny',
    'waitForAll',
)


from typing import Any, Callable,cast

def waitForAny(*task_fns: Callable[[], Any]) -> None: 

    pgl= cast(CCGreenlet, getattr(get_current_greenlet(), 'cc_greenlet'))
    sess = pgl._sess

    for fn in task_fns:
        CCGreenlet(fn)

    try:
        sess._server_greenlet.switch()
    finally:
        pgl.detach_children()


def waitForAll(*task_fns: Callable[[], Any]) -> None:     
    pgl= cast(CCGreenlet, getattr(get_current_greenlet(), 'cc_greenlet'))
    sess = pgl._sess

    for fn in task_fns:
        CCGreenlet(fn)

    try:
        for _ in range(len(task_fns)):
            sess._server_greenlet.switch()
    finally:
        pgl.detach_children()
