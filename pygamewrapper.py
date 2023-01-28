from typing import Any
from constants import *

import pygame


class PygameSpriteWrapper(pygame.sprite.Sprite):

    @staticmethod
    def to_py_pos(pos: pygame.Vector2) -> pygame.Vector2:
        return pygame.Vector2(pos.x + size[0] / 2, -pos.y + size[1] / 2)

    def __init__(self, costumes: list[str]):

        super().__init__()

        self.images = {c: pygame.image.load(c) for c in costumes}
        self.image = list(self.images.values())[0]

        self.pos = pygame.Vector2(0, 0)
        self.scale = 100
        self.rect = self.image.get_rect(center=PygameSpriteWrapper.to_py_pos(self.pos))

    def update(self, *args: Any, **kwargs: Any) -> None:

        self.rect.size = pygame.Vector2(self.image.get_size()) * self.scale / 100
        self.rect.center = PygameSpriteWrapper.to_py_pos(self.pos)