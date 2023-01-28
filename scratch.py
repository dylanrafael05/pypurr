import threading
import time
from typing import Any, Callable
from constants import *

import pygame

from pygamewrapper import PygameSpriteWrapper

_sprite_tys: list[Any] = []


class SpriteBase:

    def __init__(self, costumes: list[str], sounds: list[str]):

        self.costumes = costumes
        self.sounds = sounds

        self._sprite = PygameSpriteWrapper(costumes)

        self.dir = 0

    def _update(self):
        self._sprite.update()

    def _block(self):
        time.sleep(1 / frame_rate)

    @property
    def _pos(self) -> pygame.Vector2:
        return self._sprite.pos

    @_pos.setter
    def _pos(self, v: pygame.Vector2):
        self._sprite.pos = v

    # Publicly accessable methods
    def wait(self, sec: float):
        time.sleep(sec)

    def goto(self, x: float, y: float):
        self._pos = pygame.Vector2(x, y)
        self._block()

    def set_x(self, x: float):
        self._pos = pygame.Vector2(x, self._pos.y)
        self._block()

    def set_y(self, y: float):
        self._pos = pygame.Vector2(self._pos.x, y)
        self._block()

    def change_x(self, x: float):
        self._pos = pygame.Vector2(self._pos.x + x, self._pos.y)
        self._block()

    def change_y(self, y: float):
        self._pos = pygame.Vector2(self._pos.x, self._pos.y + y)
        self._block()

    def broadcast(self, name: str):
        _scratch_broadcast(name)


class SpriteMeta(type):

    def __new__(mcs, name: str, bases: tuple[type, ...], dct: dict[str, Any]) -> type:

        new_ty = super().__new__(mcs, name, bases, dct)
        if name == 'Sprite':
            return new_ty

        new_ty.hooks = {}

        for i in dct.values():
            if hasattr(i, '_hook'):
                new_ty.hooks[getattr(i, '_hook')] = getattr(i, '_func')

        new_ty.__init__ = lambda s: Sprite.__init__(
            s,
            dct['costumes'] if 'costumes' in dct else [],
            dct['sounds']   if 'sounds'   in dct else []
        )

        _sprite_tys.append(new_ty)

        return new_ty


class Sprite(SpriteBase, metaclass=SpriteMeta):
    pass


_when_green_flag_clicked = '_wgfc'
_broadcast = '_bc_'

def make_hooked(f, name):

    class Hooked:
        def __init__(self):
            self._func = f
            self._hook = name

    return Hooked()


def when_open(f):
    print(f'Hooking {f} to start')
    return make_hooked(f, _when_green_flag_clicked)


def when_receive(name: str):
    def inner(f):
        print(f'Hooking {f} to receive')
        return make_hooked(f, _broadcast + name)
    return inner


sprites: list[Sprite] | None = None


def _scratch_broadcast(n: str):
    for s in sprites:
        if _broadcast + n in s.hooks:
            _scratch_call_hook(s, _broadcast + n)


def _scratch_call(s: Sprite, f: Callable[[Sprite], None]):
    n = threading.Thread(target=f, args=(s,))
    n.daemon = True
    n.start()


def _scratch_call_hook(s: Sprite, n: str):
    _scratch_call(s, s.hooks[n])


def run_scratch():

    global sprites

    pygame.init()
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('pypurr')
    clock = pygame.time.Clock()

    sprites = []
    sprite_group = pygame.sprite.Group()

    for t in _sprite_tys:
        print(f'Creating sprite {t}')
        s: Sprite = t()
        sprites.append(s)
        sprite_group.add(s._sprite)

    for s in sprites:
        _scratch_call(s, s.hooks[_when_green_flag_clicked])

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                return

        sprite_group.update()
        screen.fill((0, 0, 0))
        sprite_group.draw(screen)

        pygame.display.update()

        clock.tick(frame_rate)

