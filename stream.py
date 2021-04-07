import numpy as np
from utils import load_settings
import io
from datetime import timedelta


class Stream:
    def __init__(self, dwells=None, settings_file=None):
        self.dwells = dwells
        if settings_file is not None:
            self.settings = load_settings(settings_file)
        else:
            try:
                self.settings = load_settings()
            except FileNotFoundError:
                self.settings = None

    @classmethod
    def from_file(cls, file_path, **kwargs):
        dwells = np.genfromtxt(file_path, delimiter=' ',
                               skip_header=3, usecols=range(3))
        return cls(dwells, **kwargs)

    def write(self, file_path):
        # check that all the points within limits
        try:
            addressable_pixels = self.settings['microscope']['addressable_pixels']
            max_dwt = self.settings['microscope']['max_dwt']
            if np.any(self.dwells[:, 1] < 0):
                raise Exception('Negative numbers in dwells!')
            if (np.any(self.dwells[:, 1] > addressable_pixels[0]) or np.any(self.dwells[:, 2] > addressable_pixels[1])):
                raise Exception('Stream outside addressable points!')
            if np.any(self.dwells[:, 0] > max_dwt):
                raise Exception(
                    'Dwell times larger than the maximal dwell time!')
        except KeyError:
            pass
        dwells_to_write = np.round(self.dwells).astype(int)
        header = 's16\n1\n' + str(self.dwells.shape[0])
        bio = io.BytesIO()
        np.savetxt(bio, dwells_to_write.astype(int),
                   delimiter=' ', fmt='%d', header=header, comments='')
        dwls_string = bio.getvalue().decode('latin1')
        dwls_string = dwls_string[:-1] + ' 0'
        with open(file_path, 'w') as f:
            f.write(dwls_string)

    def print_time(self):
        print(str(timedelta(microseconds=0.1 * np.sum(self.dwells[:, 0]))))
