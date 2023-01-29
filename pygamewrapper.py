from typing import Any
from constants import *

import pygame


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
        scale = pygame.transform.scale(self._current_costume_image, (sz[0] * self.scale / 100, sz[1] * self.scale / 100))
        self.image = pygame.transform.rotate(scale, self.dir-90)

        self.rect = self.image.get_rect(center=PygameSpriteWrapper.to_py_pos(self.pos))
