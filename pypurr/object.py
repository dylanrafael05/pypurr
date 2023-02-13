import abc
import sys
import time
import traceback
import pyglet as pg
from typing import Any, ParamSpec, Callable, Concatenate, Generator, Type, TypeVar, Final, Generic, Union

from . import mathpr, window, resource


class Hooked:
    def __init__(self, f: 'Procedure', name: str):
        self.func = f
        self.hook = name


class HookError(BaseException):
    pass


all_singleton_types: list[Type['GameObject']] = []
dead_objects: list['GameObject'] = []
new_objects: list['GameObject'] = []


def kill_object(o: 'GameObject'):
    global objects_by_type, all_objects

    objects_by_type[o.__class__].remove(o)
    all_objects.remove(o)


def start_object(o: 'GameObject'):
    global objects_by_type, all_objects

    if o.__class__ not in objects_by_type:
        objects_by_type[o.__class__] = []

    objects_by_type[o.__class__] += [o]
    all_objects += [o]


main_batch = pg.graphics.Batch()


def is_abstract(t):
    return '__abstract__' in t.__dict__ and t.__dict__['__abstract__'] is True


class GameObjectMeta(type):

    def __new__(mcs, name: str, bases: tuple[type, ...], dct: dict[str, Any]) -> type:

        global all_singleton_types

        new_ty = super().__new__(mcs, name, bases, dct)

        if '__abstract__' in dct and dct['__abstract__'] is True:
            old_init = new_ty.__init__ #type: ignore
            def init(self, *args, **kwargs):
                if is_abstract(self.__class__):
                    raise NotImplementedError(f'Cannot create an instance of the base sprite type {self.__class__.__name__}')
                else:
                    old_init(self, *args, **kwargs)
            new_ty.__init__ = init
            return new_ty

        new_ty.hooks = {}

        forbidden_hooks = getattr(new_ty, '_forbidden_hooks') if hasattr(new_ty, '_forbidden_hooks') else set()

        for i in dct.values():
            if isinstance(i, Hooked):
                if i.hook in forbidden_hooks:
                    raise HookError(f'Cannot create hook {i.hook} for type {new_ty.__name__}: it is forbidden!')
                if i.hook not in new_ty.hooks:
                    new_ty.hooks[i.hook] = []
                new_ty.hooks[i.hook].append(i.func)

        if hasattr(new_ty, '__singleton__') and getattr(new_ty, '__singleton__') is True:
            all_singleton_types += [new_ty]

        if hasattr(new_ty, '__type_init__'):
            GameObject.initializers += [getattr(new_ty, '__type_init__')]

        return new_ty


class GameObject(metaclass=GameObjectMeta):

    initializers: list[Callable[[], None]] = []

    __abstract__ = True
    __singleton__ = False

    def __init__(self):

        global new_objects

        self._procedures_to_start: list['Procedure'] = []
        self._active_procedures: dict['ProcCall', 'ProcedureDelay'] = {}

        if self.__class__.__singleton__ and self.__class__ in objects_by_type:
            raise ValueError(f'Cannot create duplicate instance of singleton class {self.__class__}')

        new_objects += [self]

        self._live = False
        self._dead = False

    def delete(self):
        global dead_objects

        dead_objects += [self]
        self._dead = True

    def run(self, p):
        if not isinstance(p, Procedure):
            p()
        else:
            self._procedures_to_start.append(p)

    def run_hook(self, hook: str):
        if hook not in self.hooks:
            return

        for k in self.hooks[hook]:
            self.run(k)

    def start(self):
        pass

    def prepare_render(self):
        pass

    def update(self):
        pass

    def on_frame(self):

        if self._dead:
            return

        if not self._live:
            self.run(self.start)
            self._live = True
        else:
            self.run(self.update)

        to_remove = []
        started = []

        # Run current procedures
        for cur_proc, cur_delay in self._active_procedures.items():

            if cur_delay.is_finished():
                cur_delay = next(cur_proc)
                if cur_delay is None or cur_delay is cur_proc:
                    to_remove.append(cur_proc)
                else:
                    cur_delay.mark_used()

        # Start new procedures
        for cur_proc_s in self._procedures_to_start:

            cur_proc = cur_proc_s.start(self)
            cur_delay = next(cur_proc)

            if cur_delay is None:
                continue

            if cur_delay is not cur_proc:
                self._active_procedures[cur_proc] = cur_delay
                cur_delay.mark_used()
                started.append(cur_proc_s)

        # Handle removals
        for p in to_remove:
            del self._active_procedures[p]

        for p in started:
            self._procedures_to_start.remove(p)


objects_by_type: dict[Type['GameObject'], list['GameObject']] = {}
all_objects: list['GameObject'] = []


class Singleton(GameObject):

    __abstract__ = True
    __singleton__ = True


class Object2D(GameObject):

    __abstract__ = True

    def __init__(self):

        super().__init__()

        self.rot = 90

        self._pos = mathpr.Vec2()
        self._true_scale = 1

    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, value: tuple[int|float, int|float] | mathpr.Vec2):
        if isinstance(value, tuple):
            self._pos = mathpr.Vec2(value[0], value[1])
        else:
            self._pos = value

    @property
    def x(self):
        return self._pos.x
    @x.setter
    def x(self, value):
        self._pos.x = value

    @property
    def y(self):
        return self._pos.y
    @y.setter
    def y(self, value):
        self._pos.y = value

    @property
    def scale(self):
        return self._true_scale * 100
    @scale.setter
    def scale(self, value):
        self._true_scale = value / 100

    def apply_to(self, obj: pg.text.Label | pg.sprite.Sprite):
        
        x, y = mathpr.to_screen(self._pos)
        print(f'{x}, {y}')

        obj.x = x
        obj.y = y

        obj.rotation = self.rot + 90

        obj.scale = self._true_scale


