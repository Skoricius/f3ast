from scipy.optimize import lsq_linear
import numpy as np
from tqdm import tqdm
from .plotting import plot_dwells
from scipy.spatial import KDTree
from datetime import timedelta
import time


def get_distance_matrix(sl, threshold):
    """Gets the sparse matrix containting distances between points i and j in slice sl that are under a threshold"""
    tree = KDTree(sl)
    return tree.sparse_distance_matrix(tree, threshold, output_type='coo_matrix')


class DwellSolver:
    def __init__(self, model, structure):
        self.model = model
        self.structure = structure
        self.dwell_times_slices = None

    def solve_dwells(self, tol=1e-3):
        """Solves the dwells for dwell times and stores the result in self.dwell_times_slices

        Args:
            tol (float, optional): Tolerance of the lsq_linear solver. Defaults to 1e-3.
        """
        # ensure that the structure is sliced
        if self.structure.slices is None:
            self.structure.generate_slices()
        # get the thickness of layers
        dz_slices = self.structure.z_levels[1:] - self.structure.z_levels[:-1]
        # solve for each layer. TODO: this could be paralellized
        # TODO: no need to pass the whole structure to the model. Only pass the relevant slice data.
        self.dwell_times_slices = list()
        for i, (dz, sl) in tqdm(enumerate(zip(dz_slices, self.structure.slices[:-1]))):
            N = sl.shape[0]

            # get the proximity matrix
            t0 = time.time()
            distance_matrix = get_distance_matrix(
                sl, self.model.get_nb_threshold())
            proximity_matrix = distance_matrix.copy()
            proximity_matrix.data = self.model.get_proximity_matrix(
                distance_matrix.data, self.structure, i)
            # print('Proximity: ', time.time() - t0)

            t0 = time.time()
            # solve the optimization problem
            y = dz * np.ones(N)
            # get a tight upper bound. We can never have larger dwell times than if there was no proximity.
            upper_bound = dz / \
                self.model.get_proximity_matrix(0, self.structure, i)
            result = lsq_linear(proximity_matrix, y,
                                bounds=(0, upper_bound), tol=tol)
            # remove the very small dwells
            dwell_times = result.x
            self.dwell_times_slices.append(dwell_times)
            # print('Solving: ', time.time() - t0)

    def get_dwells_slices(self):
        """Returns the dwells for point as a per-slice list"""
        if self.dwell_times_slices is None:
            self.solve_dwells()
        return [np.hstack((dwt[:, np.newaxis], sl, z * np.ones((sl.shape[0], 1)))) for dwt, sl, z in zip(
                self.dwell_times_slices, self.structure.slices, self.structure.z_levels)]

    def get_dwells_matrix(self):
        """Returns the concatenated array of dwells for each point in a Nx4 array (time, x, y, z)"""
        return np.vstack(self.get_dwells_slices())

    def show_solution(self, cutoff=None):
        """Plots the solution colouring by dwells and displaying only the dwells above the cutoff."""
        dwells = self.get_dwells_matrix()
        if cutoff is not None:
            dwells = dwells[dwells[:, 0] > cutoff, :]
        ax, sc = plot_dwells(dwells)
        return ax, sc

    def print_total_time(self):
        """Prints the total stream time"""
        if self.dwell_times_slices is not None:
            t0 = np.sum([np.sum(dwls) for dwls in self.dwell_times_slices])
            print('Total stream time: ', timedelta(milliseconds=t0))
        else:
            print('Dwell times not calculated yet!')
