# -*- coding: utf-8 -*-
"""
Created on Sun Feb 4 17:33:08 2024
@author: nyenah
"""

import numpy as np
import xarray as xr

# Define dimensions
test = xr.open_dataset('../input_data/static_input/cell_area.nc', decode_times=False)
dummy = test.copy() * 0
values = test.cell_area.values * 0

# Define common attributes
attrs = {'units': '-'}

# Create xarray dataset
ds = dummy + 0.08
ds = ds.rename({"cell_area": "openwater_albedo"})
ds["openwater_albedo"].attrs.update({'long_name': 'Open Water Albedo', **attrs})

# Define data arrays
arrays = [
    ('snow_albedo_thresh', 3.0, 'mm'),
    ('pt_coeff_humid_arid', 1.26, '-'),
    ('max_storage_coefficient', 0.30, 'mm'),
    ('snow_freeze_temp', 273.15, 'K'),
    ('snow_melt_temp', 273.15, 'K'),
    ('adiabatic_lapse_rate', 0.006, 'K/m'),
    ('runoff_frac_builtup', 0.50, '-'),
    ('gamma', 2.0, '-'),
    ('areal_corr_factor', 1.0, '-'),
    ('max_daily_pet', 15.0, 'mm/day'),
    ('critcal_gw_precipitation', 12.5, 'mm/day'),
    ('gw_dis_coeff', 0.01, '-'),
    ('reduction_exponent_lakewet', 3.32193, '-'),
    ('gw_recharge_constant', 0.01, 'md⁻¹'),
    ('swb_outflow_coeff', 0.01, 'd⁻¹'),
    ('lake_out_exp', 1.5, '-'),
    ('activelake_depth', 5.0, 'm'),
    ('wetland_out_exp', 2.5, '-'),
    ('activewetland_depth', 2.0, 'm'),
    ('swb_drainage_area_factor', 20, '-'),
    ('reduction_exponent_res', 2.81383, '-'),
    ('stat_corr_fact', 1.0, '-')
]

long_names = [
    'Snow albedo threshold',
    'Priestley-Taylor coefficient for humid and arid regions',
    'Maximum storage coefficient',
    'Snow freeze temperature',
    'Snow melt temperature',
    'Adiabatic lapse rate',
    'Runoff fraction in built-up areas',
    'Runoff coefficient',
    'Areal correction factor',
    'Maximum daily potential evapotranspiration',
    'Critical precipitation threshold for groundwater recharge',
    'Groundwater discharge coefficient',
    'Reduction exponent for lakes and wetlands',
    'Groundwater recharge constant below lakes, reservoirs & wetlands',
    'Surface water outflow coefficient',
    'Lake outflow exponent',
    'Maximum lake active depth',
    'Wetland outflow exponent',
    'Maximum wetland active depth',
    'Surface water bodies drainage area factor',
    'Reduction exponent for reservoirs and regulated lakes',
    'Station correction factor'
]


# Populate xarray dataset with data arrays
for (name, value, unit), long_name in zip(arrays, long_names):
    ds[name] = xr.DataArray(value + values, coords=ds.coords, dims=('lat', 'lon'),
                            attrs={'long_name': f'{long_name}', 'units': unit})
# Define encoding for compression





encoding = {'chunksizes': [360, 720], "zlib": True, "complevel": 5}
encoding = {var: encoding for var in ds.data_vars}
# Save to netCDF file
ds.to_netcdf('WaterGAP_2.2e_parameters.nc', encoding=encoding)



#  add semi-arid coeff to PT coefficient
arid_humid = xr.open_dataset('../input_data/static_input/watergap_22e_aridhumid.nc4',
                             decode_times=False)
add_arid= arid_humid.aridhumid[0].values

ds = xr.open_dataset('WaterGAP_2.2e_parameters.nc', decode_times=False)
ds['pt_coeff_humid_arid'][:] = np.where( add_arid==1, 1.74, ds['pt_coeff_humid_arid'][:].values )



encoding = {'chunksizes': [360, 720], "zlib": True, "complevel": 5}
encoding = {var: encoding for var in ds.data_vars}
# Save to netCDF file
ds.to_netcdf('WaterGAP_2.2e_global_parameters.nc', encoding=encoding)
