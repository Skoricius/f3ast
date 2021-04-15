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
    def __init__(self, model):
        self.model = model
        self.dwell_times_slices = None

    def solve_dwells(self, tol=1e-3):
        """Solves the dwells for dwell times and stores the result in self.dwell_times_slices

        Args:
            tol (float, optional): Tolerance of the lsq_linear solver. Defaults to 1e-3.
        """
        # get the thickness of layers
        dz_slices = self.model.struct.dz_slices
        n_layers = dz_slices.size
        # get the generator for the proximity matrix
        prox_matrix_generator = (self.model.get_proximity_matrix(lyr)
                                 for lyr in range(n_layers))
        dwell_times_slices = list()
        # solve for each layer. TODO: this could be paralellized to get it working faster
        for proximity_matrix, dz in tqdm(zip(prox_matrix_generator, dz_slices)):
            # get a tight upper bound for faster computation. We can never have larger dwell times than if there was no proximity (proximity matrix was diagonal)
            upper_bound = dz / proximity_matrix.diagonal()
            # solve the optimization problem
            y = dz * np.ones(proximity_matrix.shape[1])
            result = lsq_linear(proximity_matrix, y,
                                bounds=(0, upper_bound), tol=tol)
            dwell_times = result.x
            dwell_times_slices.append(dwell_times)
        self.dwell_times_slices = dwell_times_slices

    def get_dwells_slices(self):
        """Returns the dwells for point as a per-slice list"""
        if self.dwell_times_slices is None:
            self.solve_dwells()
        slices3d = self.model.struct.get_3dslices()
        return [np.hstack([dwt[:, np.newaxis], sl3d]) for dwt, sl3d in zip(
                self.dwell_times_slices, slices3d)]

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
