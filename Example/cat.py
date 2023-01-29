from pypurr import *


class Cat(Sprite):

    costumes = ['cat.png']

    @ when_start
    def run(self):

        self.goto(0, 0)

        while True:
            self.turn_left(5)


run()
