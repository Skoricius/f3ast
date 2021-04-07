import numpy as np
from stl import mesh
from plotting import plot_mesh
import meshio


class Structure:
    def __init__(self, msh) -> None:
        self.mesh = msh

    @classmethod
    def from_file(cls, file_path):
        file_path = file_path
        # read with meshio which extracts the data in a better way.
        # Then convert to numpy mesh that has a lot more utilities.
        mshio = meshio.read(file_path, file_format='stl')
        faces = mshio.cells[0].data
        vertices = mshio.points
        # convert
        msh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        msh.vectors = vertices[faces]
        msh.points0 = vertices
        msh.faces = faces
        # create the structure and add file path
        struct = cls(msh)
        struct.file_path = file_path
        return struct

    def get_mins_maxs(self):
        minx = self.mesh.x.min()
        maxx = self.mesh.x.max()
        miny = self.mesh.y.min()
        maxy = self.mesh.y.max()
        minz = self.mesh.z.min()
        maxz = self.mesh.z.max()
        return minx, maxx, miny, maxy, minz, maxz

    @property
    def center(self):
        minx, maxx, miny, maxy, minz, maxz = self.get_mins_maxs()
        return np.array([np.mean([maxx, minx]), np.mean([maxy, miny]), np.mean([maxz, minz])])

    def plot(self):
        ax = plot_mesh(self.mesh)
        return ax

    def plot_mpl(self):
        ax = plot_mesh_mpl(self.mesh)
        return ax

    def translate(self, vector):
        self.mesh.translate(vector)
