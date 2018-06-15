#----------------------------------------------------------------------
# Tests regridding and field definition using an analytic field
#
# 2018-05-17 A.P.Barrett <apbarret@nsidc.org>
#----------------------------------------------------------------------
import ESMF
import numpy as np
import matplotlib.pyplot as plt

#from regrid import ESMF_makeEASEGrid, ESMF_makeLLGrid
from regrid import ESMF_GenRegridWeights

from constants import srcGridFile, dstGridFile, weightsFile, regridMethods

def analyticField(field):

    DEG2RAD = np.pi / 180.
    [x, y] = [0, 1]
    
    gridXCoord = field.grid.get_coords(x, ESMF.StaggerLoc.CENTER)
    gridYCoord = field.grid.get_coords(y, ESMF.StaggerLoc.CENTER)

    field.data[:] = 2.0 + np.cos(DEG2RAD*gridXCoord)**2 * \
                    np.cos(2.0*DEG2RAD*(90.0 - gridYCoord))
    
    return field

def getField(fili, varName, field):
    """
    Reads a field from a netCDF file and writes to srcField object
    """

    import xarray as xr

    ds = xr.open_dataset(fili)

    print (ds[varName])
    
    field.data[:] = ds[varName].data.T

    return field

def main(srcGridName, dstGridName, srcGridFile=None, srcVarName=None, src_mask_values=None, dst_mask_values=None,
         method='bilinear'):

    ESMF.Manager(debug=True)

    regrid, srcField, dstField = ESMF_GenRegridWeights(srcGridName, dstGridName, method=method)

    if srcGridFile:
        srcField = getField(srcGridFile, srcVarName, srcField)
    else:
        srcField = analyticField(srcField)

    dstField = regrid(srcField, dstField)

    # Mask dstField
    dstField.data[...] = np.where(dstField.grid.mask[0] == 1, dstField.data, np.nan)
    
    fig, ax = plt.subplots( 1, 2, figsize=(10,7))

    ax[0].imshow(srcField.data.T)
    ax[0].set_title('Original Field')
    
    ax[1].imshow(dstField.data.T.reshape(360,360))
    ax[1].set_title('Regridded Field')
    
    plt.show()
    
    return

if __name__ == "__main__":

    import argparse
    
    parser = argparse.ArgumentParser(description='Regrids an analytical field or a field read from a file',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('srcGridName', type=str,
                        help='Name of source grid.  E.g. JRA55, CFSR2')
    parser.add_argument('dstGridName', type=str,
                        help='Name of destination grid.  Currently EASE grids')
    parser.add_argument('--srcGridFile', '-sf', action='store', default=None,
                        help='Path to file containing a source grid.  Assumes data is 2D')
    parser.add_argument('--srcVarName', '-sn', action='store', default=None,
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

    args = parser.parse_args()
                        
    main(args.srcGridName, args.dstGridName, srcGridFile=args.srcGridFile,
         srcVarName=args.srcVarName, method=args.method)
