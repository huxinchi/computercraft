from ..sess import eval_lua


__all__ = (
    'equipBack',
    'unequipBack',
)


def equipBack()->None:
    return eval_lua(b'G:pocket:M:equipBack').check_bool_error()


def unequipBack()->None:
    return eval_lua(b'G:pocket:M:unequipBack').check_bool_error()
