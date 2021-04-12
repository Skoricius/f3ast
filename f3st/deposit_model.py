import numpy as np
from scipy.optimize import curve_fit


class RRLModel:
    def __init__(self, gr, sigma):
        self.gr = gr
        self.sigma = sigma

    def get_nb_threshold(self):
        """How far are the points considered neighbours"""
        return 3 * self.sigma

    def get_proximity_matrix(self, distances, *args):
        """Returns the proximity matrix using the distance matrix"""
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


class DDModel:
    def __init__(self, gr, k, sigma):
        self.gr = gr
        self.k = k
        self.sigma = sigma

    def get_nb_threshold(self):
        """How far are the points considered neighbours"""
        return 3 * self.sigma

    def get_proximity_matrix(self, distances, structure, i):
        """Returns the proximity matrix using the distance matrix"""
        R = structure.resistance[i]
        return self.gr * np.exp(-self.k * R) * np.exp(-distances**2 / (2 * self.sigma**2))

    @staticmethod
    def calibration_fit_function(t, gr, k):
        """Function for fitting the calibration"""
        return 1 / k * np.log(k * gr * t + 1)

    @staticmethod
    def fit_calibration(dwell_times, lengths, gr0=0.1, k0=1):
        """Fits the calibration and returns optimal parameters and the fit function."""
        fn = DDModel.calibration_fit_function

        popt, pcov = curve_fit(fn, dwell_times, lengths,
                               p0=[gr0, k0], bounds=(0, np.inf))
        print('GR: ', popt[0])
        print('k: ', popt[1])
        return fn, popt, pcov
