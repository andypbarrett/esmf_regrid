"""
Constants used in ESMF regridding routines
"""
import os
import ESMF

DATADIR = '/home/apbarret/src/ESMF_regrid/data'

srcGridFile = {'CFSR2': '/disks/arctic5_raid/abarrett/CFSR2/TOTPREC/2011/01/CFSR2.cdas1.pgrbh.TOTPREC.20110101.nc4',
               'CFSR': '/disks/arctic5_raid/abarrett/CFSR/TOTPREC/1979/01/CFSR.pgbh01.gdas.TOTPREC.19790101.nc4',
               'JRA55': '/projects/arctic_scientist_data/Reanalysis/JRA55/daily/TOTPREC/1979/01/JRA55.fcst_phy2m.TOTPREC.19790101.nc',
               'MERRA': '/disks/arctic5_raid/abarrett/MERRA/daily/PRECTOT/1979/01/MERRA100.prod.PRECTOT.assim.tavg1_2d_flx_Nx.19790101.nc4',
               'ERAI': '/disks/arctic5_raid/abarrett/ERA_Interim/daily/PRECTOT/1979/01/era_interim.PRECTOT.19790101.nc',
               'MERRA2': '/disks/arctic5_raid/abarrett/MERRA2/daily/PRECTOT/1980/01/MERRA2_100.tavg1_2d_flx_Nx.PRECTOT.19800101.nc4',
               'ASR': '',
               'ERA5': '/projects/arctic_scientist_data/Reanalysis/ERA5/daily/TOTPREC_global/2000/01/era5.single_level.TOTPREC.20000101.nc4',
               'ERA5-45N': '/projects/arctic_scientist_data/Reanalysis/ERA5/daily/TOTPREC/1979/01/era5.single_level.daily.TOTPREC.197901.nc4',}

dstGridFile = {'EASE_NH50km': os.path.join(DATADIR, 'EASE_NH50km_ESMF.nc'),}

weightsFile = {'CFSR2': os.path.join(DATADIR, 'CFSR2_EASE_ESMF_bilinear_weights.nc'), }

regridMethods = {'bilinear': ESMF.RegridMethod.BILINEAR,
                 'nearest_stod': ESMF.RegridMethod.NEAREST_STOD,
                 'nearest_dtos': ESMF.RegridMethod.NEAREST_DTOS,
                 'patch': ESMF.RegridMethod.PATCH,
                 'conserve': ESMF.RegridMethod.CONSERVE}
              
