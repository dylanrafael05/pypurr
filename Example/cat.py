from pypurr.all import *


class Manager(Image2D, Singleton):

    costumes = ['cat2.png']

    def update(self):

        self.scale = 10
        self.pos = mouse_pos()

        if key_pressed('space'):
            for i in range(int(pick_random(20, 30))):
                Particle()


class Particle(Image2D):

    costumes = ['cat2.png']

    def __init__(self):
        super().__init__()
        self.vel: mathpr.Vec2 = mathpr.Vec2(pick_random(-10, 10), pick_random(-10, 10))
        self.rotvel = pick_random(-2, 2)

    def start(self):
        self.pos = mouse_pos()
        self.scale = 1

    def update(self):
        self.vel += mathpr.Vec2(0, -1)

        self.pos += self.vel * 0.5
        self.rot += self.rotvel

        if self.y < -500:
            self.delete()




run_project()