
from mpl_toolkits import mplot3d
import numpy as np
import trimesh
from .plotting import create_3d_axes, points3d, set_axes_equal
from .slicing import split_eqd
from .branches import split_intersection, get_branch_connections
import numpy as np
from trimesh.intersections import mesh_multiplane
import time
from scipy.spatial.transform import Rotation


class Structure(trimesh.Trimesh):
    """Class defining the mesh structure. Inherits from trimesh.base.Trimesh class.


        Attributes:
            file_path (str): Path to the STL file.
            pitch (float): Pitch for the slicing
            fill (bool): If true attempts to fill in the STL file (not implemented yet)
    """

    def __init__(self, *args, file_path=None, pitch=3, fill=False, **kwargs) -> None:
        if not 'face_colors' in kwargs:
            kwargs['face_colors'] = (17, 103, 177)
        super().__init__(*args, **kwargs)
        self.pitch = pitch
        self.fill = fill

        self.file_path = file_path
        self.clear_slicing()

    @classmethod
    def from_file(cls, file_path: str, **kwargs):
        """Gets the structure from stl file.

        Args:
            file_path (str): Path to the stl file.
            **kwargs: Further settings (pitch, fill) are passed to the __init__ method of the class.

        Returns:
            Structure
        """
        file_path = file_path
        msh = trimesh.load_mesh(file_path, file_type='stl')
        # create the structure and add file path
        struct = cls(vertices=msh.vertices, faces=msh.faces,
                     file_path=file_path, **kwargs)
        return struct

    @property
    def slices(self):
        """List of arrays of (n,2) points in each slice 
        """
        if self._slices is None:
            self.generate_slices()
        return self._slices

    @property
    def branches(self):
        """List of arrays signifying to which branch does each point in slice correspond to.
        """
        if self._branches is None:
            self.generate_slices()
        return self._branches

    @property
    def branch_lengths(self):
        """Branch lengths.
        """
        if self._branch_lengths is None:
            self.generate_slices()
        return self._branch_lengths

    @property
    def branch_connections(self):
        """Branch connection. List of lists. branch_connections[i][j] is the list of indices of which branches in the slice i-1 is the branch j in slice i connected.
        """
        if self._branch_connections is None:
            self.generate_slices(branch_connectivity=True)
        return self._branch_connections

    @property
    def z_levels(self):
        """Array of z values where the slices are.
        """
        if self._z_levels is None:
            self.generate_slices()
        return self._z_levels

    @property
    def dz_slices(self):
        """The thickness of layers
        """
        return self.z_levels[1:] - self.z_levels[:-1]

    @property
    def is_sliced(self) -> bool:
        """Weather or not the structure is sliced.

        Returns:
            bool
        """
        if self.slices is None:
            return False
        return True

    def centre(self):
        """Centres the structure to (0, 0)
        """
        self.rezero()
        transf = np.zeros((4, 4)).astype(float)
        transf[:3, :3] = np.eye(3)
        transf[0, -1] = -self.centroid[0]
        transf[1, -1] = -self.centroid[1]
        self.apply_transform(transf)

    def rescale(self, scale):
        """Scales the mesh by the scale factor"""
        transf = np.eye(4)
        transf[3, 3] = 0
        transf *= scale
        self.apply_transform(transf)
        self.clear_slicing()

    def rotate(self, rotation_axis, rotation_angle):
        """
        Rotates the mesh by a given angle around a specified axis.

        Args:
            rotation_axis: list or np.array
                Specifies rotation axis [x, y, z] as a 3-vector.
            rotation_angle: float
                Rotation angle in degrees.
        """
        r = Rotation.from_rotvec(np.deg2rad(
            rotation_angle) * np.array(rotation_axis))
        transf_matrix = np.eye(4)
        transf_matrix[:3, :3] = r.as_matrix()
        self.apply_transform(transf_matrix)
        self.clear_slicing()

    def clear_slicing(self):
        """Clears the slicing of the structure.
        """
        self._slices = None
        self._branches = None
        self._branch_lengths = None
        self._branch_connections = None
        self._z_levels = None

    def plot_mpl(self, ax=None):
        """Plots the mesh vertices in matplotlib window.

        Returns:
            axes: Matplotlib axes.
        """
        if ax is None:
            ax = create_3d_axes()

        ax.add_collection3d(mplot3d.art3d.Poly3DCollection(self.triangles))
        bounds = self.bounds

        ax.set_xlim(bounds[0, 0], bounds[1, 0])
        ax.set_ylim(bounds[0, 1], bounds[1, 1])
        ax.set_zlim(bounds[0, 2], bounds[1, 2])
        set_axes_equal(ax)
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
        """Plots the slices in matplotlib.

        Returns:
            axes: Matplotlib axes.
        """
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
        scene.set_camera(angles=np.deg2rad([45, 0, 0]))
        return scene.show()

    def generate_slices(self, branch_connectivity=True):
        """Gets the silces and all the corresponding information.

        Args:
            branch_connectivity (bool, optional): If false, does not calculate
            the connectivity of branches required for resistance calculations.
            This can be useful to save time if resistance is not going to be calculated.
            Defaults to True.
        """
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
        """Gets the intersections and z_levels.

        Returns:
            intersection_lines (list of arrays): A list of (n,2,2) arrays representing the intersection lines as start_node-end_node
            z_levels (array): Array of z levels corresponding to the intersections.
        """
        mindz = self.pitch / 5
        maxdz = 2 * self.pitch
        slice_height = self.pitch / 2

        # get the heights of slices
        minz, maxz = self.bounds[0, 2], self.bounds[1, 2]
        # move a bit to avoid artifacts
        minz += 1e-3
        maxz -= 1e-3
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
