from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple, Union
from ..sess import eval_lua, lua_context_object, ContextObject


__all__ = ('request', 'get', 'post', 'checkURL', 'checkURLAsync', 'websocket')


def request(url_or_options: Union[str, dict],
            body: Optional[str] = None,
            headers: Optional[dict] = None,
            binary: bool = False) -> None:
    """Asynchronously make a HTTP request.
    Events: http_success / http_failure.
    Can accept either positional args or a single options table."""
    if isinstance(url_or_options, dict):
        return eval_lua(b'G:http:M:request', url_or_options).take_none()
    return eval_lua(
        b'G:http:M:request', url_or_options, body, headers, binary,
    ).take_none()


def get(url_or_options: Union[str, dict],
        headers: Optional[dict] = None,
        binary: bool = False):
    """Make a synchronous HTTP GET request.
    Returns a Response handle, or (nil, err) on failure."""
    if isinstance(url_or_options, dict):
        rp = eval_lua(b'G:http:M:get', url_or_options)
    else:
        rp = eval_lua(b'G:http:M:get', url_or_options, headers, binary)
    return rp.take()


def post(url_or_options: Union[str, dict],
         body: Optional[str] = None,
         headers: Optional[dict] = None,
         binary: bool = False):
    """Make a synchronous HTTP POST request."""
    if isinstance(url_or_options, dict):
        rp = eval_lua(b'G:http:M:post', url_or_options)
    else:
        rp = eval_lua(b'G:http:M:post', url_or_options, body, headers, binary)
    return rp.take()


def checkURL(url: str) -> bool:
    """Determine whether a URL can be requested."""
    return eval_lua(b'G:http:M:checkURL', url).take_bool()


def checkURLAsync(url: str) -> bool:
    """Asynchronously determine whether a URL can be requested.
    Listen for http_check event for the actual result."""
    return eval_lua(b'G:http:M:checkURLAsync', url).take_bool()


@contextmanager
def websocket(url: str, headers: Optional[dict] = None):
    """Attempt to establish a WebSocket connection.
    Yields a WebSocketHandle on success, raises on failure."""
    with lua_context_object(
        b'http.websocket(...)',
        (url, headers),
        b'{e}.close()',
    ) as fid:
        yield WebSocketHandle(fid)


class WebSocketHandle(ContextObject):
    def send(self, message: str, binary: bool = False) -> None:
        return self._call(
            b'send', message.encode('utf-8') if not binary else message, binary,
        ).take_none()

    def receive(self) -> Optional[Tuple[str, bool]]:
        """Block until a message arrives.
        Returns (message, isBinary) or None if closed."""
        rp = self._call(b'receive')
        if rp.peek() is None:
            return None
        return (rp.take_string(), rp.take_bool())

    def close(self) -> None:
        return self._call(b'close').take_none()