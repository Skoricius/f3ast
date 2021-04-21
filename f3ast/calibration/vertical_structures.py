import numpy as np
import os
from ..stream_builder import StreamBuilder
from ..stream import Stream, intertwine_dwells


def get_spot_dwells(t, position, max_dwt=5):
    """Gets a single spot dwell

    Args:
        t (float): Time in seconds for the spot dwell.
        position ((2,) list, array): Position of the dwell.
        max_dwt (float, optional): Maximum allowed dwell time in ms. Defaults to 5.

    Returns:
        (n,3) array: Dwells
    """
    dwells_split = StreamBuilder.split_dwells(
        np.array([1000 * t, position[0], position[1]])[np.newaxis, :], max_dwt)
    return np.vstack(dwells_split)


def get_spot_calibration(grid=[5, 3], start_time=1, end_time=15, shuffle=True, addressable_pixels=[65536, 56576], max_dwt=5):
    """Gets the spot calibration stream

    Args:
        grid (list, optional): Grid size for distributing the structures. Defaults to [5, 3].
        start_time (int, optional): Time in seconds of the smallest structure. Defaults to 1.
        end_time (int, optional): Time in seconds of the largest structure. Defaults to 15.
        shuffle (bool, optional): Whether to shuffle the structures randomly on a screen. Defaults to True.
        addressable_pixels (list, optional): Addressable pixels on microscope screen. Defaults to [65536, 56576].
        max_dwt (float, optional): Maximum allowed dwell time in ms. Defaults to 5.

    Returns:
        tuple: Stream, data
    """
    n_structs = grid[0] * grid[1]
    times = np.linspace(start_time, end_time, n_structs)
    # randomly shuffle the times to get rid of transient effects
    if shuffle:
        np.random.shuffle(times)
    # get the positions of the streams
    xstep, ystep = np.array(addressable_pixels) * 0.8 / np.array(grid)
    x = np.arange(grid[0]) * xstep
    y = np.arange(grid[1]) * ystep
    xygrid = np.meshgrid(x, y)
    positions = np.array(xygrid).reshape(2, n_structs)

    # construct the streams
    spot_dwells = [get_spot_dwells(t, positions[:, i], max_dwt=max_dwt)
                   for i, t in enumerate(times)]
    # intertwine the stream dwells
    dwells = intertwine_dwells(spot_dwells)
    # combine
    combined_stream = Stream(dwells, addressable_pixels=addressable_pixels,
                             max_dwt=max_dwt)
    combined_stream.recentre()

    # save the dwell times and the positions
    positions_loc = np.array(np.meshgrid(
        np.arange(grid[0]), np.arange(grid[1]))).reshape(2, n_structs).T
    data = np.hstack((times[:, np.newaxis], positions_loc))
    return combined_stream, data


def export_spot_calibration(file_path, **kwargs):
    """Convinience function to immediately save the calibration stream. Takes all the keywords parameter of the get_spot_calibration

    Args:
        file_path (str): File to which to save.
    """
    strm, data = get_spot_calibration(**kwargs)
    strm.print_time()
    strm.write(file_path)
    data_path = os.path.splitext(file_path)[0] + '_data.csv'
    np.savetxt(data_path, data, delimiter='\t',
               header="dwellTime\tpositionX\tpositionY", comments='', fmt="%3f\t%d\t%d")
