#----------------------------------------------------------------------
# Generates a SCRIP format file from a netCDF file containing latitude
# and longitude coordinates.
#
# 2018-05-16 A.P.Barrett <apbarret@nsidc.org>
#----------------------------------------------------------------------

import numpy as np
from netCDF4 import Dataset
import ESMF
import datetime as dt

def get_lat(rootgrp):
    """
    Returns latitude coordinates from a netcdf file object
    """
    latAlias = ['lat','latitude','lat_0', 'lat2d']

    try:
        latName = (set(latAlias) & set(rootgrp.variables.keys())).pop()
    except KeyError:
        print ('Unable to find y-coordinate variable in file.  Expects '+', '.join(latAlias) )
        exit()
        
    return rootgrp.variables[latName][:]

def get_lon(rootgrp):
    """
    Returns longitude coordinates
    """
    lonAlias = ['lon','longitude','lon_0','lon2d']

    try:
        lonName = (set(lonAlias) & set(rootgrp.variables.keys())).pop()
    except KeyError:
        print ('Unable to find y-coordinate variable in file.  Expects '+', '.join(lonAlias) )
        exit()
        
    return rootgrp.variables[lonName][:]

def get_coords(fili):
    """
    Gets latitude and longitude coordinates from a netCDF file
    """

    rootgrp = Dataset(fili, "r")

    lat = get_lat(rootgrp)
    lon = get_lon(rootgrp)

    rootgrp.close()

    return (lon, lat)

def get_mask(fili):
    return None

def writeSCRIP(grid, outfile, name=None):
    """
    Writes a SCRIP format file
    """
    [x, y] = [0,1]

    grid_max = np.prod( grid.max_index )
    
    rootgrp = Dataset(outfile, "w")

    grid_size = rootgrp.createDimension('grid_size', grid_max)
    grid_rank = rootgrp.createDimension('grid_rank', grid.rank)

    grid_dims = rootgrp.createVariable('grid_dims', 'i', ('grid_rank',))
    grid_dims[:] = grid.max_index

    grid_center_lon = rootgrp.createVariable('grid_center_lon', 'f8', ('grid_size',))
    grid_center_lon.units = 'degrees'
    grid_center_lon[:] = grid.get_coords(x).reshape(-1)

    grid_center_lat = rootgrp.createVariable('grid_center_lat', 'f8', ('grid_size',))
    grid_center_lat.units = 'degrees'
    grid_center_lat[:] = grid.get_coords(y).reshape(-1)
    
    if any(grid.mask):
        grid_imask = rootgrp.createVariable('grid_imask', 'i', ('grid_size'))
        grid_imask.units = 'unitless'
        grid_imask[:] = grid.mask.reshape(-1)

    if name:
        rootgrp.title = name
    else:
        rootgrp.title = 'grid definition'
    rootgrp.created = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    rootgrp.close()
    
    return

def create_grid(Xcoords, Ycoords, mask=None):
    """
    Generates a grid object from x and y coords
    """
    [x, y] = [0,1]

    rank = len(Xcoords.shape)
    if rank > 1:
        gridDims = np.array(Xcoords.shape)
    else:
        gridDims = np.array([Xcoords.size, Ycoords.size])
        
    grid = ESMF.Grid(gridDims, staggerloc=ESMF.StaggerLoc.CENTER, coord_sys=ESMF.CoordSys.SPH_DEG)

    gridXCenter = grid.get_coords(x)
    x_par = Xcoords[ grid.lower_bounds[ESMF.StaggerLoc.CENTER][x]:grid.upper_bounds[ESMF.StaggerLoc.CENTER][x] ]
    gridXCenter[...] = x_par.reshape( (x_par.size, 1) )

    gridYCenter = grid.get_coords(y)
    y_par = Ycoords[ grid.lower_bounds[ESMF.StaggerLoc.CENTER][y]:grid.upper_bounds[ESMF.StaggerLoc.CENTER][y] ]
    gridYCenter[...] = y_par.reshape( (1, y_par.size) )

    if mask:
        grid_imask = grid.add_item(ESMF.GridItem.MASK)
        grid_imask[:] = mask
        
    return grid

def gridFromFile(fili, maskfile=None):
    """
    Generate a grid object from file

    Arguments
    ---------
    fili - a NetCDF file containing latitude and longitude values
    
    maskfile - a netcdf file containing mask 
    """

    XCoords, YCoords = get_coords(fili)

    xv, yv = np.meshgrid(XCoords, YCoords)

    grid_shape = xv.T.shape

    grid = ESMF.Grid(np.array(grid_shape), staggerloc=ESMF.StaggerLoc.CENTER, coord_sys=ESMF.CoordSys.SPH_DEG)

    lon = grid.get_coords(0)
    lat = grid.get_coords(1)
    lon[...] = xv.T
    lat[...] = yv.T

    return grid

    
    
def generateSCRIP(infile, outfile, maskfile=None, name=None, isease=False):
    """
    Generates SCRIP format grid defininition file

    See: http://www.earthsystemmodeling.org/esmf_releases/public/ESMF_7_1_0r/ESMF_refdoc/node3.html#SECTION03029000000000000000
    """

    Xcoords, Ycoords = get_coords(infile)

    # set mask values - EASE is a special case and uses coordinate grid to define mask
    mask = None
    if maskfile:
        mask = get_mask(maskfile)
    if isease:
        mask = np.where(Xcoords < -998., 0, 1)

    grid = create_grid(Xcoords, Ycoords, mask=mask)

    if mask:
        dmask = grid.add_item(ESMF.GridItem.MASK, staggerloc=ESMF.StaggerLoc.CENTER)
        dmask[...] = mask

    writeSCRIP(grid, outfile, name=name)
    
    return

if __name__ == "__main__":
    #infile = '/disks/arctic5_raid/abarrett/CFSR2/TOTPREC/2011/01/CFSR2.flxf06.gdas.TOTPREC.20110101.nc'
    #outfile = 'junkScrip.nc'
    import argparse

    parser = argparse.ArgumentParser(description='Generate a SCRIP format file describing a regular lat-lon grid')
    parser.add_argument('infile', type=str, help='NetCDF file containing latitude and longitude coordinate variables')
    parser.add_argument('outfile', type=str, help='Filepath for resulting SCRIP file')
    parser.add_argument('--grid_name', '-gn', default='Unknown grid',
                        help='Name of grid for title attribute of outfile')
    parser.add_argument('--maskfile', '-m', default=None, help='File containing mask')
    args = parser.parse_args()
    
    generateSCRIP(args.infile, args.outfile, name=args.grid_name, maskfile=args.maskfile)

    
