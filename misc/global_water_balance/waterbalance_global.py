# -*- coding: utf-8 -*-
"""Compute long term annual average global water balance in km3/year."""

import xarray as xr
import numpy as np

# Please Note!!!.
# The follwing variables should be wriiten out (set to true in configuration file)

# [consistent_precipitation, streamflow, streamflow_from_upstream,
# cell_aet_consuse, total_water_storage, actual_water_consumption,
# actual_net_abstr_surfacewater, actual_net_abstr_groundwater]

# Units Conversion Note!!!:
#     if you comment out line 337-339 in run_watergap.py
#     thus the  "create_out_var.base_units(...)" function,  before running the
#     model there is not no need to convert data to km3/day or km3 as data will
#     not be in base units (fluxes = kgm-2-s-1,  discharge= m3/s or
#     storage = kgm-2)

commented_base_units = False   # set to False if no commenting out was done

# =============================================================================
# Set path to output variables
# =============================================================================
# Define the path where output variables will be saved or retrieved from

out_var_path = "../../output_data/"

# =============================================================================
#            Select the time period for the analysis
#       (make sure model data for start year-1 is available)
# =============================================================================
start_date = '1981-01-01'  # Start date for the waterbalance
end_date = '1981-12-31'    # End date for the waterbalance

# Extract start and end years from the dates
start_year = int(start_date[:4])
end_year = int(end_date[:4])

# Calculate the difference in years, including both start year
diff_in_years = (end_year - start_year) + 1

# To get previous total water storage change (tws_prev), ensure data for year 
# before the start year is available
year_before_start = str(start_year - 1)


# =============================================================================
# Load model parameters and other static variables
# =============================================================================
mask_greenland = xr.open_dataarray("greenland_masked.nc")
drainage_direction = xr.open_dataarray('../../input_data'
                                       '/static_input/soil_storage/watergap_22e_drainage_direction.nc',
                                       decode_times=False)

cell_area = xr.open_dataarray("../../input_data/static_input/watergap_22e_continentalarea.nc", 
                              decode_times=False)
contfrac = xr.open_dataarray("../../input_data/static_input/land_water_fractions/"
                             "watergap_22e_contfrac_global.nc", decode_times=False )

# Model parameters
params = xr.open_dataset("../../model/WaterGAP_2.2e_global_parameters.nc",
                         decode_times=False)

# Get station correction factor (CFS) from model parameters
# CFS is used to adjust actual evapotranspiration to maintain the water balance
cfs = params.stat_corr_fact.values


# =============================================================================
# Read in varibales for water balance.
# Note base units are kgm-2-s-1 for fluxes except discharge= m3/s. for storage
# base unit is  kgm-2.
# (if you commented create_out_var.base_units function no unit convertion needed,
# see  Units Conversion Note above)
# =============================================================================
# Consistent precipitation 
consist_precip = xr.open_mfdataset(out_var_path + "consistent-precipitation_*.nc")

# River discharge(streamflow) from cell and that from upstream
dis = xr.open_mfdataset(out_var_path + "dis_*.nc")
dis_upstream = xr.open_mfdataset(out_var_path + "dis-from-upstream_*.nc")

# Actual evapotranspiration (AET) including actual net abstraction from surface
# and groundwater
aet = xr.open_mfdataset(out_var_path + "evap-total_*.nc")

# Total Water Storage
tws = xr.open_mfdataset(out_var_path + "tws_*.nc")
tws_prev = xr.open_dataarray(out_var_path + "tws_" + year_before_start + "-12-31.nc")

# Net abstraction from surface and ground water (nas and nag).
# Sum of nas and nag is actual consumptive water Use
nas = xr.open_mfdataset(out_var_path + "atotusesw_*.nc")
nag = xr.open_mfdataset(out_var_path + "atotusegw_*.nc")
actual_cons_use = xr.open_mfdataset(out_var_path + "atotuse_*.nc")


# Select time period by slicing data based on the defined start and end dates
consist_precip = consist_precip.sel(time=slice(start_date, end_date))
dis = dis.sel(time=slice(start_date, end_date))
dis_upstream = dis_upstream.sel(time=slice(start_date, end_date))
aet = aet.sel(time=slice(start_date, end_date))
tws = tws.sel(time=slice(start_date, end_date))

actual_cons_use = actual_cons_use.sel(time=slice(start_date, end_date))
nas = nas.sel(time=slice(start_date, end_date))
nag = nag.sel(time=slice(start_date, end_date))

