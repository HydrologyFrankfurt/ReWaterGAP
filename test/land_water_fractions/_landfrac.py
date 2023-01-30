# -*- coding: utf-8 -*-
"""
Created on Thu May 19 16:39:25 2022

@author: nyenah
"""
import xarray as xr
path = './test/land_water_fractions/'

cont_frac = xr.open_dataset(path + 'watergap2-2e'
                            '_gswp3-w5e5_obsclim_histsoc_default_contfrac_'
                            'global.nc')
cont_frac = cont_frac.contfrac.values

# Global lake and wetland
glo_wet = xr.open_dataset(path + 'watergap_22e_'
                          'v001_glowet.nc4', decode_times=False,)
glo_wet = glo_wet.glowet[0].values

glo_lake = xr.open_dataset(path + 'watergap_22e_'
                           'v001_glolak.nc4', decode_times=False,)
glo_lake = glo_lake.glolak[0].values

# local lake and wetland
loc_wet = xr.open_dataset(path + 'watergap_22e_'
                          'v001_locwet.nc4', decode_times=False,)
loc_wet = loc_wet.locwet[0].values

loc_lake = xr.open_dataset(path + 'watergap_22e_'
                           'v001_loclak.nc4', decode_times=False,)
loc_lake = loc_lake.loclak[0].values

# global and local reservior
glo_res = xr.open_dataset(path + 'watergap_22e_'
                          'v001_res.nc4', decode_times=False,)
glo_res = glo_res.res[0].values

loc_res = xr.open_dataset(path + 'watergap_22e_'
                          'v001_locres.nc4', decode_times=False,)
loc_res = loc_res.locres[0].values

# regulate lake
reg_lake = xr.open_dataset(path + 'watergap_22e_'
                           'v001_reglak.nc4', decode_times=False,)
reg_lake = reg_lake.reglak[0].values

# regulated lakes are found in global resevoiur
# local reservoir  is added to local lake

land_area_frac = \
    (cont_frac - (glo_lake + glo_wet + loc_lake + loc_wet + glo_res
                  + loc_res))/100
