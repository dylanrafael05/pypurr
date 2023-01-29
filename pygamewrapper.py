from typing import Any
from constants import *

import pygame


class PygameSpriteWrapper(pygame.sprite.Sprite):

    @staticmethod
    def to_py_pos(pos: pygame.Vector2) -> pygame.Vector2:
        return pygame.Vector2(pos.x + size[0] / 2, -pos.y + size[1] / 2)

    def __init__(self, costumes: list[str]):

        super().__init__()

        self.images = {c: pygame.image.load(c).convert_alpha() for c in costumes}
        self.image = list(self.images.values())[0]
        self.base_image = self.image

        self._scale: float = 100
        self._costume_name = list(self.images.keys())[0]

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

    @property
    def costume_name(self) -> str:
        return self._costume_name
    
    @costume_name.setter
    def costume_name(self, value):
        if value in self.images:
            self._costume_name = value
            self.base_image = self.images[value]

    def update(self, *args: Any, **kwargs: Any) -> None:

        sz = self.base_image.get_size()
        scale = pygame.transform.scale(self.base_image, (sz[0] * self.scale / 100, sz[1] * self.scale / 100))
        self.image = pygame.transform.rotate(scale, self.dir-90)

        self.rect = self.image.get_rect(center=PygameSpriteWrapper.to_py_pos(self.pos))