class Label2D(Object2D):

    def __init__(self):

        super().__init__()

        self.label = pg.text.Label(batch=main_batch)

        self.text = ""

    def prepare_render(self):

        self.label.text = self.text
        self.apply_to(self.label)

    def __del__(self):
        self.label.delete()


class Image2D(Object2D):

    costumes = ()

    image_map: dict[str, pg.image.AbstractImage]
    images: list[pg.image.AbstractImage]

    @classmethod
    def __type_init__(cls):

        cls.image_map = {c: resource.image(c) for c in (cls.costumes or [])}
        cls.images    = list(cls.image_map.values())
        cls.img_names = list(cls.image_map.keys())

        for i in cls.image_map.values():
            i.anchor_x = i.width  // 2
            i.anchor_y = i.height // 2

    def __init__(self):

        super().__init__()

        self.image_idx = 0

        self.pos = pg.math.Vec2()
        self.dir = 0
        self.scale = 100

        self.sprite = pg.sprite.Sprite(self.images[0], batch=main_batch)


    def prepare_render(self):

        image: pg.image.AbstractImage = self.images[self.image_idx]
        self.sprite.image = image

        self.apply_to(self.sprite)

    @property
    def img_name(self) -> str:
        return self.img_names[self.image_idx]
    @img_name.setter
    def img_name(self, value: str):
        self.image_idx = self.img_names.index(value)


#########################################
# Procedures and delays
#########################################
ProcCall = Generator['ProcedureDelay', None, None]


class Procedure:
    """
    Thinly wraps a generator.
    This class cannot be called like a function.
    """

    def __init__(self, f: Callable[[GameObject], ProcCall]):
        self._producer = f

    def __call__(self):
        raise NotImplementedError('Procedures cannot be called like functions; use .init() instead')

    def start(self, go: GameObject):
        return self._producer(go)


P_spc = ParamSpec('P_spc')
class _ProcedureDecorator(Generic[P_spc]):

    def __call__(self, f: Callable[Concatenate[GameObject, P_spc], ProcCall]) -> Procedure:

        def new_fn(go, *args : P_spc.args, **kwargs : P_spc.kwargs) -> ProcCall:
            yield from f(go, *args, **kwargs)
            yield None

        return Procedure(new_fn)

    # noinspection PyMethodMayBeStatic
    def forever(self, f: Callable[Concatenate[GameObject, P_spc], Union[None, ProcCall]]) -> Procedure:

        def new_fn(go, *args : P_spc.args, **kwargs : P_spc.kwargs) -> ProcCall:
            while True:
                x = f(go, *args, **kwargs)
                if x is not None:
                    yield from x
                yield delay()

        return Procedure(new_fn)

proc: Final[_ProcedureDecorator] = _ProcedureDecorator()


class ProcedureDelay(abc.ABC):

    def __init__(self):
        self._used = False
        self._source = traceback.extract_stack()

    def __del__(self):
        if self._used is False:
            sys.stderr.write('Procedure delay unused! Could you have meant to yield it?\n')
            if self._source:
                for line in traceback.format_list(self._source):
                    sys.stderr.write('\t' + line)

    def mark_used(self):
        self._used = True

    @abc.abstractmethod
    def is_finished(self) -> bool: ...


def delay() -> ProcedureDelay:
    """
    Return a procedure delay which waits for one frame to pass
    """
    return DelayFrameImpl()


class DelayFrameImpl(ProcedureDelay):

    def __init__(self):
        super().__init__()

    def is_finished(self) -> bool:
        return True


def wait(sec: float) -> ProcedureDelay:
    """
    Return a procedure delay which waits for the given amount of time
    """
    return WaitImpl(sec)


class WaitImpl(ProcedureDelay):

    def __init__(self, sec: float):
        super().__init__()
        self._start_t = time.time()
        self._sec = sec

    def is_finished(self) -> bool:
        return time.time() - self._start_t >= self._sec


def wait_until(f: Callable[[], bool]) -> ProcedureDelay:
    """
    Return a procedure delay which waits for the given amount of time
    """
    return WaitUntilImpl(f)


class WaitUntilImpl(ProcedureDelay):

    def __init__(self, f: Callable[[], bool]):
        super().__init__()
        self._f = f

    def is_finished(self) -> bool:
        return self._f()


###############################################
# Hook generators
###############################################
def when_receive(name: str) -> Callable[[Callable[[GameObject], ProcCall]], Hooked]:
    def inner(f: Callable[[GameObject], ProcCall]) -> Hooked:
        return Hooked(proc(f), 'receive<' + name + '>')
    return inner


##############################################
# Object interfaces
##############################################
_T_go = TypeVar('_T_go', bound='GameObject')


def singleton(t: Type[_T_go]) -> _T_go:
    """
    Get the instance of a singleton type
    """

    if not t.__singleton__:
        raise ValueError(f"Cannot get singleton instance of non-singleton type {t.__name__}")

    return objects_by_type[t][0]


def objects(t: Type[_T_go]) -> list[_T_go]:
    """
    Get all objects of a specified non-singleton object type
    """

    assert not t.__singleton__, f"Cannot get instances of singleton type {t.__name__}"
    return objects_by_type[t] or []


def broadcast(n: str):
    """
    Broadcasts a message to all receivers
    """

    hook_name = 'receive<' + n + '>'

    for s in all_objects:
        s.run_hook(hook_name)


def render():
    """
    Render all the current objects
    """

    for k in all_objects:
        k.prepare_render()

    main_batch.draw()