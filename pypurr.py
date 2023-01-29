import inspect
import random
import threading
import time
import pygame

from typing import Any, Callable, SupportsFloat
from pygamewrapper import PygameSpriteWrapper
from constants import *

_sprite_tys: list[Any] = []


class SpriteBase:

    def __init__(self, costumes: list[str], sounds: list[str]):

        self.costumes = costumes
        self.sounds = sounds

        self._sprite = PygameSpriteWrapper(costumes)
        self._sprite.dir = 90

        self._do_block = True
        self._has_blocked = False
        self._previous_block_location: set[tuple[str, int]] = set()
        self._previous_block_time: float = _clock.get_time() / 1000

    def _find_caller(self) -> tuple[str, int] | None:
        """
        Find the identifier for the first caller external to this library.
        """

        frames = inspect.stack()

        for f in frames:
            if f.filename != __file__:
                return f.filename, f.lineno

    def _block_call(self):
        """
        Block execution based on loops and screen updates.
        In the future, this might be implemented by patching the calling code directly.
        """

        if not self._do_block:
            return

        caller = self._find_caller()

        if caller in self._previous_block_location:

            self._previous_block_location = set()

            dt = runtime() - self._previous_block_time
            if dt < 1 / frame_rate:
                wait(1 / frame_rate - dt)

            self._previous_block_time = runtime()

        self._previous_block_location.add(caller)

    #############################
    # Properties
    #############################

    @property
    def pos(self) -> pygame.Vector2:
        return self._sprite.pos

    @pos.setter
    def pos(self, v: pygame.Vector2):
        self._sprite.pos = v
        self._block_call()

    @property
    def x(self) -> float:
        return self.pos.x

    @x.setter
    def x(self, x: float):
        self.pos = pygame.Vector2(x, self.pos.y)

    @property
    def y(self) -> float:
        return self.pos.y

    @y.setter
    def y(self, y: float):
        self.pos = pygame.Vector2(self.pos.x, y)

    @property
    def size(self) -> float:
        return self._sprite.scale

    @size.setter
    def size(self, sz: float):
        self._sprite.scale = sz
        self._block_call()

    @property
    def dir(self) -> float:
        return self._sprite.dir

    @dir.setter
    def dir(self, dir: float):
        self._sprite.dir = dir
        self._block_call()

    @property
    def costume_name(self) -> str:
        return self._sprite.costume_name

    @costume_name.setter
    def costume_name(self, value: str):
        self._sprite.costume_name = value
        self._block_call()

    @property
    def pygame_sprite(self):
        return self._sprite

    ##################################
    # Methods
    ##################################

    def goto(self, x: float, y: float):
        self.pos = pygame.Vector2(x, y)

    def step(self, step: float):
        self.pos += pygame.Vector2(step, 0).rotate(self.dir)

    def change_x(self, x: float):
        self.x += x

    def change_y(self, y: float):
        self.y += y

    def change_size(self, sz: float):
        self.size += sz

    def turn_left(self, angle: float):
        self.dir -= angle

    def turn_right(self, angle: float):
        self.dir += angle


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


_when_green_flag_clicked = 'on_start'
_broadcast = 'broadcast.'


class Hooked:
    def __init__(self, f: Callable[[Sprite], None], name: str):
        self._func = f
        self._hook = name


def when_start(f: Callable[[Sprite], None]) -> Hooked:
    # print(f'Hooking {f} to start')
    return Hooked(f, _when_green_flag_clicked)


def when_receive(name: str) -> Callable[[Callable[[Sprite], None]], Hooked]:
    def inner(f: Callable[[Sprite], None]) -> Hooked:
        # print(f'Hooking {f} to receive')
        return Hooked(f, _broadcast + name)
    return inner


def synchronous(f: Callable[[Sprite], None]) -> Callable[[Sprite], None]:

    def inner(self: Sprite):

        prev = self._do_block
        self._do_block = False

        f(self)

        self._do_block = prev

    return inner


_sprites: dict[type, Sprite] = {}


def sprite(t: type) -> Sprite:
    assert issubclass(t, Sprite), 'Type provided to sprite() must be a Sprite type'
    return _sprites[t]


def broadcast(n: str):
    for s in _sprites.values():
        if _broadcast + n in s.hooks:
            _scratch_call_hook(s, _broadcast + n)


def wait(sec: float):
    time.sleep(sec)


def wait_frame():
    wait(1 / frame_rate)


def pick_random(start: SupportsFloat, end: SupportsFloat) -> float:
    return random.random() * (float(end) - float(start)) + float(start)


def _scratch_call(s: Sprite, f: Callable[[Sprite], None]):
    n = threading.Thread(target=f, args=(s,))
    n.daemon = True
    n.start()


def _scratch_call_hook(s: Sprite, n: str):
    _scratch_call(s, s.hooks[n])


_clock: pygame.time.Clock
_sys_start_time: float


def runtime() -> float:
    """
    Gets the current run-time of the game in seconds
    """
    return time.time() - _sys_start_time


def run():
    """
    Run the scratch project currently loaded in python
    """

    global _sprites, _clock, _sys_start_time

    _sys_start_time = time.time()

    pygame.init()
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('pypurr')

    _sprites = {}
    sprite_group = pygame.sprite.Group()

    _clock = pygame.time.Clock()

    for t in _sprite_tys:
        print(f'Creating sprite {t}')
        s: Sprite = t()
        _sprites[t] = s
        sprite_group.add(s.pygame_sprite)

    for s in _sprites.values():
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

        _clock.tick(frame_rate)

