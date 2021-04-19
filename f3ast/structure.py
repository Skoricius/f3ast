
import numpy as np
import trimesh
from .plotting import plot_mesh_mpl, points3d
from .slicing import split_eqd
from .branches import split_intersection, get_branch_connections
import numpy as np
from trimesh.intersections import mesh_multiplane
import time


class Structure(trimesh.Trimesh):
    def __init__(self, *args, file_path=None, pitch=3, fill=False, **kwargs) -> None:
        if not 'face_colors' in kwargs:
            kwargs['face_colors'] = (17, 103, 177)
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
            self.generate_slices(branch_connectivity=True)
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

    def show(self):
        # shows the model and adds the build plate
        scene = self.scene()
        # add the plane to the scene
        length = np.max(self.extents[:2])
        plane = trimesh.creation.box([length, length, 1])
        scene.add_geometry(plane)
        return scene.show()

    def generate_slices(self, branch_connectivity=True):
        print('Slicing...')
        intersection_lines, self._z_levels = self.get_intersection_lines()

        # split into connected components (branches)
        branch_intersections_slices = [split_intersection(
            inter) for inter in intersection_lines]

        # get branch connectivity. This is the slowest part and might not be necessary if not doing the resistance.
        # t0 = time.time()
        if branch_connectivity:
            connection_distance = self.pitch + 0.01
            self._branch_connections = get_branch_connections(
                branch_intersections_slices, connection_distance)
        # print(time.time() - t0)

        # get equally separated points and branch indices
        self._slices, self._branches, self._branch_lengths = split_eqd(
            branch_intersections_slices, self.pitch)

        print('Sliced')

    def get_intersection_lines(self):
        mindz = self.pitch / 5
        maxdz = 2 * self.pitch
        slice_height = self.pitch / 2

        # get the heights of slices
        minz, maxz = self.bounds[0, 2], self.bounds[1, 2]
        z_levels = np.arange(minz, maxz, slice_height)

        # define the slicing plane
        plane_normal = np.array((0.0, 0.0, 1.0))
        plane_orig = np.zeros(3).astype(float)

        intersection_lines, _, _ = mesh_multiplane(
            self, plane_orig, plane_normal, z_levels)
        # drop the empty intersections
        nonempty = np.array(
            len(inter) != 0 for inter in intersection_lines).astype(bool)
        z_levels = z_levels[nonempty].flatten()
        intersection_lines = [
            inter for inter in intersection_lines if len(inter) != 0]
        return intersection_lines, z_levels
