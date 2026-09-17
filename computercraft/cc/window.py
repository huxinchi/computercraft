from typing import Optional, Tuple

from ..sess import lua_context_object, ReferenceObject
from .term import TermMixin, TermTarget


__all__ = ('create', )


class TermWindow(ReferenceObject, TermMixin):
    def setVisible(self, visibility: bool) -> None:
        return self._call(b'setVisible', visibility).take_none()

    def getVisible(self) -> bool:
        """New in version 1.106.0."""
        return self._call(b'getVisible').take_bool()

    def redraw(self) -> None:
        return self._call(b'redraw').take_none()

    def restoreCursor(self) -> None:
        return self._call(b'restoreCursor').take_none()

    def getPosition(self) -> Tuple[int, int]:
        rp = self._call(b'getPosition')
        return tuple(rp.take_int() for _ in range(2))

    def reposition(
        self, x: int, y: int,
        width: Optional[int] = None, height: Optional[int] = None,
        parent: Optional[TermTarget] = None,
    ) -> None:
        return self._call(
            b'reposition', x, y, width, height, parent,
        ).take_none()

    def getLine(self, y: int) -> Tuple[str, bytes, bytes]:
        rp = self._call(b'getLine', y)
        return rp.take_string(), rp.take_bytes(), rp.take_bytes()


def create(
    parentTerm: TermTarget,
    x: int, y: int,
    width: int, height: int,
    visible: Optional[bool] = None,
) -> TermWindow:
    return TermWindow(lua_context_object(
        b'window.create(...)',
        (parentTerm, x, y, width, height, visible)))
