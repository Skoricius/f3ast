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


def intertwine_dwells(dwells_list):
    """Takes the list of matrices of dwells and intertwines them."""
    n_list = len(dwells_list)
    size_list = [dwls.shape[0] for dwls in dwells_list]
    max_rows = np.max(size_list)
    total_length = np.sum(size_list)
    dwells = np.zeros((total_length, 3))

    cnt = 0
    for i in range(max_rows):
        for j in range(n_list):
            if i >= dwells_list[j].shape[0]:
                continue
            dwells[cnt, :] = dwells_list[j][i, :]
            cnt += 1
    return dwells
