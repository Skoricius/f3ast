from numba import njit
import numpy.linalg as la
import numpy as np


@njit(parallel=True, fastmath=True)
def _numba_eqd_pts(start_nodes, conn_vecs, n_steps):

    pts = np.zeros((np.sum(n_steps), 2))
    start_indx = 0
    for i in range(n_steps.shape[0]):
        end_indx = start_indx + n_steps[i]
        n = n_steps[i]
        pts[start_indx:end_indx, :] = start_nodes[i, :].reshape(
            1, -1) + conn_vecs[i, :].reshape(1, -1) * np.arange(n).reshape(-1, 1) / n
        start_indx = end_indx

    return pts


def get_line_eqd_pts(lines, pitch):

    start_nodes = np.ascontiguousarray(lines[:, 0, :])
    end_nodes = np.ascontiguousarray(lines[:, 1, :])

    conn_vecs = end_nodes - start_nodes
    conn_norms = np.zeros(conn_vecs.shape[0])
    conn_norms = la.norm(conn_vecs, axis=1)
    conn_vecs_unit = conn_vecs / conn_norms.reshape(-1, 1)
    n_steps = np.ceil(conn_norms / pitch).astype(np.int32)

    pts = _numba_eqd_pts(start_nodes, conn_vecs, n_steps)

    pts_unique = np.unique(np.round(pts / pitch) * pitch, axis=0)

    return pts_unique
