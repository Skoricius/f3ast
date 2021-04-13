import numpy as np
import trimesh
from .plotting import plot_mesh_mpl
from .slicing import get_line_eqd_pts
from .resistance import split_intersection
import numpy as np


class Structure(trimesh.Trimesh):
    def __init__(self, *args, file_path=None, pitch=3, fill=False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pitch = pitch
        self.fill = fill

        self.file_path = file_path
        self.slices = None
        self.branches = None
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

        # split into connected components (branches)
        branch_intersections = [split_intersection(
            inter) for inter in intersection_lines]
        # split into equidistant points, keep track of connected components (branches)
        # can parallelize with joblib
        eqd_branches = [[(get_line_eqd_pts(
            line, self.pitch), i) for i, line in enumerate(brinter)] for brinter in branch_intersections]
        self.slices = [np.vstack([x[0] for x in eqbrch])
                       for eqbrch in eqd_branches]
        self.branches = [np.concatenate(
            [x[1] * np.ones(x[0].shape[0]) for x in eqbrch]) for eqbrch in eqd_branches]

        # self.slices = [get_line_eqd_pts(
        #     line, self.pitch) for line in intersection_lines]
