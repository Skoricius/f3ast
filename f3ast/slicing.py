from numba import njit, config, prange
import numpy.linalg as la
import numpy as np
from trimesh.grouping import group_rows
from trimesh.graph import connected_component_labels

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


def split_intersection(intersection):
    """Splits the intersection into connected components.

    Args:
        intersection ((n,2,2)): array of intersection lines

    Returns:
        (m,) list of (k,2,2) intersections: intersections grouped into components
    """
    # group the same points in the intersections
    grouped_rows = group_rows(intersection.reshape(-1, 2))
    # assign each point an index.
    grouped_indices = np.array(
        [[l, i] for i, ls in enumerate(grouped_rows) for l in ls])
    # get the indices sorted so that i-th element of node_indices corresponds to the i-th point
    try:
        arg = np.argsort(grouped_indices[:, 0])
    except IndexError:
        print(len(intersection))
        print(intersection)
        raise Exception()
    node_indices = grouped_indices[arg, 1]
    # label the connected components
    edges = node_indices.reshape(-1, 2)
    conn_labels = connected_component_labels(
        edges, node_count=len(grouped_rows))
    # conn labels correspond to the nodes. Label each edge by one of its nodes.
    edge_labels = conn_labels[edges[:, 0]]

    unique_lbls = np.unique(conn_labels)
    split_intersection = []
    for lbl in unique_lbls:
        split_intersection.append(intersection[edge_labels == lbl, :, :])
    return split_intersection
