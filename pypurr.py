import inspect
import os
import random
import re
import textwrap
import threading
import time
import pygame

from typing import Any, Callable, SupportsFloat, TypeAlias, Literal
from constants import *


###############################
# Pygame Interface
###############################
class PygameSpriteWrapper(pygame.sprite.Sprite):

    @staticmethod
    def to_py_pos(pos: pygame.Vector2) -> pygame.Vector2:
        return pygame.Vector2(pos.x + size[0] / 2, -pos.y + size[1] / 2)

    def __init__(self, costumes: list[str]):

        super().__init__()

        self._costume_map = {c: pygame.image.load(c).convert_alpha() for c in costumes}

        self._costume_idx_to_name = {i: costumes[i] for i in range(len(costumes))}
        self._costume_name_to_idx = {v: k for k, v in self._costume_idx_to_name.items()}

        self._costume_images = list(self._costume_map.values())

        self._costume_index = 0
        self._costume_name = list(self._costume_map.keys())[0]

        self._current_costume_image = self._costume_images[self._costume_index]
        self.image = self._current_costume_image

        self._scale: float = 100

        self.pos = pygame.Vector2(0, 0)
        self.dir: float = 90

        self.rect = self.image.get_rect(center=PygameSpriteWrapper.to_py_pos(self.pos))

    @property
    def scale(self) -> float:
        return self._scale

    @scale.setter
    def scale(self, scale: float):
        if scale > 200:
            self._scale = 200
        elif scale < 1:
            self._scale = 1
        else:
            self._scale = scale

    def next_costume(self):
        self._costume_index += 1

        if self._costume_index >= self.costume_count:
            self._costume_index = 0

        self.costume_index = self._costume_index

    @property
    def costume_count(self) -> int:
        return len(self._costume_images)

    @property
    def costume_name(self) -> str:
        return self._costume_name

    @costume_name.setter
    def costume_name(self, value):
        if value in self._costume_map:
            self._costume_name = value
            self._current_costume_image = self._costume_map[value]
            self._costume_index = self._costume_name_to_idx[value]

    @property
    def costume_index(self) -> int:
        return self._costume_index

    @costume_index.setter
    def costume_index(self, value: int):
        if 0 <= value < self.costume_count:
            self._costume_index = value
            self._current_costume_image = self._costume_images[value]
            self._costume_name = self._costume_idx_to_name[value]

    def update(self, *args: Any, **kwargs: Any) -> None:

        sz = self._current_costume_image.get_size()
        scale = pygame.transform.scale(self._current_costume_image,
                                       (sz[0] * self.scale / 100, sz[1] * self.scale / 100))
        self.image = pygame.transform.rotate(scale, self.dir - 90)

        self.rect = self.image.get_rect(center=PygameSpriteWrapper.to_py_pos(self.pos))

#########################################
# User interface
#########################################
_main_sync = threading.Event()
_sprite_tys: list[Any] = []
_sprites: dict[type, 'Sprite'] = {}


class SpriteBase:

    def __init__(self, costumes: list[str], sounds: list[str]):

        self.costumes = costumes
        self.sounds = sounds

        self._sprite = PygameSpriteWrapper(costumes)

    #############################
    # Properties
    #############################

    @property
    def pos(self) -> pygame.Vector2:
        return self._sprite.pos

    @pos.setter
    def pos(self, v: pygame.Vector2):
        self._sprite.pos = v

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

    @property
    def dir(self) -> float:
        return self._sprite.dir

    @dir.setter
    def dir(self, dir: float):
        self._sprite.dir = dir

    @property
    def costume_name(self) -> str:
        return self._sprite.costume_name

    @costume_name.setter
    def costume_name(self, value: str):
        self._sprite.costume_name = value

    @property
    def costume_index(self) -> int:
        return self._sprite.costume_index

    @costume_index.setter
    def costume_index(self, value: int):
        self._sprite.costume_index = value

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

    def next_costume(self):
        self._sprite.next_costume()


