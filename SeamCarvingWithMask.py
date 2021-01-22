import numpy as np
import numpy.core._multiarray_umath


class SeamCarvingWithMask:
    image: np.ndarray
    energy_matrix: np.ndarray
    dynamic_energy_matrix: np.ndarray

    # coords of x from prev row
    backtrace: numpy.core._multiarray_umath.ndarray

    mask: np.ndarray

    def __init__(self, image: np.ndarray, mask: np.ndarray):
        self.image = np.copy(image)
        self.height, self.width, self.channels = image.shape

        self.mask =  np.zeros((self.height, self.width), dtype=np.bool)
        for y in range(self.height):
            for x in range(self.width):
                self.mask[y, x] = max(mask[y, x]) > 128

        # noinspection PyTypeChecker
        self.energy_matrix = np.fromfunction(np.vectorize(self.energy), (self.height, self.width), dtype=np.float32)

        self.dynamic_energy_matrix = np.zeros((self.height, self.width), dtype=np.float32)
        self.dynamic_energy_matrix[0] = np.copy(self.energy_matrix[0])

        self.backtrace = np.zeros((self.height, self.width), dtype=np.int32)

        for y in range(1, self.height):
            for x in range(self.width):
                self.backtrace[y, x], self.dynamic_energy_matrix[y, x] = self.dynamic_energy(y, x)

    def energy(self, y: int, x: int) -> float:
        y, x = int(y), int(x)
        if self.mask[y, x]:
            return -10000.0

        prev_x = self.width - 1 if x == 0 else x - 1
        next_x = x + 1 if x + 1 < self.width else 0

        prev_y = self.height - 1 if y == 0 else y - 1
        next_y = y + 1 if y + 1 < self.height else 0

        sum_of_square_diff_by_x = 0
        for channel in range(self.channels):
            sum_of_square_diff_by_x += (int(self.image[y, prev_x, channel]) - int(self.image[y, next_x, channel])) ** 2

        sum_of_square_diff_by_y = 0
        for channel in range(self.channels):
            sum_of_square_diff_by_y += (int(self.image[prev_y, x, channel]) - int(self.image[next_y, x, channel])) ** 2

        return (sum_of_square_diff_by_x + sum_of_square_diff_by_y) ** .5

    def build_energy_matrix(self):
        for y in range(self.height):
            for x in range(self.width):
                if np.isnan(self.energy_matrix[y, x]):
                    self.energy_matrix[y, x] = self.energy(y, x)

    def dynamic_energy(self, y, x):
        backtrace_x = max(0, x - 1)
        for iterate_x in range(x, min(self.width, x + 2)):
            if self.dynamic_energy_matrix[y - 1, iterate_x] <= self.dynamic_energy_matrix[y - 1, backtrace_x]:
                backtrace_x = iterate_x

        return backtrace_x, self.dynamic_energy_matrix[y - 1, backtrace_x] + self.energy_matrix[y][x]

    def build_dynamic_energy_matrix(self):
        changed_in_current_row = set()
        for x in range(self.width):
            if np.isnan(self.dynamic_energy_matrix[0, x]):
                self.dynamic_energy_matrix[0, x] = self.energy_matrix[0, x]
                changed_in_current_row.add(x)
                changed_in_current_row.add(x - 1)
                changed_in_current_row.add(x + 1)
            elif len(changed_in_current_row):
                break

        if not changed_in_current_row:
            return

        for y in range(1, self.height):
            changed_in_previous_row, changed_in_current_row = changed_in_current_row, set()
            for x in range(self.width):
                if np.isnan(self.dynamic_energy_matrix[y, x]) or x in changed_in_previous_row:
                    self.backtrace[y, x], dynamic_energy = self.dynamic_energy(y, x)
                    if dynamic_energy != self.dynamic_energy_matrix[y, x]:
                        self.dynamic_energy_matrix[y, x] = dynamic_energy
                        changed_in_current_row.add(x)
                        changed_in_current_row.add(x - 1)
                        changed_in_current_row.add(x + 1)

    def find_seam(self):
        self.build_energy_matrix()
        self.build_dynamic_energy_matrix()

        # Boolean 2-metric array. True value show pixel for remove
        seams_mask = np.zeros((self.height, self.width), dtype=np.bool)

        # detect min at last line. Then backtrace to first line and build Seam matrix
        current_min_x = 0
        for x in range(1, self.width):
            if self.dynamic_energy_matrix[self.height - 1, x] <= self.dynamic_energy_matrix[self.height - 1, current_min_x]:
                current_min_x = x

        for y in range(self.height - 1, -1, -1):
            seams_mask[y, current_min_x] = True
            current_min_x = self.backtrace[y, current_min_x]

        return seams_mask

    def mark_seam_as_red(self, seam: np.ndarray) -> None:
        for y in range(seam.shape[0]):
            for x in range(seam.shape[1]):
                if seam[y, x]:
                    self.image[y, x] = [0, 0, 255]

    def remove_seam(self, seam: np.ndarray) -> None:
        self.width -= 1
        self.image = self.image[~seam].reshape(self.height, self.width, self.channels)

        self.mask = self.mask[~seam].reshape(self.height, self.width)
        self.energy_matrix = self.energy_matrix[~seam].reshape(self.height, self.width)
        self.dynamic_energy_matrix = self.dynamic_energy_matrix[~seam].reshape(self.height, self.width)
        self.dynamic_energy_matrix[0] = np.copy(self.energy_matrix[0])
        self.backtrace = self.backtrace[~seam].reshape(self.height, self.width)
        for y in range(self.height):
            x = 0
            for _x in range(self.width):
                if seam[y, _x]:
                    x = _x
                    break

            next_y = min(self.height - 1, y + 1)
            self.energy_matrix[y, x] = self.energy_matrix[y - 1, x] = self.energy_matrix[next_y, x] = \
            self.energy_matrix[y, x - 1] = np.nan
            self.dynamic_energy_matrix[y, x] = self.dynamic_energy_matrix[y - 1, x] = self.dynamic_energy_matrix[
                next_y, x] = self.dynamic_energy_matrix[y, x - 1] = np.nan

            if y + 1 != self.height:
                for _x in range(x + 1, self.backtrace.shape[1]):
                    self.backtrace[next_y, _x] -= 1
