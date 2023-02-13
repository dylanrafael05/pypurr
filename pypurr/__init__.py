import time as time
import typing as typing
from random import random as random
import pyglet as pg

from . import ping
from . import object
from . import window
from . import resource


def pick_random(start: typing.SupportsFloat, end: typing.SupportsFloat) -> float:
    """
    Returns a random number between init and end
    """
    return random() * (float(end) - float(start)) + float(start)


def runtime() -> float:
    """
    Gets the current run_project-time of the game in seconds
    """
    return time.time() - _sys_start_time


def dt() -> float:
    """
    Gets the current delta time of this application
    """
    return pg.clock.get_default().time() - pg.clock.get_default().last_ts


def fps() -> float:
    """
    Gets the current FPS of this application
    """
    return 1 / dt()


_sys_start_time: float


def run_project():
    """
    Run the current pypurr app
    """

    global _sys_start_time

    _sys_start_time = time.time()

    resource.init()
    window.init()

    for k in object.GameObject.initializers:
        k()

    for k in object.all_singleton_types:
        k()

    pg.clock.schedule_interval(window.cur.on_frame, 1 / 60)

    pg.app.run()