#########################################
# User Metaclass
#########################################
class SpriteMeta(type):

    def __new__(mcs, name: str, bases: tuple[type, ...], dct: dict[str, Any]) -> type:

        new_ty = super().__new__(mcs, name, bases, dct)
        if name == 'Sprite':
            return new_ty

        new_ty.hooks = {}

        for i in dct.values():
            if isinstance(i, Hooked):
                if i.hook not in new_ty.hooks:
                    new_ty.hooks[i.hook] = []
                new_ty.hooks[i.hook].append(i.func)

        new_ty.__init__ = lambda s: Sprite.__init__(
            s,
            dct['costumes'] if 'costumes' in dct else [],
            dct['sounds']   if 'sounds'   in dct else []
        )

        _sprite_tys.append(new_ty)

        return new_ty


class Sprite(SpriteBase, metaclass=SpriteMeta):
    pass

#########################################
# Internal Representation
#########################################
_when_green_flag_clicked = 'on_start'
_broadcast = 'broadcast.'


def _scratch_block_bool(b: bool) -> bool:
    """
    A simple function which waits for synchronization, then returns its argument.
    Used in the code generated by _scratch_make_async
    """
    _main_sync.wait()
    return b


def _scratch_make_async(f: Callable[[Sprite, ...], None]) -> Callable[[Sprite, ...], None]:
    """
    Modify the source function in order to produce a new function which blocks on loops.
    This code should only be called while setting up a program.
    """

    # Get source code
    code = inspect.getsource(f)
    code = textwrap.dedent(code)

    # Skip first decorator
    # TODO: handle multiline decorators!
    if code.startswith('@'):
        code_first_eol = code.find('\n')
        code = code[code_first_eol:]

    # Get import name
    import_name      = os.path.basename(__file__)
    import_name, ext = os.path.splitext(import_name)

    # Patch to include blocking loops
    code = f'import {import_name} as __IMPL__' + code
    code = re.sub(r'(?<=while)\s+(.+)(?=:)', r'(__IMPL__._scratch_block_bool(\1))', code)

    # Get module to execute into
    mod = dict(getattr(f, '__globals__'))

    # Execute patched code
    new_code = compile(code, '<async-builder>', 'exec')
    exec(new_code, mod)

    # Extract and return new function
    new_fn = mod[f.__name__]
    return new_fn


#########################################
# Hooks and Calls
#########################################
class Hooked:
    def __init__(self, f: Callable[[Sprite], None], name: str):
        self.func = f
        self.hook = name


def when_start(f: Callable[[Sprite], None]) -> Hooked:
    # print(f'Hooking {f} to start')
    return Hooked(_scratch_make_async(f), _when_green_flag_clicked)


def when_receive(name: str) -> Callable[[Callable[[Sprite], None]], Hooked]:
    def inner(f: Callable[[Sprite], None]) -> Hooked:
        # print(f'Hooking {f} to receive')
        return Hooked(_scratch_make_async(f), _broadcast + name)
    return inner


def _scratch_call(s: Sprite, f: Callable[[Sprite], None]):
    n = threading.Thread(target=lambda: f(s))
    n.daemon = True
    n.start()


def _scratch_call_hook(s: Sprite, n: str):
    for k in s.hooks[n]:
        _scratch_call(s, k)


#########################################
# Global User Functions: Basic
#########################################
def sprite(t: type) -> Sprite:
    """
    Get the sprite of a given type
    """
    assert issubclass(t, Sprite), 'Type provided to sprite() must be a Sprite type'
    return _sprites[t]


def broadcast(n: str):
    """
    Broadcasts a message to all receivers
    """
    for s in _sprites.values():
        if _broadcast + n in s.hooks:
            _scratch_call_hook(s, _broadcast + n)


def wait(sec: float):
    """
    Waits for the given amount of seconds
    """
    time.sleep(sec)


def pick_random(start: SupportsFloat, end: SupportsFloat) -> float:
    """
    Returns a random number between start and end
    """
    return random.random() * (float(end) - float(start)) + float(start)


def runtime() -> float:
    """
    Gets the current run-time of the game in seconds
    """
    return time.time() - _sys_start_time


#########################################
# Global User Functions: Mouse
#########################################
def mouse_x() -> int:
    """
    Get the x-position of the mouse in pypurr coordinates
    """
    return pygame.mouse.get_pos()[0] - size[0] / 2


def mouse_y() -> int:
    """
    Get the y-position of the mouse in pypurr coordinates
    """
    return pygame.mouse.get_pos()[1] - size[1] / 2


