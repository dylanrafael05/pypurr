from pypurr import *


class Cat(Sprite):

    costumes = ['cat.png', 'cat2.png']

    @when_start
    def run(self):
        self.goto(0, 0)
        self.size = 50

        # while True:
        #     self.turn_left(5)

    @when_start
    def costume_handler(self):
        while True:
            self.next_costume()
            wait(2)


run()
