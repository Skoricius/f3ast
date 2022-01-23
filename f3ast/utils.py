import hjson
import pickle
import os
from glob import glob
from warnings import warn
from shutil import copy2
from pathlib import Path

# TODO: remove os and just use pathlib


def load_settings(file_path='settings.hjson'):
    """Loads the settings from the given path.

    Args:
        file_path (str, optional): Path to hjson file containing the settings. Defaults to 'settings.hjson'.

    Returns:
        dict: settings dictionary
    """
    settings_path = Path(file_path)
    if not settings_path.exists():
        warn("Settings file not found. Creating a default one.")
        default_settings_path = Path(
            __file__).parent.resolve() / "default_settings.hjson"
        copy2(default_settings_path, settings_path)

    with open(file_path, 'r') as f:
        settings = hjson.load(f)
    return settings


def save_build(file_path, dwell_solver, stream_builder):
    """Saves the dwell_solver and stream_builder to the save path.

    Args:
        file_path (str): Path to which to save
        dwell_solver (DwellSolver)
        stream_builder (StreamBuilder)
    """
    assert type(dwell_solver).__name__ == "DwellSolver"
    assert type(stream_builder).__name__ == "StreamBuilder"
    # make sure the extension is .pickle
    file_path = os.path.splitext(file_path)[0] + '.pickle'
    with open(file_path, 'wb') as f:
        pickle.dump((dwell_solver, stream_builder), f)


def load_build(file_path):
    """Loads the build from the given pickled file.

    Args:
        file_path (str): File path to the pickled file

    Returns:

        dwell_solver (DwellSolver), stream_builder (StreamBuilder)
    """
    with open(file_path, 'rb') as f:
        loaded_data = pickle.load(f)
        dwell_solver, stream_builder = loaded_data[0], loaded_data[1]
    return dwell_solver, stream_builder


def create_safe_savename(path):
    """Creates a path which does not already exist

    Args:
        path (str)

    Returns:
        str: Path same as the given path, but appends a string (e.g. _001) to the path if it already exists
    """
    ext = os.path.splitext(path)[1]
    path_noext = os.path.splitext(path)[0]
    init_path = path_noext
    i = 0
    while len(glob(path_noext + '*')) > 0:
        i += 1
        path_noext = init_path + '_{:03}'.format(i)
    path = path_noext + ext
    return path
