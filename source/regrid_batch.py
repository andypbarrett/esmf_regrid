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

def getField(fili, varName, field):
    """
    Reads a field from a netCDF file and writes to srcField object
    """

    import xarray as xr

    ds = xr.open_dataset(fili)

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

def make_fileout(fili, dstGridName):
    """Returns output filepath"""
    return fili.replace('.nc', '.{:s}.nc'.format(dstGridName))

def regrid_batch(srcGridName, dstGridName, datadir, srcVarName, first_date=None, last_date=None,
                 src_mask_values=None, dst_mask_values=None,
                 method='bilinear', verbose=False):

    ESMF.Manager(debug=True)

    # Setup regrid object
    if verbose: print ('% Generating regrid weights')
    regrid, srcField, dstField = ESMF_GenRegridWeights(srcGridName, dstGridName, method=method)

    if verbose: print ('% Getting fileList')
    fileList = getFileList(datadir, first_date=first_date, last_date=last_date)
    
    for fili in fileList:

        if verbose: print ('   Regridding {:s}'.format(fili))
    
        srcField, srcAttrs = getField(fili, srcVarName, srcField)

        dstField = regrid(srcField, dstField)

        # Mask dstField
        dstField.data[...] = np.where(dstField.grid.mask[0] == 1, dstField.data, np.nan)

        filo = make_fileout(fili, dstGridName)
        if verbose: print ('   Writing regridded data to {:s}'.format(filo))
        writeNetCDF(dstField, srcAttrs, srcVarName, filo)

    return

def writeNetCDF(field, attrs, varName, filo):
    """
    Write data to NetCDF file
    """

    nx, ny = [360, 360]
    fill_value = 1e20
    
    rootgrp = Dataset(filo, 'w')

    x = rootgrp.createDimension('x', nx)
    y = rootgrp.createDimension('y', ny)
    
    lat = rootgrp.createVariable( 'latitude', 'f4', ('x','y',) )
    lon = rootgrp.createVariable( 'longitude', 'f4', ('x','y',) )
    var = rootgrp.createVariable( varName, 'f4', ('x','y',), fill_value=fill_value )

    rootgrp.created = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    rootgrp.created_by = 'A.P.Barrett <apbarret@nsidc.org>'

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
    parser.add_argument('srcGridName', type=str,
                        help='Name of source grid.  E.g. JRA55, CFSR2')
    parser.add_argument('dstGridName', type=str,
                        help='Name of destination grid.  Currently EASE grids')
    parser.add_argument('datadir', type=str, 
                        help='Path to directory containing data to regrid.  Assumes data is 2D')
    parser.add_argument('srcVarName', type=str,
                        help='Name of variable to read from source grid')
    parser.add_argument('--first_date', '-fd', action='store', default=None,
                        help='datestamp of first file to process YYYYMMDD')
    parser.add_argument('--last_date', '-ld', action='store', default=None,
                        help='datestamp of last file to process YYYYMMDD')
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

    regrid_batch(args.srcGridName, args.dstGridName, args.datadir, args.srcVarName,
         first_date=args.first_date, last_date=args.last_date,
         method=args.method, verbose=args.verbose)
