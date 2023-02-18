from . import window, math


def key_pressed(key: str) -> bool:
    if key not in window.cur.key:
        return False
    return window.cur.key[key] and (key not in window.cur.prev_key or not window.cur.prev_key[key])


def key_down(key: str) -> bool:
    if key not in window.cur.key:
        return False
    return window.cur.key[key]


def key_up(key: str) -> bool:
    if key not in window.cur.key:
        return True
    return not window.cur.key[key]


def mouse_pressed(button: str) -> bool:
    if button not in window.cur.mouse:
        return False
    return window.cur.mouse[button] and (button not in window.cur.prev_mouse or not window.cur.prev_mouse[button])


def mouse_down(button: str) -> bool:
    if button not in window.cur.mouse:
        return False
    return window.cur.mouse[button]


def mouse_up(button: str) -> bool:
    if button not in window.cur.mouse:
        return True
    return not window.cur.mouse[button]


def mouse_pos() -> math.Vec2:
    return window.cur.mouse_coord


def mouse_x() -> float:
    return mouse_pos().x


def mouse_y() -> float:
    return mouse_pos().y