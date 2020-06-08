#----------------------------------------------------------------------
# Tests regridding and field definition using an analytic field
#
# 2018-05-17 A.P.Barrett <apbarret@nsidc.org>
#----------------------------------------------------------------------
import ESMF
import numpy as np
import matplotlib.pyplot as plt
import os, glob
import re
import datetime as dt
from netCDF4 import Dataset

#from regrid import ESMF_makeEASEGrid, ESMF_makeLLGrid
from regrid import ESMF_GenRegridWeights

from constants import srcGridFile, dstGridFile, weightsFile, regridMethods

FILL_FLOAT = 9.9692099683868690e+36

def getField(fili, varName, field, mask_value=None):
    """
    Reads a field from a netCDF file and writes to srcField object
    """

    import xarray as xr

    ds = xr.open_dataset(fili)

    # Work around to set NaN to a value
    ds[varName] = ds[varName].where( ds[varName].notnull(), -999.)
    
    field.data[:] = ds[varName].data.T
    attrs = ds[varName].attrs

    ds.close()
    
    return field, attrs

def getFileList(diri, first_date=None, last_date=None):
    """
    Returns a list of files to regrid
    """

    def datestamp(f):
        m = re.compile('(\d{8}).nc')
        return dt.datetime.strptime(m.search(f).groups(0)[0], '%Y%m%d')
        
    fileList = glob.glob(os.path.join(diri,'????','??','*.????????.nc*'))
    fileList.sort()

    # Remove filepaths for regridded files - must match *.YYYYMMDD.nc4
    p = re.compile('\d{8}.nc')
    fileList = [f for f in fileList if p.search(f)]
    
    if first_date:
        first = dt.datetime.strptime(first_date, '%Y%m%d')
    else:
        first = datestamp(fileList[0])

    if last_date:
        last = dt.datetime.strptime(last_date, '%Y%m%d')
    else:
        last = datestamp(fileList[-1])
                         
    fileList = [f for f in fileList if (datestamp(f) >= first) & (datestamp(f) <= last)]
                         
    return fileList

def make_fileout(fili, dstGridName, method):
    """Returns output filepath"""
    if method == 'bilinear':
        return fili.replace('.nc', '.{:s}.nc'.format(dstGridName))
    else:
        return fili.replace('.nc', '.{:s}.{:s}.nc'.format(dstGridName, method))

def regrid_one_file(infile, srcGridName, dstGridName, srcVarName, 
                 src_mask_values=None, dst_mask_values=None,
                 method='bilinear', verbose=False):

    ESMF.Manager(debug=True)

    # Setup regrid object
    if verbose: print ('% Generating regrid weights')
    regrid, srcField, dstField = ESMF_GenRegridWeights(srcGridName, dstGridName,
                                                       method=method,)

    if verbose: print ('   Regridding {:s}'.format(infile))
    
    srcField, srcAttrs = getField(infile, srcVarName, srcField)

    dstField = regrid(srcField, dstField)

    # Mask dstField
    if srcGridName == 'ERA5-45N':
        # Special case, mask out cells below 45N
        dstField.data[...] = np.where(dstField.grid.get_coords(1) > 45., dstField.data, np.nan)
    else:
        dstField.data[...] = np.where(dstField.grid.mask[0] == 1, dstField.data, np.nan)

    filo = make_fileout(infile, dstGridName, method)
    if verbose: print ('   Writing regridded data to {:s}'.format(filo))
    writeNetCDF(dstField, srcAttrs, srcVarName, method, filo)

    return

def writeNetCDF(field, attrs, varName, method, filo):
    """
    Write data to NetCDF file
    """

    nx, ny = [360, 360]
    fill_value = FILL_FLOAT

    #field.data[...] = np.where(np.isfinite(field.data), field.data, fill_value)
        
    rootgrp = Dataset(filo, 'w')

    x = rootgrp.createDimension('x', nx)
    y = rootgrp.createDimension('y', ny)
    
    lat = rootgrp.createVariable( 'latitude', 'f4', ('x','y',) )
    lon = rootgrp.createVariable( 'longitude', 'f4', ('x','y',) )
    var = rootgrp.createVariable( varName, 'f4', ('x','y',), fill_value=fill_value )

    rootgrp.created = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    rootgrp.created_by = 'A.P.Barrett <apbarret@nsidc.org>'
    rootgrp.method = 'Regridded with ESMPy using '+method
    
    lat.long_name = 'latitude'
    lat.units = 'degrees_north'
    lon.long_name = 'longitude'
    lon.units = 'degrees_east'

    var.setncatts(attrs)
    
    lat[:,:] = field.grid.get_coords(1)[...].T
    lon[:,:] = field.grid.get_coords(0)[...].T
    var[:,:] = field.data.T
    
    rootgrp.close()
            
    return

if __name__ == "__main__":

    import argparse
    
    parser = argparse.ArgumentParser(description='Regrids all files in a directory and subdirectories',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('infile', type=str, 
                        help='Path to file to regrid.  Assumes data is 2D')
    parser.add_argument('srcGridName', type=str,
                        help='Name of source grid.  E.g. JRA55, CFSR2')
    parser.add_argument('dstGridName', type=str,
                        help='Name of destination grid.  Currently EASE grids')
    parser.add_argument('srcVarName', type=str,
                        help='Name of variable to read from source grid')
    parser.add_argument('--method', '-m', action='store', default='bilinear',
                        help='''Regrid method.  See:
<http://www.earthsystemmodeling.org/esmf_releases/public/last/esmpy_doc/html/RegridMethod.html#ESMF.api.constants.RegridMethod>

Options are:
bilinear - bilinear regridding
nearest_stod - Nearest neighbour - nearest source point to destination
nearest_dtos - Nearest neighbour - nearest destination point to source
patch - patch recovery interpolation - better approx to differentials
conserve - Conservative interpolation - preserves integral''')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
                        
    args = parser.parse_args()

    regrid_one_file(args.infile, args.srcGridName, args.dstGridName, args.srcVarName,
         method=args.method, verbose=args.verbose)
