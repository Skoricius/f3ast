import numpy as np
import trimesh
from .plotting import plot_mesh_mpl
from .slicing import get_line_eqd_pts, get_lines_length, split_intersection
from scipy.spatial import KDTree
import numpy as np


class Structure(trimesh.Trimesh):
    def __init__(self, *args, file_path=None, pitch=3, fill=False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pitch = pitch
        self.fill = fill

        self.file_path = file_path
        self.slices = None
        self.branches = None
        self.branch_lengths = None
        self.branch_connections = None
        self.z_levels = None

    @classmethod
    def from_file(cls, file_path, **kwargs):
        file_path = file_path
        msh = trimesh.load_mesh(file_path, file_type='stl')
        # create the structure and add file path
        struct = cls(vertices=msh.vertices, faces=msh.faces,
                     file_path=file_path, **kwargs)
        return struct

    def rescale(self, scale):
        """Scales the mesh by the scale factor"""
        transf = np.eye(4)
        transf[3, 3] = 0
        transf *= scale
        self.apply_transform(transf)
        self.clear_slicing()

    def clear_slicing(self):
        self.slices = None
        self.z_levels = None

    def is_sliced(self):
        if self.slices is None:
            return False
        return True

    def plot_mpl(self):
        ax = plot_mesh_mpl(self)
        return ax

    def generate_slices(self):
        intersection_lines = self.get_intersection_lines()

        # split into connected components (branches)
        branch_intersections_slices = [split_intersection(
            inter) for inter in intersection_lines]

        # get equally separated points and branch indices
        self.slices, self.branches, self.branch_lengths = self.split_eqd(
            branch_intersections_slices)

        # get branch connectivity
        self.branch_connections = self.get_branch_connections()

    def get_intersection_lines(self):
        mindz = self.pitch / 5
        maxdz = 2 * self.pitch
        slice_height = self.pitch / 2

        # get the heights of slices
        minz, maxz = self.bounds[0, 2], self.bounds[1, 2]
        self.z_levels = np.arange(minz, maxz, slice_height)

        # define the slicing plane
        plane_normal = np.array((0.0, 0.0, 1.0))
        plane_orig = np.zeros(3).astype(float)

        intersection_lines, _, _ = trimesh.intersections.mesh_multiplane(
            self, plane_orig, plane_normal, self.z_levels)
        return intersection_lines

    def split_eqd(self, branch_intersections_slices):
        # split into equidistant points, keep track of connected components (branches)
        # can parallelize with joblib
        slices = []
        branches = []
        branch_lengths = []
        for branch_intersections in branch_intersections_slices:
            branches_pts = [get_line_eqd_pts(
                lines, self.pitch) for lines in branch_intersections]
            slices.append(np.vstack(branches_pts))
            branches.append(np.concatenate(
                [i * np.ones(brpts.shape[0]) for i, brpts in enumerate(branches_pts)]))
            branch_lengths.append(
                [get_lines_length(lines) for lines in branch_intersections])
        return slices, branches, branch_lengths

    def get_branch_connections(self):
        connection_distance = self.pitch + 0.01
        branch_connections = []
        for i, (pts, branch) in enumerate(zip(self.slices, self.branches)):
            unique_br = np.unique(branch)
            # separate the points into branches
            separated_pts = [pts[branch == lbl, :] for lbl in unique_br]
            if i == 0:
                branch_connections.append([])
                separated_pts_below = separated_pts
                continue
            this_slice_connections = []
            for br_pts in separated_pts:
                this_branch_connections = []
                tree = KDTree(br_pts)
                for k, branch_pts_below in enumerate(separated_pts_below):
                    tree_branch_below = KDTree(branch_pts_below)
                    dist_matrix = tree.sparse_distance_matrix(
                        tree_branch_below, max_distance=connection_distance)
                    if dist_matrix.count_nonzero() > 0:
                        this_branch_connections.append(k)
                this_slice_connections.append(this_branch_connections)
            branch_connections.append(this_slice_connections)
            separated_pts_below = separated_pts
        return branch_connections
