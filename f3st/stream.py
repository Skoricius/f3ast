import numpy as np
from .utils import load_settings
import io
from datetime import timedelta
import os

# conversion factor from ms to 0.1us
CONVERSION_FACTOR = 10000


class Stream:
    def __init__(self, dwells, addressable_pixels=[65536, 56576], max_dwt=50000):
        self.dwells = dwells

        self.addressable_pixels = addressable_pixels
        self.max_dwt = max_dwt

    @classmethod
    def from_file(cls, file_path, **kwargs):
        dwells = np.genfromtxt(file_path, delimiter=' ',
                               skip_header=3, usecols=range(3))
        # convert the dwells to ms
        dwells /= CONVERSION_FACTOR
        return cls(dwells, **kwargs)

    @property
    def limits(self):
        mnmx = np.zeros((2, 2))
        mnmx[:, 0] = np.min(self.dwells[:, 1])
        mnmx[:, 1] = np.max(self.dwells[:, 1])
        return mnmx

    def is_valid(self):
        limits = self.limits
        if np.any(limits[:, 0] < 0) or np.any(limits[:, 1] > self.addressable_pixels) or np.any(self.dwells[:, 0] > self.max_dwt):
            return False
        return True

    def recentre(self):
        """Centres the stream"""
        stream_centre = self.limits[:, 1] - self.limits[:, 0]
        screen_centre = np.array(self.addressable_pixels) / 2
        translation_vector = screen_centre - stream_centre
        self.dwells[:, 1:] += translation_vector[np.newaxis, :]

    def write(self, file_path):
        """Writes the stream to file_path"""
        # make sure the extension is .str
        file_path = os.path.splitext(file_path)[0] + '.str'
        # check that all the points are within limits
        if not self.is_valid():
            Exception('Stream not valid! One of the dimensions is out of range.')

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

    def print_time(self):
        """Prints the total stream time"""
        print(str(timedelta(microseconds=0.1 * np.sum(self.dwells[:, 0]))))
