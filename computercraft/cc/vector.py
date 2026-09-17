import math
from typing import Optional, Tuple


__all__ = ('Vector', 'new')


class Vector:
    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return 'vector.new({}, {}, {})'.format(self.x, self.y, self.z)

    def __eq__(self, o):
        return isinstance(o, Vector) and self.x == o.x and self.y == o.y and self.z == o.z

    def __add__(self, o):
        return Vector(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o):
        return Vector(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, m: float):
        return Vector(self.x * m, self.y * m, self.z * m)

    __rmul__ = __mul__

    def __truediv__(self, m: float):
        return Vector(self.x / m, self.y / m, self.z / m)

    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)

    def add(self, o: 'Vector') -> 'Vector':
        return self + o

    def sub(self, o: 'Vector') -> 'Vector':
        return self - o

    def mul(self, m: float) -> 'Vector':
        return self * m

    def div(self, m: float) -> 'Vector':
        return self / m

    def unm(self) -> 'Vector':
        return -self

    def dot(self, o: 'Vector') -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o: 'Vector') -> 'Vector':
        return Vector(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x,
        )

    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self) -> 'Vector':
        ln = self.length()
        return Vector(self.x / ln, self.y / ln, self.z / ln)

    def round(self, tolerance: Optional[float] = None) -> 'Vector':
        if tolerance is None:
            tolerance = 1e-5
        return Vector(
            round(self.x, -int(math.log10(tolerance))) if tolerance else round(self.x),
            round(self.y, -int(math.log10(tolerance))) if tolerance else round(self.y),
            round(self.z, -int(math.log10(tolerance))) if tolerance else round(self.z),
        )

    def tostring(self) -> str:
        return '{}, {}, {}'.format(self.x, self.y, self.z)

    def equals(self, o: 'Vector') -> bool:
        return self == o


def new(x: float, y: float, z: float) -> Vector:
    """Construct a new Vector."""
    return Vector(x, y, z)