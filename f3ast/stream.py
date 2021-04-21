import numpy as np
from .utils import load_settings
import io
from datetime import timedelta
import os
from .plotting import points2d

# conversion factor from ms to 0.1us
CONVERSION_FACTOR = 10000


def intertwine_dwells(dwells_list):
    """Takes the list of matrices of dwells and intertwines them.

    Args:
        dwells_list (list of (n,3 arrays)): Dwells to intertwine.

    Returns:
        (n,3) array: Array of intertwined dwells.
    """
    n_list = len(dwells_list)
    size_list = [dwls.shape[0] for dwls in dwells_list]
    max_rows = np.max(size_list)
    total_length = np.sum(size_list)
    dwells = np.zeros((total_length, 3))

    cnt = 0
    for i in range(max_rows):
        for j in range(n_list):
            if i >= dwells_list[j].shape[0]:
                continue
            dwells[cnt, :] = dwells_list[j][i, :]
            cnt += 1
    return dwells


class Stream:
    """Class representing the stream file.

        Attributes:
            dwells ((n,3) array): Specifying dwells (t, x, y) in (ms, px, px)
            addressable_pixels (list of two int): Microscope addressable pixels.
            max_dwt (float): Maximum dwell time in ms.
    """

    def __init__(self, dwells, addressable_pixels=[65536, 56576], max_dwt=5):
        self.dwells = dwells

        self.addressable_pixels = addressable_pixels
        self.max_dwt = max_dwt

    @classmethod
    def from_file(cls, file_path, **kwargs):
        """Imports the stream from .str file

        Args:
            file_path (str): Path to the .str file

        Returns:
            Stream: Stream class with dwells from the file.
        """
        dwells = np.genfromtxt(file_path, delimiter=' ',
                               skip_header=3, usecols=range(3))
        # convert the dwells to ms
        dwells /= CONVERSION_FACTOR
        return cls(dwells, **kwargs)

    @property
    def limits(self):
        """Limits of the stream in x and y directions.

        Returns:
            (2, 2) array: Limits of the stream
        """
        mnmx = np.zeros((2, 2))
        mnmx[:, 0] = np.min(self.dwells[:, 1:], axis=0)
        mnmx[:, 1] = np.max(self.dwells[:, 1:], axis=0)
        return mnmx

    def is_valid(self):
        """Checks if the stream is valid (i.e. within the bounds).

        Returns:
            bool:
        """
        limits = self.limits
        if np.any(limits[:, 0] < 0) or np.any(limits[:, 1] > self.addressable_pixels) or np.any(self.dwells[:, 0] > self.max_dwt):
            return False
        return True

    def recentre(self, position=None):
        """Centres the stream.

        Args:
            position ((2,) array, optional): Position on which to centre. If None, centres to the centre of the screen. Defaults to None.
        """
        stream_centre = (self.limits[:, 1] + self.limits[:, 0]) / 2
        screen_centre = np.array(self.addressable_pixels) / 2
        if position is None:
            position = screen_centre
        else:
            position = np.array(position)
        translation_vector = position - stream_centre
        self.dwells[:, 1:] += translation_vector[np.newaxis, :]

    def write(self, file_path, centre=True):
        """Writes the stream to the file_path.

        Args:
            file_path (str): Path to the .str file to which to write.
            centre (bool, optional): Whether to centre the stream before exporting. Defaults to True.
        """
        # make sure the extension is .str
        file_path = os.path.splitext(file_path)[0] + '.str'
        if centre:
            self.recentre()
        # check that all the points are within limits
        if not self.is_valid():
            raise Exception(
                'Stream not valid! One of the dimensions is out of range.')

        dwells_to_write = self.dwells.copy()
        dwells_to_write[:, 0] *= CONVERSION_FACTOR
        dwells_to_write = np.round(dwells_to_write).astype(int)

        # gets the string ready to be written. Slightly roudabout way, but it's because of optional blanked screen lines
        header = 's16\n1\n' + str(self.dwells.shape[0])
        bio = io.BytesIO()
        np.savetxt(bio, dwells_to_write.astype(int),
                   delimiter=' ', fmt='%d', header=header, comments='')
        dwls_string = bio.getvalue().decode('latin1')
        dwls_string = dwls_string[:-1] + ' 0'
        with open(file_path, 'w') as f:
            f.write(dwls_string)

    def show_on_screen(self):
        """Plots the stream as it would look on the microscope screen.
        """
        ax, sc = points2d(self.dwells[:, 1:])
        ax.set_xlabel('x [px]')
        ax.set_ylabel('y [px]')
        ax.set_xlim([0, self.addressable_pixels[0]])
        ax.set_ylim([0, self.addressable_pixels[1]])

    def get_time(self):
        """Gets the total stream time.

        Returns:
            datetime.timedelta:
        """
        return timedelta(milliseconds=np.sum(self.dwells[:, 0]))

    def print_time(self):
        """Prints the total stream time."""
        print('Total time: ', str(self.get_time()))
