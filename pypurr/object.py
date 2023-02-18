import abc
import sys
import time
import traceback
import pyglet as pg
from typing import Any, ParamSpec, Callable, Concatenate, Generator, Type, TypeVar, Final, Generic, Union

from . import math, window, resource


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
main_group = pg.graphics.Group()


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
            new_ty.instance = None
            new_ty.__annotations__['instance'] = new_ty

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


class OnlyOne(GameObject):

    __abstract__ = True
    __singleton__ = True

    instance: 'OnlyOne'


class Object2D(GameObject):

    __abstract__ = True

    def __init__(self):

        super().__init__()

        self.rot = 90

        self._pos = math.Vec2()
        self.true_scale = 1

    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, value: math.SupportsVec2):
        self._pos = math.vec2(value)

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
        return self.true_scale * 100
    @scale.setter
    def scale(self, value):
        self.true_scale = value / 100

    def apply_to(self, obj: pg.text.Label | pg.sprite.Sprite):
        
        x, y = math.to_screen(self._pos)

        obj.x = x
        obj.y = y

        obj.rotation = self.rot + 90

        obj.scale = self.true_scale


class Label2D(Object2D):

    def __init__(self):

        super().__init__()

        self.label = pg.text.Label(batch=main_batch, group=main_group)

        self.text = ""

    def prepare_render(self):

        self.label.text = self.text
        self.apply_to(self.label)

    def __del__(self):
        self.label.delete()


class Sprite2D(Object2D):

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

    def __init__(self, *, group=None):

        super().__init__()

        self.image_num = 0

        self.pos = pg.math.Vec2()
        self.dir = 0
        self.scale = 100

        group = group or main_group

        self.sprite = pg.sprite.Sprite(self.images[0], batch=main_batch, group=group)


    def prepare_render(self):

        image: pg.image.AbstractImage = self.images[self.image_num]
        self.sprite.image = image

        self.apply_to(self.sprite)

    @property
    def image_name(self) -> str:
        return self.img_names[self.image_num]
    @image_name.setter
    def image_name(self, value: str):
        self.image_num = self.img_names.index(value)

    @property
    def rect(self):
        size_vec = math.Vec2(
            self.true_scale * self.sprite.image.width,
            self.true_scale * self.sprite.image.height
        )
        return math.Rect(self.pos - size_vec / 2, self.pos + size_vec / 2)

    def touching(self, other: 'SupportsObject') -> bool:
        other = gameobject(other)
        assert isinstance(other, Sprite2D), "Cannot check if a sprite is touching a non-sprite"
        return (self.rect @ other.rect) is not None

    def _pixperf_touching(self, other: 'Sprite2D'):

        selfrect, otherrect = self.rect / self.true_scale, other.rect / other.true_scale
        inter = selfrect @ otherrect

        if inter:

            selfdata: pg.image.ImageData  = self.sprite.image.get_image_data()
            otherdata: pg.image.ImageData = other.sprite.image.get_image_data()

            selfd:  bytes = selfdata.get_data('RGBA', selfdata.width*4)
            otherd: bytes = otherdata.get_data('RGBA', otherdata.width)

            selfnorm  = inter - selfrect.min
            othernorm = inter - otherrect.min

            for i in range(round(inter.width)):
                for j in range(round(inter.height)):

                    selfx = round(i + selfnorm.min.x)
                    selfy = round(j + selfnorm.min.y)

                    otherx = round(i + othernorm.min.x)
                    othery = round(j + othernorm.min.y)

                    selfi = (selfx*selfdata.width+selfy)*4+3
                    otheri = (otherx*otherdata.width+othery)*4+3

                    if selfd[selfi] > 0 and otherd[otheri] > 0:
                        return True

        return False





class Particle2D(Sprite2D):

    __abstract__ = True

    costume: str

    _group: pg.graphics.TextureGroup

    @classmethod
    def __type_init__(cls):

        if not hasattr(cls, 'costume'):
            raise TypeError(f'{cls.__name__}: particles must have only one costume!')

        cls.costumes = [cls.costume]

        super().__type_init__()

        cls._group = pg.graphics.TextureGroup(cls.images[0], parent=main_group)

    def __init__(self):

        super().__init__(group=self._group)


SupportsObject = Type[OnlyOne] | GameObject

def gameobject(x: SupportsObject, /) -> GameObject:
    if isinstance(x, GameObject):
        return x
    else:
        assert x.__singleton__, "Cannot get a game object from a non-singleton type"
        return x.instance

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