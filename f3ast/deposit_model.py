import numpy as np
from scipy.optimize import curve_fit
from scipy.spatial import KDTree
from .resistance import get_resistance


class Model:
    """Template class for the model classes. Defines how we model the deposit.
    """

    def __init__(self, struct, get_parameters=True):
        self._struct = struct
        if get_parameters:
            self.get_layer_parameters()

    @property
    def struct(self):
        """Structure to which the model applies.
        """
        return self._struct

    def set_structure(self, struct, update_parameters=True):
        """Sets the structure and updates any internal parameters (e.g. resistance)

        Args:
            struct (Structure): Structure to update.
            update_parameters (bool, optional): Whether or not to update parameters.. Defaults to True.
        """
        self._struct = struct
        if update_parameters:
            self.get_layer_parameters()

    def get_nb_threshold(self):
        """Gets the threshold distance for which the points in a layer are considered neighbours.

        Returns:
            distance (float):
        """
        return 0

    def get_distance_matrix(self, layer):
        """Gets the distance matrix for the layer given by the index.

        Args:
            layer (int,): Index of the layer

        Returns:
            coo_matrix: distance_matrix: Sparse matrix (SciPy coo_matrix) of distances within the points that are withing the nb_threshold as defined by the class
        """
        tree = KDTree(self.struct.slices[layer])
        threshold = self.get_nb_threshold()
        return tree.sparse_distance_matrix(tree, threshold, output_type='coo_matrix')

    def proximity_fun(self, distances, *args):
        """Defines the proximity function to get the proximity matrix from distances.

        Args:
            distances (float, matrix)

        Returns:
            type(distances): proximit value
        """
        return distances + 1

    def get_proximity_matrix(self, layer, *args):
        """Gets the proximity matrix for the layer required by the solver.

        Args:
            layer (int): Index of the layer

        Returns:
            coo_matrix: proximity_matrix: Sparse matrix (SciPy coo_matrix) defining the parameters for the proximity calculation.
        """
        distance_matrix = self.get_distance_matrix(layer)
        # need to copy the matrix so that we can apply the proximity function to the data
        proximity_matrix = distance_matrix.copy()
        proximity_matrix.data = self.proximity_fun(distance_matrix.data, *args)
        return proximity_matrix

    def get_layer_parameters(self):
        """Gets any necessary layer parameters from the structure for the model to be able to calculate the proximity matrix. E.g. resistance for temperature, layer height for focus correction etc."""
        pass


class RRLModel(Model):
    """Reaction rate limited model. Basic model only taking into account growth rate and sigma parameters.

        Attributes:
            gr (float): growth rate
            sigma (float): deposit width
    """

    def __init__(self, struct, gr, sigma, **kwargs):
        super().__init__(struct, **kwargs)
        self.gr = gr
        self.sigma = sigma

    def get_nb_threshold(self):
        """How far are the points considered neighbours"""
        return 3 * self.sigma

    def proximity_fun(self, distances):
        return self.gr * np.exp(-distances**2 / (2 * self.sigma**2))

    @staticmethod
    def calibration_fit_function(t, gr):
        """Function for fitting the calibration"""
        return t * gr

    @staticmethod
    def fit_calibration(dwell_times, lengths, gr0=0.1):
        """Fits the calibration and returns optimal parameters and the fit function."""
        fn = RRLModel.calibration_fit_function

        popt, pcov = curve_fit(fn, dwell_times, lengths,
                               p0=[gr0, ], bounds=(0, np.inf))
        return fn, popt, pcov


class DDModel(Model):
    """Desorption-dominated model taking into account the heating via the resistance model.

        Attributes:
            struct (Structure):
            gr (float): growth rate
            k (float): temperature scaling parameter
            sigma (float): deposit width
    """

    def __init__(self, struct, gr, k, sigma, single_pixel_width=50, **kwargs):
        self.gr = gr
        self.k = k
        self.sigma = sigma

        self.single_pixel_width = single_pixel_width

        self._resistance = None
        super().__init__(struct, **kwargs)

    @property
    def resistance(self):
        """Resistance parameter."""
        if self._resistance is None:
            self.get_layer_parameters()
        return self._resistance

    def get_layer_parameters(self):
        """Gets the resistance and stores it as an internal parameter
        """
        self._resistance = get_resistance(
            self.struct, single_pixel_width=self.single_pixel_width)

    def proximity_fun(self, distances, resistance):
        return self.gr * np.exp(-self.k * resistance) * np.exp(-distances**2 / (2 * self.sigma**2))

    def get_proximity_matrix(self, layer):
        """Returns the proximity matrix using the distance matrix for the given layer."""
        distance_matrix = self.get_distance_matrix(layer)
        # each row of distance matrix has the resistance of the corresponding point
        res = self.resistance[layer][distance_matrix.row]
        # get the proximity matrix
        proximity_matrix = distance_matrix.copy()
        proximity_matrix.data = self.proximity_fun(
            distance_matrix.data, res)
        return proximity_matrix

    def get_nb_threshold(self):
        """How far are the points considered neighbours."""
        return 3 * self.sigma

    @staticmethod
    def calibration_fit_function(t, gr, k):
        """Function for fitting the calibration."""
        return 1 / k * np.log(k * gr * t + 1)

    @staticmethod
    def fit_calibration(dwell_times, lengths, gr0=0.1, k0=1):
        """Fits the calibration and returns optimal parameters and the fit function.

        Args:
            dwell_times (array): Array of measured dwell times.
            lengths (array): Array of measured lengths.
            gr0 (float, optional): Initial guess for GR. Defaults to 0.1.
            k0 (float, optional): Initial guess for k. Defaults to 1.

        Returns:
            [type]: [description]
        """
        fn = DDModel.calibration_fit_function

        popt, pcov = curve_fit(fn, dwell_times, lengths,
                               p0=[gr0, k0], bounds=(0, np.inf))
        print('GR: ', popt[0])
        print('k: ', popt[1])
        return fn, popt, pcov
