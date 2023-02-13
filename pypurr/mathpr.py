from . import window
import pyglet.math as pgm


Vec2 = pgm.Vec2


_scr_mod_x = (window.window_size[0] // 2)
_scr_mod_y = (window.window_size[1] // 2)


def from_screen(x, y) -> Vec2:
    return Vec2(x - _scr_mod_x, y - _scr_mod_y)


def to_screen(v) -> (float, float):
    return v.x + _scr_mod_x, v.y + _scr_mod_y


for k in ((a, b) for a in range(100) for b in range(100)):
    assert to_screen(from_screen(k[0], k[1])) == k