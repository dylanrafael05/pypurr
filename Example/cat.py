from pypurr import *


class Rand(Clone):

    costumes = ['cat.png']

    @when_clone_start
    def run(self):

        wait(2)
        delete(self)


class Center(Sprite):

    costumes = ['cat.png', 'cat2.png']

    @when_start
    def run(self):

        self.size = 25

        while (lambda x: x)(
            # COMMENT
            True
        ):
            self.pos = mouse_pos()
            if self.is_touching_sprite(Cat):
                self.costume_index = 0
            else:
                self.costume_index = 1


class Cat(Sprite):

    costumes = ['cat.png']

    @when_start
    def run(self):

        self.goto(0, 0)
        self.size = 25

        while True:
            wait(0.5)
            r = summon(Rand)
            r.goto(pick_random(-100, 100), pick_random(-100, 100))

run()
