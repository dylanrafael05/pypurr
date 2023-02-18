from . import window
import pyglet.math as pgm
from typing import Optional, SupportsFloat


Vec2 = pgm.Vec2


_scr_mod_x = (window.window_size[0] // 2)
_scr_mod_y = (window.window_size[1] // 2)


SupportsVec2 = tuple[SupportsFloat, SupportsFloat] | Vec2
def vec2(v: SupportsVec2) -> Vec2:
    if isinstance(v, Vec2):
        return v
    return Vec2(float(v[0]), float(v[1]))


def from_screen(x, y) -> Vec2:
    return Vec2(x - _scr_mod_x, y - _scr_mod_y)


def to_screen(v) -> (float, float):
    return v.x + _scr_mod_x, v.y + _scr_mod_y


class Rect:
    """
    Represents an axis-aligned rectangle with the given minimum and
    maximum points.
    """

    __slots__ = 'min', 'max'

    def __init__(self, a: SupportsVec2, b: SupportsVec2):
        a, b = vec2(a), vec2(b)
        self.min = Vec2(min(a.x, b.x), min(a.y, b.y))
        self.max = Vec2(max(a.x, b.x), max(a.y, b.y))

    def intersection(self, other: 'Rect') -> Optional['Rect']:
        min_pos = Vec2(max(self.min.x, other.min.x), max(self.min.y, other.min.y))
        max_pos = Vec2(min(self.max.x, other.max.x), min(self.max.y, other.max.y))

        if min_pos.x > max_pos.x or min_pos.y > max_pos.y:
            return None

        result = Rect(min_pos, max_pos)

        return result if result.size.mag > 0 else None
    def __matmul__(self, other: 'Rect') -> Optional['Rect']:
        return self.intersection(other)

    def __contains__(self, other: SupportsVec2) -> bool:
        other = vec2(other)
        return self.min.x <= other.x <= self.max.x and self.min.y <= other.y <= self.max.y
    def contains(self, other: SupportsVec2) -> bool:
        return other in self
    def contains_exclusive(self, other: SupportsVec2) -> bool:
        return other in self and other not in self.corners

    @property
    def corners(self) -> list[Vec2]:
        def gen():
            yield self.min
            yield Vec2(self.min.x, self.max.y)
            yield self.max
            yield Vec2(self.max.x, self.min.y)
        return list(gen())

    @property
    def width(self) -> float:
        return self.max.x - self.min.x

    @property
    def height(self) -> float:
        return self.max.y - self.min.y

    @property
    def center(self) -> Vec2:
        return (self.min + self.max) / 2

    @property
    def size(self) -> Vec2:
        return Vec2(self.width, self.height)

    def __add__(self, other: Vec2) -> 'Rect':
        return Rect(self.min + other, self.max + other)
    def __sub__(self, other: Vec2) -> 'Rect':
        return Rect(self.min - other, self.max - other)

    def __str__(self) -> str:
        return repr(self)
    def __repr__(self) -> str:
        return f'Rect(min={self.min}, max={self.max})'