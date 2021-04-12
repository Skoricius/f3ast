import hjson
import numpy as np
import pickle
import os
from glob import glob


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


def create_safe_savename(path):
    ext = os.path.splitext(path)[1]
    path_noext = os.path.splitext(path)[0]
    init_path = path_noext
    i = 0
    while len(glob(path_noext + '*')) > 0:
        i += 1
        path_noext = init_path + '_{:03}'.format(i)
    path = path_noext + ext
    return path
