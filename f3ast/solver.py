from scipy.optimize import lsq_linear
import numpy as np
from .plotting import plot_dwells
from scipy.spatial import KDTree
from datetime import timedelta
import time
from joblib import Parallel, delayed


def get_distance_matrix(sl, threshold):
    """Gets the sparse matrix containting distances between points i and j in slice sl that are under a threshold.

    Args:
        sl ((n,2) array): Points in slice to which to get the distance matrix of.
        threshold (float): Maximal distance which to consider.

    Returns:
        coo_matrix: Sparse distance matrix.
    """
    tree = KDTree(sl)
    return tree.sparse_distance_matrix(tree, threshold, output_type='coo_matrix')


class DwellSolver:
    """Class which solves the proximity problem for dwell times.

        Attributes:
            model (Model): Model which to solve.
            dwell_times_slices (list of arrays): Solutionto the proximity problem.
    """

    def __init__(self, model):
        self.model = model
        self.dwell_times_slices = None

    def solve_dwells(self, n_jobs=5):
        """Solves the dwells for dwell times and stores the result in self.dwell_times_slices

        Args:
            tol (float, optional): Tolerance of the lsq_linear solver. Defaults to 1e-3.
        """
        print('Solving for dwells...')
        # get the thickness of layers
        dz_slices = self.model.struct.dz_slices
        n_layers = dz_slices.size
        # get the generator for the proximity matrix
        prox_matrix_generator = (self.model.get_proximity_matrix(lyr)
                                 for lyr in range(n_layers))
        dwell_times_slices = list()
        # solve for each layer. Do this in parallel to speed up.
        dwell_times_slices = Parallel(n_jobs=n_jobs)(delayed(self.solve_layer)(
            proximity_matrix, dz) for proximity_matrix, dz in zip(prox_matrix_generator, dz_slices))
        self.dwell_times_slices = dwell_times_slices
        print('Solved')

    @staticmethod
    def solve_layer(proximity_matrix, dz, tol=1e-3):
        """Solves a layer proximity problem given a proximity matrix and the layer height.

        Args:
            proximity_matrix (sparse matrix): Proximity matrix
            dz (float): Layer height
            tol (float, optional): Tolerance for the optimization. Defaults to 1e-3.

        Returns:
            dwell_times: Array of dwell times as a solution for the layer.
        """
        # get a tight upper bound for faster computation. We can never have larger dwell times than if there was no proximity (proximity matrix was diagonal)
        upper_bound = dz / proximity_matrix.diagonal()
        # solve the optimization problem
        y = dz * np.ones(proximity_matrix.shape[1])
        result = lsq_linear(proximity_matrix, y,
                            bounds=(0, upper_bound), tol=tol)
        return result.x

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
        """Plots the solution colouring by dwells and displaying only the dwells above the cutoff.

        Args:
            cutoff (float, optional): Minimum dwell time to include. Defaults to None.

        Returns:
            tuple: axes, sc
        """
        dwells = self.get_dwells_matrix()
        if cutoff is not None:
            dwells = dwells[dwells[:, 0] > cutoff, :]
        ax, sc = plot_dwells(dwells)
        return ax, sc

    def get_total_time(self):
        """Gets the total solution time. Returns None if not solved.

        Returns:
            datetime.timedelta:
        """
        if self.dwell_times_slices is not None:
            t = np.sum([np.sum(dwls) for dwls in self.dwell_times_slices])
            return timedelta(milliseconds=t)
        return None

    def print_total_time(self):
        """Prints the total stream time"""
        t = self.get_total_time()
        if t is not None:
            print('Total stream time: ', t)
        else:
            print('Dwell times not calculated yet!')
