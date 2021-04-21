from numba import njit, config, prange
import numpy.linalg as la
import numpy as np

# set the threading layer before any parallel target compilation
config.THREADING_LAYER = 'threadsafe'


@njit(parallel=True, fastmath=True)
def _numba_eqd_pts(start_nodes, conn_vecs, n_steps):
    pts = np.zeros((np.sum(n_steps), 2))
    end_indices = np.cumsum(n_steps)
    start_indices = np.zeros(end_indices.shape[0]).astype(np.uint32)
    start_indices[1:] = end_indices[:-1]
    for i in prange(n_steps.shape[0]):
        end_indx = end_indices[i]
        start_indx = start_indices[i]
        n = n_steps[i]
        pts[start_indx:end_indx, :] = start_nodes[i, :].reshape(
            1, -1) + conn_vecs[i, :].reshape(1, -1) * np.arange(n).reshape(-1, 1) / n
    return pts


def get_line_eqd_pts(lines, pitch):
    """Gets the line points that are on a grid with spacing pitch.

    Args:
        lines ((n,2,2) array): Array of lines (start_node - end_node)
        pitch (float): Distance on the grid.

    Returns:
        (n,2) array: Points out on the grid.
    """

    start_nodes = np.ascontiguousarray(lines[:, 0, :])
    end_nodes = np.ascontiguousarray(lines[:, 1, :])

    conn_vecs = end_nodes - start_nodes
    conn_norms = la.norm(conn_vecs, axis=1)
    n_steps = np.ceil(conn_norms / pitch).astype(np.int32)

    pts = _numba_eqd_pts(start_nodes, conn_vecs, n_steps)

    pts_unique = np.unique(np.round(pts / pitch) * pitch, axis=0)

    return pts_unique


# def get_lines_length(lines):
#     return np.sum(la.norm(lines[:, 1, :] - lines[:, 0, :], axis=1))

def get_path_length(pts):
    """Gets the length of path defined by moving through the sequence of points

        Args:
            pts ((n,m) array): A sequence of n m-dimensional points

        Returns:
            (n,2) array: Distance of the path moving between the points
    """
    return np.sum(la.norm(pts[1:, :] - pts[:-1, :], axis=1))


def split_eqd(branch_intersections_slices, pitch):
    """Split into equidistant points, keep track of connected components (branches)
    can parallelize with joblib.

    Args:
        branch_intersections_slices (list of lists of arrays): For each slice, for each branch, array of points in that branch.
        pitch (float): Required spacing between the points.

    Returns:
        tuple: slices, branches, branch_lengths
    """
    slices = []
    branches = []
    branch_lengths = []
    for branch_intersections in branch_intersections_slices:
        branches_pts = [get_line_eqd_pts(
            lines, pitch) for lines in branch_intersections]

        slices.append(np.vstack(branches_pts))
        branches.append(np.concatenate(
            [i * np.ones(brpts.shape[0]) for i, brpts in enumerate(branches_pts)]))
        # defining the branch length can be a bit tricky. Here I use the total distance along a path in branches_pts, but this might not be absolutely correct for all structures
        branch_lengths.append(
            [get_path_length(pts) for pts in branches_pts])
    return slices, branches, branch_lengths
