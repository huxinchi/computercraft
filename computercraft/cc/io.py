from ..sess import eval_lua
from typing import Optional
__all__ = ('read', 'write', 'lines', 'open', 'close', 'flush', 'input', 'output')


def read(*formats):
    """Read from the default input (or a file handle).

    Formats: "n" (number), "a" (all), "l" (line), or a number.
    """
    rp = eval_lua(b'G:io:M:read', *formats)
    return rp.take()


def write(*texts) -> None:
    """Write to the default output."""
    return eval_lua(
        b'G:io:M:write',
        *[t.encode('utf-8') if isinstance(t, str) else t for t in texts],
    ).take_none()


def lines(filename: Optional[str] = None, *formats):
    """Opens a file in read mode and returns an iterator.
    Each iteration returns a new line (or chunk per the given formats).

    Usage:
        for line in io.lines("data.txt"):
            print(line)

        for chunk in io.lines("audio.dfpwm", 16 * 1024):
            ...
    """
    return eval_lua(b'G:io:M:lines', filename, *formats).take()


def open(filename: str, mode: Optional[str] = None):
    """Open a file, returning a file handle."""
    return eval_lua(b'G:io:M:open', filename, mode).take()


def close(file=None) -> None:
    """Close a file handle."""
    return eval_lua(b'G:io:M:close', file).take_none()


def flush() -> None:
    """Flush the default output."""
    return eval_lua(b'G:io:M:flush').take_none()


def input(file=None):
    """Get or set the default input file handle."""
    return eval_lua(b'G:io:M:input', file).take()


def output(file=None):
    """Get or set the default output file handle."""
    return eval_lua(b'G:io:M:output', file).take()