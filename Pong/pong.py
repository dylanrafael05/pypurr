from pypurr.all import *

class Test(Sprite2D, OnlyOne):

    costumes = ['cat.png']

    def start(self):
        self.pos = 0, 0
        self.scale = 10


class Other(Sprite2D, OnlyOne):

    costumes = ['cat.png', 'cat2.png']

    @proc.forever
    def start(self):

        self.scale = 5

        self.pos = mouse_pos()
        self.image_num = 1 if self.touching(Test) else 0

        if key_pressed('space'):
            for i in range(300):
                Particle()


class Particle(Particle2D):

    costume = 'cat.png'

    def __init__(self):
        super().__init__()

        self.vel = Vec2(pick_random(-10, 10), pick_random(-10, 10))

    @proc
    def start(self):
        self.scale = 0.5
        yield wait(pick_random(0.5, 2))
        self.delete()

    def update(self):
        self.pos += self.vel


run_project()