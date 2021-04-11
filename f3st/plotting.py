import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import numpy as np
import mayavi.mlab as mlab
import numpy.linalg as la


def plot_mesh_maya(mesh, wireframe=False):
    mlab.figure()
    if wireframe:
        s = trimesh3d(mesh.points0, mesh.faces, color=(1, 1, 1),
                      opacity=0.5, representation='wireframe')
    else:
        s = trimesh3d(mesh.points0, mesh.faces, color=(1, 1, 1))
    mlab.axes()
    return s


def plot_mesh_mpl(msh, ax=None):
    if ax is None:
        fig = plt.figure()
        ax = mplot3d.Axes3D(fig, auto_add_to_figure=False)
        fig.add_axes(ax)

    ax.add_collection3d(mplot3d.art3d.Poly3DCollection(msh.triangles))
    bounds = msh.bounds

    ax.set_xlim(bounds[0, 0], bounds[1, 0])
    ax.set_ylim(bounds[0, 1], bounds[1, 1])
    ax.set_zlim(bounds[0, 2], bounds[1, 2])
    set_axes_equal(ax)
    return ax


def points3d(verts, *args, ax=None, **kwargs):
    if ax is None:
        fig = plt.figure()
        ax = mplot3d.Axes3D(fig, auto_add_to_figure=False)
        fig.add_axes(ax)
    ax.scatter(verts[:, 0], verts[:, 1], verts[:, 2], *args, **kwargs)
    return ax


def points2d(verts, ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    ax.scatter(verts[:, 0], verts[:, 1])
    return ax


def points3d_maya(verts, point_size=3, **kwargs):
    if 'mode' not in kwargs:
        kwargs['mode'] = 'point'
    p = mlab.points3d(verts[:, 0], verts[:, 1], verts[:, 2], **kwargs)
    p.actor.property.point_size = point_size


def trimesh3d(verts, faces, **kwargs):
    return mlab.triangular_mesh(verts[:, 0], verts[:, 1], verts[:, 2], faces,
                                **kwargs)


def show_plane(orig, n, scale=1.0, **kwargs):
    """
    Show the plane with the given origin and normal. scale give its size
    """
    b1 = orthogonal_vector(np.array(n).astype(float))
    b1 /= la.norm(b1)
    b2 = np.cross(b1, n)
    b2 /= la.norm(b2)
    verts = [orig + scale * (-b1 - b2),
             orig + scale * (b1 - b2),
             orig + scale * (b1 + b2),
             orig + scale * (-b1 + b2)]
    faces = [(0, 1, 2), (0, 2, 3)]
    return trimesh3d(np.array(verts), faces, **kwargs)


def orthogonal_vector(v):
    """Return an arbitrary vector that is orthogonal to v"""
    if v[1] != 0 or v[2] != 0:
        c = (1, 0, 0)
    else:
        c = (0, 1, 0)
    return np.cross(v, c)


def set_axes_equal(ax):
    '''Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc..  This is one possible solution to Matplotlib's
    ax.set_aspect('equal') and ax.axis('equal') not working for 3D.

    Input
      ax: a matplotlib axis, e.g., as output from plt.gca().
    '''

    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    # The plot bounding box is a sphere in the sense of the infinity
    # norm, hence I call half the max range the plot radius.
    plot_radius = 0.5 * max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])
