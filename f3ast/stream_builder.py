from numpy.core.numeric import full
from .stream import Stream
from .solver import DwellSolver
import numpy as np
import warnings


class StreamBuilder:
    """Builds the stream using the microscope settings.


        Attributes:
            dwells_slices (list of (n,3) arrays): Specifying per layer dwells (t, x, y)
            addressable_pixels (list of two int): Microscope addressable pixels.
            max_dwt (float): Maximum dwell time in ms.
            cutoff_time (float): Minimum dwell time in ms. This is just for cutting of insignificant dwells to reduce file size.
            screen_width (float): Screen width in nm.
            scanning_order (str): Layer scanning order. Can be "serpentine" or "serial".
    """

    def __init__(self, dwells_slices,
                 addressable_pixels=[65536, 56576],
                 max_dwt=5,
                 cutoff_time=0.01,
                 screen_width=6400,
                 scanning_order="serpentine"):
        self.dwells_slices = dwells_slices

        self.addressable_pixels = addressable_pixels
        self.max_dwt = max_dwt
        self.cutoff_time = cutoff_time
        self.screen_width = screen_width
        assert scanning_order in {
            "serial", "serpentine"}, "Unrecognized scanning order!"
        self.scanning_order = scanning_order

    @classmethod
    def from_model(cls, model, **kwargs):
        """Creates the class from the model. Internally creates the DwellSolver and solves for dwells.

        Args:
            model (Model): Class defining the growth model.

        Returns:
            tuple:
                stream_builder (StreamBuilder), dwell_solver (DwellSolver)
        """
        # get the dwells
        dwell_solver = DwellSolver(model)
        dwell_solver.solve_dwells()
        dwells_slices = dwell_solver.get_dwells_slices()
        # build the class
        stream_builder = cls(dwells_slices, **kwargs)
        return stream_builder, dwell_solver

    @ property
    def ppn(self):
        """Pixels per nanometer"""
        return self.addressable_pixels[0] / self.screen_width

    def get_stream(self, centre=False):
        """Builds the stream object from the calculated dwells

        Args:
            centre (bool, optional): Wether to centre the stream on the screen. Defaults to False.

        Returns:
            Stream:
        """
        dwells = self.get_stream_dwells()
        # if the dwells include the z direction, get rid of that
        if dwells.shape[1] > 3:
            dwells = dwells[:, :3]
        stream = Stream(
            dwells, addressable_pixels=self.addressable_pixels, max_dwt=self.max_dwt)
        if centre:
            stream.recentre()
            if not stream.is_valid():
                warnings.warn(
                    "Stream outside screen limits. Structure might be too large!")
        return stream

    def get_stream_dwells(self):
        """Gets the stream dwells by splitting and ordering them appropriately. Also converts x, y in pixels and gets rid of small dwells.

        Returns:
            (n,3) array: Array of dwells.
        """
        # remove the dwells that are below the cutoff time
        dwells_slices = [ds[ds[:, 0] > self.cutoff_time]
                         for ds in self.dwells_slices]
        # split the dwells
        split_dwells_slices = [self.split_dwells(
            ds, self.max_dwt) for ds in dwells_slices]
        del dwells_slices

        # connect the split slices in a list, reverse the order of every other one if the serpentine order is used
        if self.scanning_order == "serial":
            full_dwells_list = [
                dwls for sds in split_dwells_slices for dwls in sds]
        else:
            full_dwells_list = []
            i = 0
            for sds in split_dwells_slices:
                for dwls in sds:
                    if i % 2 == 1:
                        full_dwells_list.append(np.flipud(dwls))
                    else:
                        full_dwells_list.append(dwls)
        # concatenate the list
        stream_dwells = np.vstack(full_dwells_list)
        # convert nm to px
        stream_dwells[:, 1:] *= self.ppn
        return stream_dwells

    @staticmethod
    def split_dwells(dwells, max_dwt):
        """Takes a matrix of dwells and splits them so that none of them exceeds the max dwell time. Returns a list of N_reps items which are all the split dwells.

        Args:
            dwells ((n,3) array): Array of dwells
            max_dwt (float): Maximum allowed dwell time.

        Returns:
            list: List of equal (n,3) arrays that when summed correspond to the dwells.
        """
        n_splits = int(np.ceil(np.max(dwells[:, 0]) / max_dwt))
        dwells_reduced = dwells.copy()
        dwells_reduced[:, 0] = dwells_reduced[:, 0] / n_splits
        return [dwells_reduced for i in range(n_splits)]
