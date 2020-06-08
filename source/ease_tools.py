#----------------------------------------------------------------------
# Tools for working with EASE grids that do not require ESMF
#
# Some of these tools are currently available in regrid.py so as not to
# break legacy code.
#----------------------------------------------------------------------

import numpy as np
import os

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
            'Nh': {'c': 12.5, 'nx': 1441, 'ny': 1441, 'r0': 720, 's0': 720},
            'Nh50km': {'c': 50., 'nx': 360, 'ny': 360, 'r0': 179.5, 's0': 179.5},
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

    return (s, r)

