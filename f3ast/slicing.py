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

    start_nodes = np.ascontiguousarray(lines[:, 0, :])
    end_nodes = np.ascontiguousarray(lines[:, 1, :])

    conn_vecs = end_nodes - start_nodes
    conn_norms = la.norm(conn_vecs, axis=1)
    n_steps = np.ceil(conn_norms / pitch).astype(np.int32)

    pts = _numba_eqd_pts(start_nodes, conn_vecs, n_steps)

    pts_unique = np.unique(np.round(pts / pitch) * pitch, axis=0)

    return pts_unique


def get_lines_length(lines):
    return np.sum(la.norm(lines[:, 1, :] - lines[:, 0, :], axis=1))


def split_eqd(branch_intersections_slices, pitch):
    # split into equidistant points, keep track of connected components (branches)
    # can parallelize with joblib
    slices = []
    branches = []
    branch_lengths = []
    for branch_intersections in branch_intersections_slices:
        branches_pts = [get_line_eqd_pts(
            lines, pitch) for lines in branch_intersections]

        slices.append(np.vstack(branches_pts))
        branches.append(np.concatenate(
            [i * np.ones(brpts.shape[0]) for i, brpts in enumerate(branches_pts)]))
        branch_lengths.append(
            [get_lines_length(lines) for lines in branch_intersections])
    return slices, branches, branch_lengths