#########################################
# Global User Functions: Keyboard
#########################################
Key: TypeAlias = Literal[
    'a', 'b', 'c', 'd', 'e',
    'f', 'g', 'h', 'i', 'j',
    'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't',
    'u', 'v', 'w', 'x', 'y',
    'z', 'space',
    '0', '1', '2', '3', '4',
    '5', '6', '7', '8', '9',
    'left', 'right', 'up', 'down'
]


def key_pressed(k: Key) -> bool:
    """
    Get if the given key is being pressed or not
    """
    return k in _keys_down_active


def key_down(k: Key) -> bool:
    """
    Get if the given key was just pressed or not
    """
    return k in _keys_just_down_active


def key_up(k: Key) -> bool:
    """
    Get if the given key was just released or not
    """
    return k in _keys_just_up_active


def _pygame_key(k: int) -> Key:
    """
    Convert a pygame key to a corresponding pypurr key
    """
    match k:
        # Numeric keys
        case pygame.K_0: return '0'
        case pygame.K_1: return '1'
        case pygame.K_2: return '2'
        case pygame.K_3: return '3'
        case pygame.K_4: return '4'
        case pygame.K_5: return '5'
        case pygame.K_6: return '6'
        case pygame.K_7: return '7'
        case pygame.K_8: return '8'
        case pygame.K_9: return '9'

        # Characters
        case pygame.K_a: return 'a'
        case pygame.K_b: return 'b'
        case pygame.K_c: return 'c'
        case pygame.K_d: return 'd'
        case pygame.K_e: return 'e'
        case pygame.K_f: return 'f'
        case pygame.K_g: return 'g'
        case pygame.K_h: return 'h'
        case pygame.K_i: return 'i'
        case pygame.K_j: return 'j'
        case pygame.K_k: return 'k'
        case pygame.K_l: return 'l'
        case pygame.K_m: return 'm'
        case pygame.K_n: return 'n'
        case pygame.K_o: return 'o'
        case pygame.K_p: return 'p'
        case pygame.K_q: return 'q'
        case pygame.K_r: return 'r'
        case pygame.K_s: return 's'
        case pygame.K_t: return 't'
        case pygame.K_u: return 'u'
        case pygame.K_v: return 'v'
        case pygame.K_w: return 'w'
        case pygame.K_x: return 'x'
        case pygame.K_y: return 'y'
        case pygame.K_z: return 'z'

        # Special
        case pygame.K_SPACE: return 'space'
        case pygame.K_LEFT:  return 'left'
        case pygame.K_RIGHT: return 'right'
        case pygame.K_UP:    return 'up'
        case pygame.K_DOWN:  return 'down'


##################################
# Main Functionality
##################################
_clock: pygame.time.Clock
_sys_start_time: float

_keys_just_down: set[Key] = set()
_keys_just_up: set[Key] = set()
_keys_down: set[Key] = set()

_keys_down_active: set[Key] = set()
_keys_just_down_active: set[Key] = set()
_keys_just_up_active: set[Key] = set()


def handle_event(ev: pygame.event.Event):
    """
    Handle one event
    """
    if ev.type == pygame.KEYDOWN:
        _keys_just_down.add(_pygame_key(ev.key))
    elif ev.type == pygame.KEYUP:
        _keys_just_up.add(_pygame_key(ev.key))


def start_events():
    """
    Prepare to handle all events
    """
    global _keys_just_up, _keys_just_down

    _keys_just_up = set()
    _keys_just_down = set()


def finalize_events():
    """
    Finish up handling of events
    """
    global _keys_down, _keys_down_active, _keys_just_down_active, _keys_just_up_active

    _keys_down.difference_update(_keys_just_up)
    _keys_down.update(_keys_just_down)

    _keys_down_active = set(_keys_down)
    _keys_just_down_active = set(_keys_just_down)
    _keys_just_up_active = set(_keys_just_up)


def run():
    """
    Run the pypurr project currently loaded
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
        s: Sprite = t()
        _sprites[t] = s
        sprite_group.add(s.pygame_sprite)

    for s in _sprites.values():
        _scratch_call_hook(s, _when_green_flag_clicked)

    while True:
        events = pygame.event.get()
        start_events()

        for e in events:

            if e.type == pygame.QUIT:
                pygame.quit()
                return

            handle_event(e)

        finalize_events()

        _main_sync.set()
        _main_sync.clear()

        sprite_group.update()
        screen.fill((0, 0, 0))
        sprite_group.draw(screen)

        pygame.display.update()

        _clock.tick(frame_rate)

