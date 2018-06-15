#---------------------------------------------------------------------
# Tools to regrid PIOMAS data to EASE grids
#
# 2018-03-14 A.P.Barrett <apbarret@nsidc.org>
#---------------------------------------------------------------------

import numpy as np
import os
import ESMF

from constants import srcGridFile, dstGridFile, weightsFile, regridMethods
from generateSCRIP import gridFromFile

#import geopy.distance

gdir = '/oldhome/apbarret/projects/ancillary/maps'

meta = {
        'Na12': {'xdim': 722,
                 'ydim': 722,
                 'latfile': os.path.join(gdir,'ycenter.Na12.722x722x1.float'),
                 'lonfile': os.path.join(gdir,'xcenter.Na12.722x722x1.float')},
        'Nh':   {'xdim': 1441,
                 'ydim': 1441,
                 'latfile': os.path.join(gdir,'ycenter.Nh.1441x1441x1.float'),
                 'lonfile': os.path.join(gdir,'xcenter.Nh.1441x1441x1.float')},
        'AWI_25km': {'xdim': 129,
                      'ydim': 104,
                      'latfile': os.path.join(gdir,'ycenter.AWI_25km.104x129x1.float'),
                      'lonfile': os.path.join(gdir,'xcenter.AWI_25km.104x129x1.float')},
        'Nh50km': {'xdim': 360,
                   'ydim': 360,
                   'latfile': os.path.join(gdir,'ycenter.nh50km_nest.360x360x1.float'),
                   'lonfile': os.path.join(gdir,'xcenter.nh50km_nest.360x360x1.float')},
       }

def get_ease_coords(gridname):
    """
    Gets lon, lat coordinates for an EASE grid

    Argument
    --------
    gridname - name of EASE grid, e.g. Na12
    
    Returns
    -------
    Tuple containing lon, lat
    """

    latfile = meta[gridname]['latfile']
    lonfile = meta[gridname]['lonfile']
    xdim = meta[gridname]['xdim']
    ydim = meta[gridname]['ydim'] 

    lat = np.fromfile(latfile, dtype='f4').reshape(xdim,ydim)
    lon = np.fromfile(lonfile, dtype='f4').reshape(xdim,ydim)
 
    return (lon, lat)

def griddef(gridname):
    """
    Returns a tuple of grid parameters for an EASE grid

    gridname - standard name of grid
    """
    gdef = {
            'Nh': {'c': 12.5, 'nx': 1441, 'ny': 1441, 'r0': 720, 's0': 720}
            }

    try:
        result = gdef[gridname]
        return result
    except:
        print ('griddef: unknown grid name')
#        return -1

def ll2northEase(ingrid, gridname, radius=6371.228):
    """
    Calculates EASE grid column and row coordinates for a given grid definition

    Arguments
    ---------
    ingrid - (lon,lat) tuple for input grid
    gridname - standard ease grid name

    Returns
    -------
    EASE grid row column coordinates
    """

    prm = griddef(gridname)

    rlon = np.radians(ingrid[0])
    rlat = np.radians(ingrid[1])
    
    r = 2*radius/prm['c']*np.sin(rlon)*np.sin((np.pi/4.)-(rlat/2.)) + prm['r0']
    s = 2*radius/prm['c']*np.cos(rlon)*np.sin((np.pi/4.)-(rlat/2.)) + prm['s0']

    return (r, s)

def ESMF_makeEASEGrid(grid_name):

    coords = get_ease_coords(grid_name)

    grid_shape = coords[0].T.shape

    grid = ESMF.Grid(np.array(grid_shape), staggerloc=ESMF.StaggerLoc.CENTER, coord_sys=ESMF.CoordSys.SPH_DEG)
    
    smask = grid.add_item(ESMF.GridItem.MASK, staggerloc=ESMF.StaggerLoc.CENTER)
    smask[...] = np.where(coords[0].T < -998., 0, 1) # Use coordinates to mask out cells off map

    XCoords = grid.get_coords(0)
    XCoords[...] = coords[0].T
    YCoords = grid.get_coords(1)
    YCoords[...] = coords[1].T

    return grid

def ESMF_makeLLGrid(grid_name):

    if grid_name == 'JRA55':
        grid = gridFromFile(srcGridFile[grid_name])
    else:
        grid = ESMF.Grid(filename=srcGridFile[grid_name], filetype=ESMF.FileFormat.SCRIP)

    return grid

