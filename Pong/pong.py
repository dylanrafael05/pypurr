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
        self.image_idx = 1 if self.touching(Test.instance) else 0

run_project()