import numpy as np
import trimesh
from .plotting import plot_mesh_mpl, points3d
from .slicing import get_line_eqd_pts, get_lines_length, split_intersection
from scipy.spatial import KDTree
import numpy as np


class Structure(trimesh.Trimesh):
    def __init__(self, *args, file_path=None, pitch=3, fill=False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pitch = pitch
        self.fill = fill

        self.file_path = file_path
        self.clear_slicing()

    @classmethod
    def from_file(cls, file_path, **kwargs):
        file_path = file_path
        msh = trimesh.load_mesh(file_path, file_type='stl')
        # create the structure and add file path
        struct = cls(vertices=msh.vertices, faces=msh.faces,
                     file_path=file_path, **kwargs)
        return struct

    @property
    def slices(self):
        if self._slices is None:
            self.generate_slices()
        return self._slices

    @property
    def branches(self):
        if self._branches is None:
            self.generate_slices()
        return self._branches

    @property
    def branch_lengths(self):
        if self._branch_lengths is None:
            self.generate_slices()
        return self._branch_lengths

    @property
    def branch_connections(self):
        if self._branch_connections is None:
            self.generate_slices()
        return self._branch_connections

    @property
    def z_levels(self):
        if self._z_levels is None:
            self.generate_slices()
        return self._z_levels

    @property
    def dz_slices(self):
        """The thickness of layers
        """
        return self.z_levels[1:] - self.z_levels[:-1]

    def rescale(self, scale):
        """Scales the mesh by the scale factor"""
        transf = np.eye(4)
        transf[3, 3] = 0
        transf *= scale
        self.apply_transform(transf)
        self.clear_slicing()

    def clear_slicing(self):
        self._slices = None
        self._branches = None
        self._branch_lengths = None
        self._branch_connections = None
        self._z_levels = None

    def is_sliced(self):
        if self.slices is None:
            return False
        return True

    def plot_mpl(self):
        ax = plot_mesh_mpl(self)
        return ax

    def get_3dslices(self):
        """Gets the slices with appended z values

        Returns:
            slices (list of (n,3) arrays)
        """
        return [np.hstack(
            [sl, z * np.ones((sl.shape[0], 1))]) for sl, z in zip(self.slices, self.z_levels)]

    def get_sliced_points(self):
        """Gets the sliced points in a matrix form.

        Returns:
            points ((n, 3) array)
        """
        points = np.vstack(self.get_3dslices())
        return points

    def plot_slices(self, *args, **kwargs):
        points = self.get_sliced_points()
        ax = points3d(points, *args, **kwargs)
        return ax

    def generate_slices(self):
        print('Slicing...')
        intersection_lines = self.get_intersection_lines()

        # split into connected components (branches)
        branch_intersections_slices = [split_intersection(
            inter) for inter in intersection_lines]

        # get equally separated points and branch indices
        self._slices, self._branches, self._branch_lengths = self.split_eqd(
            branch_intersections_slices)

        # get branch connectivity
        self._branch_connections = self.get_branch_connections()

    def get_intersection_lines(self):
        mindz = self.pitch / 5
        maxdz = 2 * self.pitch
        slice_height = self.pitch / 2

        # get the heights of slices
        minz, maxz = self.bounds[0, 2], self.bounds[1, 2]
        self._z_levels = np.arange(minz, maxz, slice_height)

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
