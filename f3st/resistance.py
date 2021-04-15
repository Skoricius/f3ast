import numpy as np
import numpy.linalg as la


def get_resistance(struct, single_pixel_width=50):

    slices = struct.slices
    branches = struct.branches
    branch_lengths = struct.branch_lengths
    branch_connections = struct.branch_connections
    dz_levels = struct.z_levels[1:] - struct.z_levels[:-1]
    resistance_slices = []
    for i, (pts, branch, brlens, conn) in enumerate(zip(slices, branches, branch_lengths, branch_connections)):
        resistance = np.zeros(pts.shape[0])
        unique_br = np.unique(branch)
        dz = dz_levels[i - 1]
        # separate the points into branches
        separated_pts = [pts[branch == lbl, :] for lbl in unique_br]
        # if on the substrate, set the resistance to 0 and continue
        if i == 0:
            separated_pts_below = separated_pts
            resistances_below = resistance
            resistance_slices.append(resistance)
            continue

        # find out how the branches connect: for each of the branches find the
        # ones from the layer below it connects to by finding if there are any
        # points which are within the pitch. Then add their resistance in
        # parallel to the other branches it connects to
        for j, (br_pts, br_conn) in enumerate(zip(separated_pts, conn)):
            # get the centre of the current layer
            center_curr = np.mean(br_pts, axis=0)
            # for each of the connected layers below, get the resistance increment
            r_inv = 0
            for c in br_conn:
                branch_pts_below = separated_pts_below[c]
                center_below = np.mean(branch_pts_below, axis=0)
                layer_sep = np.sqrt(
                    la.norm(center_curr - center_below)**2 + dz**2)
                connection_resistance = resistances_below[c] + \
                    layer_sep / (brlens[j] + single_pixel_width)
                r_inv += 1 / connection_resistance
            r = 1 / r_inv if r_inv != 0 else 0
            resistance[branch == j] = r
        resistance_slices.append(resistance)
        separated_pts_below = separated_pts
        resistances_below = resistance
    return resistance_slices
