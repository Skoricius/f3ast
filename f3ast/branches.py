# This is a set of functions for splitting slices into connected components and determining how these components connect with each other
from scipy.spatial import KDTree
from joblib.parallel import Parallel, delayed
import numpy as np
from trimesh.grouping import group_rows
from trimesh.graph import connected_component_labels


def split_intersection(intersection):
    """Splits the intersection into connected components (branches).

    Args:
        intersection ((n,2,2)): array of intersection lines

    Returns:
        (m,) list of (k,2,2) arrays: intersections grouped into components
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


def get_branch_connections(branch_intersections_slices, connection_distance):
    """Gets the connections between branches organized in slices

    Args:
        branch_intersections_slices (list of lists of arrays): For each slice, for each branch, array of points in that branch.
        connection_distance (float): Distance for which branches are considered connected.

    Returns:
        list of list of arrays:  For each slice, for each branch, which branches from layer below is it connected to.
    """
    branch_connections = []
    # with Parallel(n_jobs=5, backend="threading") as parallel:
    for i, separated_pts in enumerate(branch_intersections_slices):
        if i == 0:
            branch_connections.append([])
            separated_pts_below = separated_pts
            continue
        this_slice_connections = []
        for br_pts in separated_pts:
            # get how the branches in this layer connect to the branches from the previous layer. This is done by checking if the branches are neighbours (within a connection_distance away)
            this_branch_connections = []
            tree = KDTree(br_pts.reshape(-1, 2))
            branch_min_distances = []
            for k, branch_pts_below in enumerate(separated_pts_below):
                nb, dist = is_branch_nb(
                    tree, branch_pts_below, connection_distance)
                if nb:
                    branch_min_distances.append(dist)
                    this_branch_connections.append(k)
            this_branch_connections = np.array(this_branch_connections)
            n_conn = len(this_branch_connections)

            # the previous has an issue. The two branches can be close, but not fully merge until a few layers above.
            # This is a hack to fix it. It looks if the branches that seem to connect to each other exist (within a connection distance) in the current layer.
            # If something does not work properly, this is the likely culprit.
            # There must be a better way of doing this
            if n_conn > 1:
                # Ensure that the branches that were merged do not exist in the current layer
                # to know how many duplicates, need to know how many branches in this layer are within a conn distance away
                count = 0
                for br_pts2 in separated_pts:
                    if is_branch_nb(tree, br_pts2, connection_distance)[0]:
                        count += 1
                if count > 1 and count <= n_conn:
                    # drop the extra connections
                    n_drop = n_conn - count + 1
                    keep_indx = np.argsort(branch_min_distances)[:n_drop]
                    this_branch_connections = this_branch_connections[keep_indx]
            this_slice_connections.append(this_branch_connections)
        branch_connections.append(this_slice_connections)
        separated_pts_below = separated_pts
    return branch_connections


def is_branch_nb(tree, branch_pts, connection_distance):
    """Gets if the branch is a neighbour of a branch with KDTree tree.

    Args:
        tree (KDTree): KDTree of the current branch
        branch_pts ((n, 2) array): Other branch pts
        connection_distance (float): Distance for which the branches are considered neighours

    Returns:
        bool: True if branches are close
        float: Minimal distance between branches. np.inf if not neighbours.
    """
    tree1 = KDTree(branch_pts.reshape(-1, 2))
    distance_matrix = tree.sparse_distance_matrix(
        tree1, connection_distance, p=np.inf)
    if distance_matrix.count_nonzero() > 0:
        min_dist = np.min(list(distance_matrix.values()))
        return True, min_dist
    return False, np.inf


def get_branch_connections_in_slice(br_pts, separated_pts_below, connection_distance):
    """Auxiliary function to get the connections in a slice. This is for the purposes of parallelizing, but is not used atm.
    """

    this_branch_connections = []
    tree = KDTree(br_pts.reshape(-1, 2))
    branch_min_distances = []
    for k, branch_pts_below in enumerate(separated_pts_below):
        nb, dist = is_branch_nb(
            tree, branch_pts_below, connection_distance)
        if nb:
            branch_min_distances.append(dist)
            this_branch_connections.append(k)
    this_branch_connections = np.array(this_branch_connections)
    return np.array(this_branch_connections), branch_min_distances
