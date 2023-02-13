import pyglet as pg

from . import object, mathpr


cur: 'PypurrWindow'
window_size: (int, int) = 1600 // 2, 900 // 2


def init():

    global cur

    cur = PypurrWindow()
    cur.set_caption('PyPurr')
    cur.set_size(window_size[0], window_size[1])

    cur.set_minimum_size(window_size[0], window_size[1])
    cur.set_maximum_size(window_size[0], window_size[1])


class PypurrWindow(pg.window.Window):

    def __init__(self):

        super().__init__()

        self.key = {}
        self.prev_key = {}

        self.mouse_coord = mathpr.Vec2(0, 0)

        self.mouse = {}
        self.prev_mouse = {}

    def on_frame(self, _):

        cur_objs = object.all_objects + object.new_objects

        while len(cur_objs) > 0:

            for o in cur_objs:
                o.on_frame()

            for o in object.new_objects:
                object.start_object(o)
            for o in object.dead_objects:
                object.kill_object(o)

            cur_objs = object.new_objects

            object.dead_objects = []
            object.new_objects = []

        self.prev_key = dict(self.key)
        self.prev_mouse = dict(self.mouse)

    # noinspection PyMethodOverriding
    def on_draw(self):
        self.clear()
        object.render()

    def on_key_press(self, symbol, modifiers):
        self.key[pg.window.key.symbol_string(symbol).lower()] = True

    def on_key_release(self, symbol, modifiers):
        self.key[pg.window.key.symbol_string(symbol).lower()] = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_coord = mathpr.from_screen(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse[pg.window.mouse.buttons_string(button).lower()] = True

    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse[pg.window.mouse.buttons_string(button).lower()] = False
