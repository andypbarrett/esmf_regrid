import xarray as xr
import os, glob

def my_strftime(t):
    return '{:4d}{:02d}{:02d}'.format(t.dt.year.values, t.dt.month.values, t.dt.day.values)

def make_fileout(fili, time):
    return os.path.join( os.path.dirname(fili),
                         '{:02d}'.format(time.dt.month.values),
                         'era_interim.PRECTOT.{:6s}.nc'.format(my_strftime(time)) )

def extract_day(fili, verbose=False):
    """
    Extracts and writes days to individual files
    """

    if verbose: print ( '% extract_day: Getting data from {:s}'.format(fili) )
    ds = xr.open_dataset(fili)

    # Fix lat and lons
    ds.rename({'lon': 'lat', 'lat': 'lon'}, inplace=True)

    # write individuals days to files
    for time in ds['time']:

        if verbose: print ( '... Extracting data for {:6s}'.format(my_strftime( time )) )
                           
        # Generate filename
        filo = make_fileout(fili, time)

        # Create output directory YYYY/MM if it doesn't exist
        if not os.path.exists( os.path.dirname(filo) ):
            if verbose: print ( '... Creating directory {:s}'.format(os.path.dirname(filo)) )
            os.makedirs( os.path.dirname(filo) )
            
        # Write single time to netcdf4
        if verbose: print ( '... Writing data to {:s}'.format(filo) )
        ds['PRECTOT'].sel(time=time).to_netcdf(filo)
        
    return

def main():

    fileList = glob.glob('/disks/arctic5_raid/abarrett/ERA_Interim/daily/PRECTOT/????/era_interim.PRECTOT.??????.day.nc')
    for f in fileList:
        extract_day(f, verbose=True)

    return

if __name__ == "__main__":
    main()

                            
