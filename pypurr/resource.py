import dataclasses
import pyglet as pg

loaded_resources = {}


def init():
    pg.resource.path = ['./res/']
    pg.resource.reindex()


@dataclasses.dataclass(eq=True, frozen=True)
class ImageOptions:
    name: str
    flip_x: bool
    flip_y: bool
    rotate: int
    atlas: bool
    border: int


def image(name: str,
          flip_x: bool = False,
          flip_y: bool = True,
          rotate: int = 0,
          atlas: bool = True,
          border: int = 1) -> pg.image.AbstractImage:
    """
    Load an image from the /res folder
    """

    options = ImageOptions(name, flip_x, flip_y, rotate, atlas, border)

    if options not in loaded_resources:
        loaded_resources[options] = pg.resource.image(name, flip_x, flip_y, rotate, atlas, border)

    return loaded_resources[options]


@dataclasses.dataclass(eq=True, frozen=True)
class MediaOptions:
    name: str
    streaming: bool


def media(name: str,
          streaming: bool = False):
    """
    Load a media file from the /res folder
    """

    options = MediaOptions(name, streaming)

    if options not in loaded_resources:
        loaded_resources[options] = pg.resource.media(name, streaming)

    return loaded_resources[options]