# =============================================================================
# Mask out greeland from data
# =============================================================================
consist_precip = consist_precip["consistent-precipitation"] / mask_greenland
dis = dis.dis / mask_greenland
dis_upstream = dis_upstream["dis-from-upstream"] / mask_greenland
aet = aet["evap-total"] / mask_greenland
tws = tws.tws / mask_greenland
tws_prev = tws_prev / mask_greenland

actual_cons_use = actual_cons_use.atotuse / mask_greenland
nas = nas.atotusesw/mask_greenland
nag = nag.atotusegw/mask_greenland
cfs = cfs/mask_greenland

# =======================================================================
# convert input data to from kgm-2-s-1 (mm/s) or kgm-2 (mm) to
# km3/day or km3 (if needed )
# =======================================================================
if commented_base_units:
    print('units already in km3/day or km3')
else:
    s_to_day = 86400
    mm_km3 = (cell_area * (contfrac/100))/1e6  # Convert mm to km³
    m3_km3 = 1e-9   # Convert m to km³

    # fluxes
    consist_precip = consist_precip * mm_km3 * s_to_day
    aet = aet * mm_km3 * s_to_day
    actual_cons_use = actual_cons_use * mm_km3 * s_to_day
    nas = nas * mm_km3 * s_to_day
    nag = nag * mm_km3 * s_to_day

    # note base unit of discharge is m3/s
    dis = dis * m3_km3 * s_to_day
    dis_upstream = dis_upstream * m3_km3 * s_to_day

    tws = tws * mm_km3
    tws_prev = tws_prev * mm_km3

# =============================================================================
# calulate annual means for variables (km3 / year)
# =============================================================================
consist_precip_annual_sum = consist_precip.resample(time='1Y').sum()
consist_precip_mean = consist_precip_annual_sum.mean(dim='time')

aet_annual_sum = aet.resample(time='1Y').sum()
aet_mean = aet_annual_sum.mean(dim='time')


dis_annual_sum = dis.resample(time='1Y').sum()
dis_mean = dis_annual_sum.mean(dim='time')


dis_without_cfs = dis_mean / cfs
cfs_diff = dis_without_cfs - dis_mean


dis_upstream_annual_sum = dis_upstream.resample(time='1Y').sum()
dis_upstream_mean = dis_upstream_annual_sum.mean(dim='time')

# inflow from inland sink
inflow_inland_sink = np.where(drainage_direction < 0, dis_upstream_mean, np.nan)

# change in total water storage
dtws = (tws[-1].values - tws_prev[-1])/diff_in_years

# Streamflow into ocean
Q_rg = dis_mean - dis_upstream_mean

actual_cons_use_annual_sum = actual_cons_use.resample(time='1Y').sum() 
actual_cons_use_mean = actual_cons_use_annual_sum.mean(dim='time')

nas_annual_sum = nas.resample(time='1Y').sum()
nas_mean = nas_annual_sum.mean(dim='time')

nag__annual_sum = nag.resample(time='1Y').sum()
nag_mean = nag__annual_sum.mean(dim='time')

# =============================================================================
# # Sum over all grid cell (km3 / year)
# =============================================================================
sum_consist_precip = np.nansum(consist_precip_mean)
sum_aet = np.nansum(aet_mean) + np.nansum(cfs_diff)  # cfs used for AET correction
sum_Q_rg = np.nansum(Q_rg)
sum_inflow_inlandsink = np.nansum(inflow_inland_sink)
sum_dtws = np.nansum(dtws)
sum_actual_cons_use = np.nansum(actual_cons_use_mean)
sum_nas = np.nansum(nas_mean)
sum_nag = np.nansum(nag_mean)

sum_wb_rg = sum_consist_precip - sum_Q_rg - sum_aet - sum_dtws

print("Precipitation: ", sum_consist_precip)
print("Actual evapotranspiration: ",  sum_aet)
print("Streamflow into oceans: ", sum_Q_rg)
print("Inflow into inland sinks: ", sum_inflow_inlandsink)
print("Actual consumptive water use: ", sum_actual_cons_use)
print("Actual net abstraction from surface water: ", sum_nas)
print("Actual net abstraction from groundwater: ", sum_nag)
print("Change of total water storage: ", sum_dtws)
print("Long-term average volume balance error: ", sum_wb_rg)
print("AET_CFS_corr", np.nansum(cfs_diff))
