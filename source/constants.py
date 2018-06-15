"""
Constants used in ESMF regridding routines
"""
import os
import ESMF

DATADIR = '/home/apbarret/src/ESMF_regrid/data'

srcGridFile = {'CFSR2': os.path.join(DATADIR, 'CFSR2_361x720_SCRIP.nc'),
               'JRA55': '/projects/arctic_scientist_data/Reanalysis/JRA55/daily/TOTPREC/1979/01/JRA55.fcst_phy2m.TOTPREC.19790101.nc',}
dstGridFile = {'EASE_NH50km': os.path.join(DATADIR, 'EASE_NH50km_ESMF.nc'),}

weightsFile = {'CFSR2': os.path.join(DATADIR, 'CFSR2_EASE_ESMF_bilinear_weights.nc'), }

regridMethods = {'bilinear': ESMF.RegridMethod.BILINEAR,
                 'nearest_stod': ESMF.RegridMethod.NEAREST_STOD,
                 'nearest_dtos': ESMF.RegridMethod.NEAREST_DTOS,
                 'patch': ESMF.RegridMethod.PATCH,
                 'conserve': ESMF.RegridMethod.CONSERVE}
              
