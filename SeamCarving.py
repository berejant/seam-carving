from PIL import Image


class SeamCarvingVertical:

    def __init__(self, image: Image):
        self.image = image
        self.pixels = image.load()
        self.width, self.height = image.size

    def energy(self, x: int, y: int) -> float:
        prev_x = self.width if x == 0 else x - 1
        next_x = x + 1
        if next_x > self.width:
            next_x = 0
        prevRGB = self.pixels[prev_x, y]
        print(prevRGB)
        nextRGB = self.pixels[next_x, y]
        print(nextRGB)

        return 0.0



seamCarving = SeamCarvingVertical(Image.open('dead_parrot.jpg'))

seamCarving.energy(10, 10)

