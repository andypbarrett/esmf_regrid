#----------------------------------------------------------------------
# Calculates daily total precipitation from 3h average precipitation
# for JRA55.
#
# 2018-05-18 A.P.Barrett <apbarret@nsidc.org>
#----------------------------------------------------------------------

import xarray as xr
import os
import numpy as np
import glob

vardict = {
           'TOTPREC': {'filevar': '061_tprat', 'gribvar': 'TPRAT_GDS4_SFC_ave3h'},
           'SNOFALL': {'filevar': '064_srweq', 'gribvar': 'SRWEQ_GDS4_SFC_ave3h'},
           }

def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

def make_fileout(fili, date, reanalysis, variable, grid=None):

    datestamp = '{:4d}{:02d}{:02d}'.format(date.dt.year.data,
                                           date.dt.month.data,
                                           date.dt.day.data)

    dirpath = os.path.join(os.path.join( *splitall(fili)[0:-2] ), 
                           variable, 
                           '{:4d}'.format(date.dt.year.data),
                           '{:02d}'.format(date.dt.month.data) )

    fname = '{:s}.{:s}.{:s}.{:s}.nc'.format(reanalysis,
                                            os.path.basename(fili).split('.')[0],
                                            variable,
                                            datestamp)

    return os.path.join(dirpath, fname)

def process_onefile(fili, verbose=False):

    ds = xr.open_dataset(fili)

    nt = ds.coords['initial_time0_hours'].size
    
    for it in np.arange(0,nt,4):

        # Aggregate 3h average precipitation to daily total
        # N.B. Units are already mm/day so only need to sum 
        dayP = ds['TPRAT_GDS4_SFC_ave3h'][it:it+4,:,:,:].sum(dim=('initial_time0_hours', 'forecast_time1'))
        # Set name and attributes
        dayP.name = 'TOTPREC'
        dayP.attrs = ds['TPRAT_GDS4_SFC_ave3h'].attrs
        # Change coordinate names
        dayP = dayP.rename({'g4_lat_2': 'lat', 'g4_lon_3': 'lon'})
        
        dsout = xr.Dataset({'TOTPREC': dayP}, attrs=ds.attrs)

        filo = make_fileout(fili, ds.coords['initial_time0_hours'][it], 'JRA55', 'TOTPREC')
        if verbose: print ('% process_onefile: writing data to '+filo)
        if not os.path.exists( os.path.dirname(filo) ):
            os.makedirs( os.path.dirname(filo) )
        dsout.to_netcdf( filo )

    return

def process_jra55(variable, verbose=False):

    diri = '/projects/arctic_scientist_data/Reanalysis/JRA55/daily/temp'
    fileList = glob.glob( os.path.join( diri,'fcst_phy2m.{:s}.*.nc.gz'.format(vardict[variable]['filevar']) ) )

    for f in fileList:
        if verbose: print ( '% process_jra55_totprec: Processing '+f )
        #process_onefile( f, verbose=verbose )
        
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Parses JRA55 variables form 3h averages to daily totals')
    parser.add_argument('variable', type=str, help='Name of variable')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()
    
    process_jra55( args.variable, verbose=args.verbose )
    
        
