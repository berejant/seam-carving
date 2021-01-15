#!/usr/bin/env python3
from typing import List
from PIL import Image
import sys

import numpy
import cv2

class SeamCarving:

    image: numpy.ndarray

    def __init__(self, image: numpy.ndarray):
        self.image = image
        self.height, self.width, self.channels = image.shape

    def energy(self, y: int, x: int) -> float:
        x = int(x)
        y = int(y)
        prev_x = self.width - 1 if x == 0 else x - 1
        next_x = x + 1
        if next_x + 1 > self.width:
            next_x = 0

        prev_y = self.height - 1 if y == 0 else y - 1
        next_y = y + 1
        if next_y + 1 > self.height:
            next_y = 0

        sum_of_square_diff_by_x = 0
        for channel in range(self.channels):
            sum_of_square_diff_by_x += (int(self.image[y, prev_x, channel]) - int(self.image[y, next_x, channel])) ** 2

        sum_of_square_diff_by_y = 0
        for channel in range(self.channels):
            sum_of_square_diff_by_y += (int(self.image[prev_y, x, channel]) - int(self.image[next_y, x, channel])) ** 2

        return (sum_of_square_diff_by_x + sum_of_square_diff_by_y) ** .5

    def build_energy_matrix(self) -> numpy.ndarray:
        return numpy.fromfunction(numpy.vectorize(self.energy), (self.height, self.width), dtype=numpy.float32)

    def find_seam(self):
        energy_matrix = self.build_energy_matrix()
        dynamic_energy_matrix = numpy.zeros((self.height, self.width), dtype=numpy.float32)
        dynamic_energy_matrix[0] = energy_matrix[0]
        # coords of x from prev row
        backtrace = numpy.zeros((self.height, self.width), dtype=numpy.int32)

        for y in range(self.height):
            for x in range(self.width):
                min_neighbour_x = max(0, x - 1)
                backtrace[y, x] = min_neighbour_x + dynamic_energy_matrix[y - 1, min_neighbour_x:x+2].argmin()
                dynamic_energy_matrix[y, x] = dynamic_energy_matrix[y - 1, backtrace[y, x]] + energy_matrix[y][x]
        # Boolean 2-metric array. True value show pixel for remove
        seams_mask = numpy.zeros((self.height, self.width), dtype=numpy.bool)

        # detect min at last line. Then backtrace to first line and build Seam matrix
        current_x = int(dynamic_energy_matrix[self.height - 1].argmin())

        for y in reversed(range(self.height)):
            seams_mask[y, current_x] = True
            current_x = backtrace[y, current_x]

        return seams_mask

    def mark_seam_as_red(self, seam: numpy.ndarray) -> None:
        for y in range(seam.shape[0]):
            for x in range(seam.shape[1]):
                if seam[y, x]:
                    self.image[y, x] = [0, 0, 255]

    def remove_seam(self, seam:numpy.ndarray) -> None:
        self.width -= 1
        self.image = self.image[~seam].reshape(self.height, self.width, self.channels)


if len(sys.argv) < 3:
    print('Please input crop size in pixel and input file name')
    exit(-1)

crop_size = int(sys.argv[1])
if crop_size < 1 :
    print('Bad crop size: ' + str(crop_size))
    exit(-1)

source = sys.argv[2]
target = sys.argv[3] if len(sys.argv) >= 4 else None

image = cv2.imread(source) if isinstance(source, str) else None
if image is None:
    print('Failed to read ' + source)
    exit(-1)

seamCarving = SeamCarving(image)

window_name = 'Carving'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

for i in range(crop_size):
    seam = seamCarving.find_seam()
    cv2.imshow(window_name, seamCarving.image)
    if i == 0:
        cv2.resizeWindow(winname=window_name, height=max(750, seamCarving.image.shape[0]),
                         width=max(1000, seamCarving.image.shape[1]))

    cv2.waitKey(1)
    seamCarving.mark_seam_as_red(seam)
    cv2.imshow(window_name, seamCarving.image)
    cv2.waitKey(1)
    seamCarving.remove_seam(seam)

if target:
    cv2.imwrite(target, seamCarving.image)
cv2.waitKey(0)

cv2.destroyAllWindows()
