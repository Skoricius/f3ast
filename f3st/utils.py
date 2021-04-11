import hjson
import numpy as np
import pickle
import os


def load_settings(file_path='settings.hjson'):
    with open(file_path, 'r') as f:
        settings = hjson.load(f)
    return settings


def save_build(file_path, dwell_solver, stream_builder):
    # make sure the extension is .pickle
    file_path = os.path.splitext(file_path)[0] + '.pickle'
    with open(file_path, 'wb') as f:
        pickle.dump((dwell_solver, stream_builder), f)


def load_build(file_path):
    with open(file_path, 'rb') as f:
        loaded_data = pickle.load(f)
        dwell_solver, stream_builder = loaded_data[0], loaded_data[1]
    return dwell_solver, stream_builder


def intertwine_dwells(dwells1, dwells2):
    """Takes the two matrices of dwells and intertwines them"""
    dwells = np.zeros((dwells1.shape[0] + dwells2.shape[0], 3))
    dwells[::2, :] = dwells1
    dwells[1::2, :] = dwells2
    return dwells
