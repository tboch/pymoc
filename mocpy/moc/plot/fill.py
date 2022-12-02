import numpy as np
from astropy.coordinates import ICRS, SkyCoord
import cdshealpix

from astropy.wcs.utils import skycoord_to_pixel

from matplotlib.path import Path
from matplotlib.patches import PathPatch

from .utils import build_plotting_moc
from . import culling_backfacing_cells
from . import axis_viewport


def compute_healpix_vertices(depth, ipix, wcs):
    path_vertices = np.array([])
    codes = np.array([])

    depth = int(depth)

    ipix_lon, ipix_lat = cdshealpix.vertices(ipix, depth)

    ipix_lon = ipix_lon[:, [2, 3, 0, 1]]
    ipix_lat = ipix_lat[:, [2, 3, 0, 1]]
    ipix_boundaries = SkyCoord(ipix_lon, ipix_lat, frame=ICRS())
    # Projection on the given WCS
    xp, yp = skycoord_to_pixel(ipix_boundaries, wcs=wcs)

    c1 = np.vstack((xp[:, 0], yp[:, 0])).T
    c2 = np.vstack((xp[:, 1], yp[:, 1])).T
    c3 = np.vstack((xp[:, 2], yp[:, 2])).T
    c4 = np.vstack((xp[:, 3], yp[:, 3])).T

    cells = np.hstack((c1, c2, c3, c4, np.zeros((c1.shape[0], 2))))

    path_vertices = cells.reshape((5 * c1.shape[0], 2))
    single_code = np.array(
        [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    )

    codes = np.tile(single_code, c1.shape[0])

    return path_vertices, codes


def compute_the_patches(moc, wcs):
    depth_ipix_d = moc.serialize(format="json")
    depth_ipix_clean_d = culling_backfacing_cells.from_moc(
        depth_ipix_d=depth_ipix_d, wcs=wcs
    )

    patches = []
    for depth, ipix in depth_ipix_clean_d.items():
        patch = compute_healpix_vertices(depth=depth, ipix=ipix, wcs=wcs)
        patches.append(patch)

    return patches


def add_patches_to_mpl_axe(patches, ax, wcs, **kw_mpl_pathpatch):
    first_patch = patches[0]
    vertices_first_patch, codes_first_patch = first_patch
    path_vertices = np.array(vertices_first_patch)
    path_codes = np.array(codes_first_patch)

    for vertices, codes in patches[1:]:
        path_vertices = np.vstack((path_vertices, vertices))
        path_codes = np.hstack((path_codes, codes))

    path = Path(path_vertices, path_codes)
    patches_mpl = PathPatch(path, **kw_mpl_pathpatch)

    # Add the patches to the mpl axis
    ax.add_patch(patches_mpl)
    axis_viewport.set(ax, wcs)


def fill(moc, ax, wcs, **kw_mpl_pathpatch):
    # Simplify the MOC for plotting purposes:
    # 1. Degrade the MOC if the FOV is enough big so that we cannot see the smallest HEALPix cells.
    # 2. For small FOVs, plot the MOC & POLYGONAL_MOC_FROM_FOV.
    moc_to_plot = build_plotting_moc(moc=moc, wcs=wcs)

    # If the FOV contains no cells, then moc_to_plot (i.e. the intersection between the moc
    # and the MOC created from the FOV polygon) will be empty.
    # If it is the case, we exit the method without doing anything.
    if not moc_to_plot.empty():
        patches = compute_the_patches(moc=moc_to_plot, wcs=wcs)
        add_patches_to_mpl_axe(patches=patches, ax=ax, wcs=wcs, **kw_mpl_pathpatch)