def ESMF_GenRegridWeights( srcGridName, dstGridName,
                           src_mask_values=None, dst_mask_values=None,
                           method='bilinear'):
    """
    Generates an ESMF regrid object containing regrid weights

    Arguments
    ---------
    srcGridName - Name of source grid.  Currently CFSR2
    dstGridName - Name of EASE grid
    src_mask_values - ndarray containing values to mask out in srcMask
    dst_mask_values - ndarray containing values to mask out in dstMask
    method - Interpolation method ('bilinear', 'nearest', 'conserve', 'patch'
             See <http://www.earthsystemmodeling.org/esmf_releases/public/ESMF_7_1_0r/esmpy_doc/html/RegridMethod.html#ESMF.api.constants.RegridMethod>

    N.B. masking does not appear to work currently

    Returns
    -------
    An ESMF regrid object
    """

    srcGrid = ESMF_makeLLGrid(srcGridName)
    srcField = ESMF.Field(srcGrid, name='Source Grid')

    dstGrid = ESMF_makeEASEGrid(dstGridName)
    dstField = ESMF.Field(dstGrid, name='Destination Grid')
    
    regrid = ESMF.Regrid(srcField, dstField,
                         regrid_method=regridMethods[method],
                         unmapped_action=ESMF.UnmappedAction.IGNORE,
                         src_mask_values=src_mask_values,
                         dst_mask_values=dst_mask_values )

    return regrid, srcField, dstField

def ESMF_GenRegridWeights_fromCoords(srcCoord, dstCoord, srcMask=None, dstMask=None,
                                     src_mask_values=None, dst_mask_values=None,
                                     method='bilinear'):
    """
    Generates an ESMF regrid object containing regrid weights

    Arguments
    ---------
    srcGrid - tuple containing source grid lons and lats
    dstGrid - tuple containing destination grid lons and lats
    srcMask - ndarray containing a mask for the source grid
    dstMask - ndarray containing a mask for the source grid
    src_mask_values - ndarray containing values to mask out in srcMask
    dst_mask_values - ndarray containing values to mask out in dstMask
    method - Interpolation method ('bilinear', 'nearest', 'conserve', 'patch'
             See <http://www.earthsystemmodeling.org/esmf_releases/public/ESMF_7_1_0r/esmpy_doc/html/RegridMethod.html#ESMF.api.constants.RegridMethod>

    N.B. masking does not appear to work currently

    Returns
    -------
    An ESMF regrid object
    """

    methods = {'bilinear': ESMF.RegridMethod.BILINEAR,
              'nearest_stod': ESMF.RegridMethod.NEAREST_STOD,
              'nearest_dtos': ESMF.RegridMethod.NEAREST_DTOS,
              'patch': ESMF.RegridMethod.PATCH,
              'conserve': ESMF.RegridMethod.CONSERVE}
              
    # Define grids
    # - grids are transposed to make ESMF efficient.  ESMF is Fortran based, so transposing grids
    #   makes them Fortran contiguous
    srcGrid_shape = srcCoord[0].T.shape
    dstGrid_shape = dstCoord[0].T.shape
    
    sourcegrid = ESMF.Grid(np.array(srcGrid_shape), staggerloc=ESMF.StaggerLoc.CENTER, coord_sys=ESMF.CoordSys.SPH_DEG)
    destgrid = ESMF.Grid(np.array(dstGrid_shape), staggerloc=ESMF.StaggerLoc.CENTER, coord_sys=ESMF.CoordSys.SPH_DEG)

    # Add mask to destination grid
    if isinstance(srcMask, np.ndarray):
        smask = sourcegrid.add_item(ESMF.GridItem.MASK, staggerloc=ESMF.StaggerLoc.CENTER)
        smask[...] = srcMask.T

    if isinstance(dstMask, np.ndarray):
        print ('HERE')
        dmask = destgrid.add_item(ESMF.GridItem.MASK, staggerloc=ESMF.StaggerLoc.CENTER)
        dmask[...] = dstMask.T
        
    # Assign grid coordinates
    source_lon = sourcegrid.get_coords(0)
    source_lat = sourcegrid.get_coords(1)
    source_lon[...] = srcCoord[0].T
    source_lat[...] = srcCoord[1].T

    dest_lon = destgrid.get_coords(0)
    dest_lat = destgrid.get_coords(1)
    dest_lon[...] = dstCoord[0].T
    dest_lat[...] = dstCoord[1].T

    # Define fields
    sourcefield = ESMF.Field(sourcegrid, name='PIOMAS Ice Thickness')
    destfield = ESMF.Field(destgrid, name='Regridded Ice Thickness')

    regrid = ESMF.Regrid(sourcefield, destfield, 
                         regrid_method=methods[method],
                         unmapped_action=ESMF.UnmappedAction.IGNORE,
                         src_mask_values=src_mask_values,
                         dst_mask_values=dst_mask_values )

    return regrid, sourcefield, destfield

def main():

    indices = make_regrid_index('Na12', SAVEFILE=True)

    return

if __name__ == "__main__":
    main()

