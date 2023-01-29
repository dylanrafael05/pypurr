from pypurr import *


class Cat(Sprite):

    costumes = ['cat.png', 'cat2.png']

    @when_start
    def run(self):

        self.goto(0, 0)
        self.size = 50

        while True:
            if key_down('space'):
                self.next_costume()

run()
