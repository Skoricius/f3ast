from f3ast.utils import load_settings
import numpy as np
from ..structure import Structure
from scipy.spatial.transform import Rotation as R
from ..stream_builder import StreamBuilder
from ..stream import Stream
import os

dirname = os.path.dirname(__file__)
CUBE_PATH = os.path.join(dirname, 'cube.stl')


def get_sigma_structures(model, sigma_list, width=75, length=800, angle=45):
    """Gets the structures for sigma calibration and returns a single stream file

    Args:
        model : Deposit model
        sigma_list (list): List of sigma values to try
        width (float, optional): Width of the structures. Defaults to 75.
        length (float, optional): Length of the structures. Defaults to 800.
        angle (float, optional): Angle to xy plane of the structures. Defaults to 45.
    """
    settings = load_settings()

    # get the straight ramp of minimal thickness
    struct = get_straight_ramp(length, width, 0.1, angle)
    model.set_structure(struct)

    # solve for dwell times
    sigma_strm_list = []
    for s in sigma_list:
        model.sigma = s
        stream_builder, _ = StreamBuilder.from_model(
            model, **settings['stream_builder'])
        sigma_strm_list.append(stream_builder.get_stream())

    # get the single pixel line
    struct_1px = get_straight_ramp(length, 0.1, 0.1, 45)
    model.set_structure(struct_1px)
    stream_builder, _ = StreamBuilder.from_model(
        model, **settings['stream_builder'])
    strm_1px = stream_builder.get_stream()

    # arange on a screen
    addressable_pixels = settings['stream_builder']['addressable_pixels']
    y_positions = np.linspace(
        0.1 * addressable_pixels[1], 0.9 * addressable_pixels[1], len(sigma_list))
    positions_list = [(addressable_pixels[0] / 2, y) for y in y_positions]
    for strm, pos in zip(sigma_strm_list, positions_list):
        strm.recentre(position=pos)

    pos1px = [0.75 * addressable_pixels[0], addressable_pixels[1] / 2]
    strm_1px.recentre(position=pos1px)

    # combine into one screen
    all_dwells = np.vstack([strm.dwells for strm in sigma_strm_list])
    all_dwells = np.vstack((all_dwells, strm_1px.dwells))

    strm_out = Stream(all_dwells, addressable_pixels=addressable_pixels,
                      max_dwt=settings['stream_builder']['max_dwt'])
    return strm_out


def get_straight_ramp(length, width, thickness, angle):
    """Gets a straight ramp stl file.

    Args:
        length (float): Length of the ramp.
        width (float): Width of the ramp.
        thickness (float): Thickness of the ramp.
        angle (float): Angle to substrate.

    Returns:
        Structure: The ramp with desired parameters.
    """
    struct = Structure.from_file(CUBE_PATH)
    transf_matrix = np.eye(4)
    transf_matrix[3, 3] = 0  # don't translate
    transf_matrix[0, 0] = length
    transf_matrix[1, 1] = width
    transf_matrix[2, 2] = thickness
    r = R.from_rotvec(np.deg2rad(angle) * np.array([0, 1, 0]))
    transf_matrix[:3, :3] = r.as_matrix().dot(transf_matrix[:3, :3])

    struct.apply_transform(transf_matrix)
    return struct
