#----------------------------------------------------------------------
# Plots regridded TOTPREC field to check regridding
#
# 2018-05-24 A.P.Barrett
#----------------------------------------------------------------------

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os

import cartopy.crs as ccrs

def main():

    diri = '/projects/arctic_scientist_data/Reanalysis/JRA55/daily/TOTPREC/2017'
    ds = xr.open_mfdataset(os.path.join(diri,'??','JRA55.fcst_phy2m.TOTPREC.????????.Nh50km.nc'),
                           concat_dim='time')

    totprec = ds['TOTPREC'].sum(dim='time', skipna=False).load().data
    lat = ds['latitude'][0,:,:].load().data
    lon = ds['longitude'][0,:,:].load().data
    ds.close()

    lat = np.where(lat > -998., lat, np.nan)
    lon = np.where(lon > -998., lon, np.nan)

#    print (totprec[lat > 50.].min(), totprec[lat > 50.].max())

    levels = np.linspace(0,30000,10)
    
    map_proj = ccrs.NorthPolarStereo()

    coords = map_proj.transform_points(ccrs.PlateCarree(), lon, lat)

    fig = plt.figure(figsize=(15,10))
    ax = plt.subplot(projection=map_proj)
    ax.set_extent([-180.,180.,50.,90.], ccrs.PlateCarree())
    
    cs = ax.contourf( coords[:,:,0], coords[:,:,1], totprec, levels=levels, extend='both' )
    ax.coastlines()

    cb = plt.colorbar(cs, ax=ax)

    plt.show()
    
    return

if __name__ == "__main__":
    main()

