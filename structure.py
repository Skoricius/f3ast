import numpy as np
import trimesh
from plotting import plot_mesh_mpl
from slicing import get_line_eqd_pts
from utils import load_settings
import numpy as np


class Structure:
    def __init__(self, msh, file_path=None, settings_file=None) -> None:
        self.mesh = msh
        if settings_file is not None:
            self.load_settings(settings_file)
        else:
            try:
                self.load_settings()
            except (FileNotFoundError, KeyError):
                self.pitch = None
                self.fill = False
        self.slices = None
        self.z_levels = None

    @classmethod
    def from_file(cls, file_path, **kwargs):
        file_path = file_path
        msh = trimesh.load(file_path)
        # create the structure and add file path
        struct = cls(msh, file_path=file_path, **kwargs)
        return struct

    def get_bounds(self):
        return self.mesh.bounds

    def rezero(self):
        self.mesh.rezero()

    def plot_mpl(self):
        ax = plot_mesh_mpl(self.mesh)
        return ax

    def load_settings(self, settings_file="settings.hjson"):
        settings = load_settings(settings_file)['stl']
        self.pitch = settings['pitch']
        self.fill = settings['fill']

    def get_slices(self):
        mindz = self.pitch / 5
        maxdz = 2 * self.pitch
        slice_height = self.pitch / 2

        # get the heights of slices
        bounds = self.get_bounds()
        minz, maxz = bounds[0, 2], bounds[1, 2]
        z_levels = np.arange(minz, maxz, slice_height)

        # define the slicing plane
        plane_normal = np.array((0.0, 0.0, 1.0))
        plane_orig = np.zeros(3).astype(float)

        intersection_lines, to_3D, face_index = trimesh.intersections.mesh_multiplane(
            self.mesh, plane_orig, plane_normal, z_levels)

        # can parallelize with joblib
        self.slices = [get_line_eqd_pts(
            line, self.pitch) for line in intersection_lines]
        self.z_levels = z_levels
