import numpy as np


class RRLModel:
    def __init__(self, gr, sigma):
        self.gr = gr
        self.sigma = sigma

    def get_nb_threshold(self):
        """How far are the points considered neighbours"""
        return 3 * self.sigma

    def get_proximity_matrix(self, distances):
        return self.gr * np.exp(-distances**2 / (2 * self.sigma**2))
