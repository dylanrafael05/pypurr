from scratch import *


class Cat(Sprite):

    costumes = 'cat.png',

    @when_receive('hello')
    def hello(self):
        print('Testing!')

    @when_open
    def run_cat(self):

        self.goto(0, 0)

        grav = 10

        while True:

            if grav <= -10:
                grav = 10
            else:
                grav -= 1

            self.change_y(grav)

            self.broadcast('hello')


run_scratch()
