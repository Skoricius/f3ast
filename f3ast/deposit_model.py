import numpy as np
from scipy.optimize import curve_fit
from scipy.spatial import KDTree

from .resistance import get_resistance
from .structure import Structure


class Model:
    """Template class for the model classes. Defines how we model the deposit."""

    def __init__(self, struct, get_parameters=True):
        self._struct = struct
        if get_parameters:
            self.get_layer_parameters()

    @property
    def struct(self):
        """Structure to which the model applies."""
        return self._struct

    def set_structure(self, struct: Structure, update_parameters: bool = True):
        """Sets the structure and updates any internal parameters (e.g. resistance)

        Args:
            struct (Structure): Structure to update.
            update_parameters (bool, optional): Whether or not to update parameters.. Defaults to True.
        """
        self._struct = struct
        if update_parameters:
            self.get_layer_parameters()

    def get_nb_threshold(self) -> float:
        """Gets the threshold distance for which the points in a layer are considered neighbours.

        Returns:
            distance (float):
        """
        return 0.0

    def get_distance_matrix(self, layer: int):
        """Gets the distance matrix for the layer given by the index.

        Args:
            layer (int,): Index of the layer

        Returns:
            coo_matrix: distance_matrix: Sparse matrix (SciPy coo_matrix) of distances within the points that are withing the nb_threshold as defined by the class
        """
        tree = KDTree(self.struct.slices[layer])
        threshold = self.get_nb_threshold()
        return tree.sparse_distance_matrix(tree, threshold, output_type="coo_matrix")

    def proximity_fun(self, distances, *args):
        """Defines the proximity function to get the proximity matrix from distances.

        Args:
            distances (float, matrix)

        Returns:
            type(distances): proximit value
        """
        return distances + 1

    def get_proximity_matrix(self, layer: int, *args):
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

    def __init__(self, struct: Structure, gr: float, sigma: float, **kwargs):
        super().__init__(struct, **kwargs)
        self.gr = gr
        self.sigma = sigma

    def get_nb_threshold(self):
        """How far are the points considered neighbours"""
        return 3 * self.sigma

    def proximity_fun(self, distances, *_args):
        return self.gr * np.exp(-(distances**2) / (2 * self.sigma**2))

    @staticmethod
    def calibration_fit_function(t, gr: float):
        """Function for fitting the calibration"""
        return t * gr

    @staticmethod
    def fit_calibration(dwell_times, lengths, gr0=0.1):
        """Fits the calibration and returns optimal parameters and the fit function."""
        fn = RRLModel.calibration_fit_function

        popt, pcov = curve_fit(
            fn,
            dwell_times,
            lengths,
            p0=[
                gr0,
            ],
            bounds=(0, np.inf),
        )
        return fn, popt, pcov


class DDModel(Model):
    """Desorption-dominated model taking into account the heating via the resistance model.

    Attributes:
        struct (Structure):
        gr (float): growth rate
        k (float): temperature scaling parameter
        sigma (float): deposit width
    """

    def __init__(self, struct, gr: float, k: float, sigma: float, single_pixel_width: float = 50.0, **kwargs):
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
        """Gets the resistance and stores it as an internal parameter."""
        self._resistance = get_resistance(
            self.struct, single_pixel_width=self.single_pixel_width
        )

    def proximity_fun(self, distances, resistance):
        return (
            self.gr
            * np.exp(-self.k * resistance)
            * np.exp(-(distances**2) / (2 * self.sigma**2))
        )

    def get_proximity_matrix(self, layer: int):
        """Returns the proximity matrix using the distance matrix for the given layer."""
        distance_matrix = self.get_distance_matrix(layer)
        # each row of distance matrix has the resistance of the corresponding point
        res = self.resistance[layer][distance_matrix.row]
        # get the proximity matrix
        proximity_matrix = distance_matrix.copy()
        proximity_matrix.data = self.proximity_fun(distance_matrix.data, res)
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
        """Fits the calibration and returns optimal parameters and the
        fit function.

        Args:
            dwell_times (array): Array of measured dwell times.
            lengths (array): Array of measured lengths.
            gr0 (float, optional): Initial guess for GR. Defaults to 0.1.
            k0 (float, optional): Initial guess for k. Defaults to 1.

        Returns:
            [type]: [description]
        """
        fn = DDModel.calibration_fit_function

        popt, pcov = curve_fit(
            fn, dwell_times, lengths, p0=[gr0, k0], bounds=(0, np.inf)
        )
        print("GR: ", popt[0])
        print("k: ", popt[1])
        return fn, popt, pcov


class HeightCorrectionModel(RRLModel):
    """Returns stream model with exponential correction over structure height.
    Might be useful for stl files with disconnected components, which leads to
    a breakdown of the DDModel.

    Takes initial growth rate/time from GR, and doubles dwell time over the
    length scale of doubling_length.
    Doubling_length needs to be determined experimentally, e.g., from pitch of
    periodic structures over heights.

    Attributes:
        struct: structure
        GR: growth rate in um/s
        sigma: in nm, deposit width
        doubling_length: in nm, length over which deposition time doubles
    """

    def __init__(self, struct: Structure, gr: float, sigma: float, doubling_length: float = 500.0, **kwargs):
        super().__init__(struct, gr, sigma, **kwargs)
        self.doubling_length = doubling_length

    def get_proximity_matrix(self, layer, *args):
        proximity_matrix = super().get_proximity_matrix(layer, *args)
        layer_height = self.struct.z_levels[layer]
        proximity_matrix /= np.power(2.0, layer_height / self.doubling_length)
        return proximity_matrix


class InheritModel(Model):
    """Abstract class that allows inheriting a model to build upon it"""

    def __init__(self, base_model: Model, **kwargs):
        super().__init__(base_model.struct, **kwargs)
        self.base_model = base_model

    def get_nb_threshold(self):
        """How far are the points considered neighbours"""
        return self.base_model.get_nb_threshold()

    def proximity_fun(self, distances, *args):
        return self.base_model.proximity_fun(distances, *args)


class PhiAngleCorrectionModel(InheritModel):
    """ """

    def __init__(self, base_model: Model, phi0: float, correction_factor: float, num_layers_smoothing: int = 10):
        super().__init__(base_model)
        # for smoothing, we need to take a difference a number of layers apart
        self.num_layers_smoothing = num_layers_smoothing
        self.phi0 = phi0
        self.correction_factor = correction_factor
        self.layer_angles = self.get_layer_angles()

    def get_layer_angles(self) -> np.ndarray:
        layer_centres = np.array(
            [layer_points.mean(axis=0)
             for layer_points in self.struct.get_3dslices()]
        )
        num_smoothing = self.num_layers_smoothing
        layer_vectors = layer_centres[num_smoothing:,
                                      :] - layer_centres[:-num_smoothing, :]
        angles = np.zeros(len(self.struct.z_levels), dtype=float)
        angles[num_smoothing:] = np.arctan2(
            layer_vectors[:, 1], layer_vectors[:, 0])
        return angles

    def angle_correction_function(self, angles: np.ndarray) -> np.ndarray:
        return 1 + self.correction_factor * np.cos(angles - self.phi0)

    def get_proximity_matrix(self, layer: int, *args):
        proximity_matrix = super().get_proximity_matrix(layer, *args)
        proximity_matrix *= self.angle_correction_function(
            self.layer_angles[layer])
        return proximity_matrix
