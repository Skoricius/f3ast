from trimesh.grouping import group_rows
from trimesh.graph import connected_component_labels
import numpy as np


def split_intersection(intersection):
    """Splits the intersection into connected components.

    Args:
        intersection ((n,2,2)): array of intersection lines

    Returns:
        (m,) list of (k,2,2) intersections: intersections grouped into components
    """
    # group the same points in the intersections
    grouped_rows = group_rows(intersection.reshape(-1, 2))
    # assign each point an index. This could be done faster
    grouped_indices = np.array(
        [[l, i] for i, ls in enumerate(grouped_rows) for l in ls])
    # get the indices sorted so that i-th element of node_indices corresponds to the i-th point
    arg = np.argsort(grouped_indices[:, 0])
    node_indices = grouped_indices[arg, 1]
    # label the connected components
    conn_labels = connected_component_labels(node_indices.reshape(-1, 2))

    unique_lbls = np.unique(conn_labels)
    split_intersection = []
    for lbl in unique_lbls:
        split_intersection.append(intersection[conn_labels == lbl, :, :])
    return split_intersection
