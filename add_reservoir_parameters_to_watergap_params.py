"""
Author: S. Mohammed Hosseini

===============================================================================
Script: add_reservoir_parameters_to_watergap_params.py

Purpose:
--------
This script extends the WaterGAP global parameter NetCDF file by adding six
new reservoir calibration parameters:

    P1_reservoir : January - February
    P2_reservoir : March - April
    P3_reservoir : May - June
    P4_reservoir : July - August
    P5_reservoir : September - October
    P6_reservoir : November - December

The parameters are created as spatially distributed gridded parameters with:

    - Value = 1.0 over land grid cells
    - Value = NaN over ocean grid cells

The land mask is derived from the WaterGAP continent fraction field
(cont_frac), ensuring consistency with the existing WaterGAP parameter
structure.

These parameters are intended for later calibration using optimization
methods (e.g., Genetic Algorithm, GA). Each parameter represents a seasonal
(two-month) reservoir parameter that can be optimized independently.

Input:
------
WaterGAP_2.3_global_parameters_gswp3_era5.nc

Output:
-------
WaterGAP_2.3_global_parameters_gswp3_era5_with_reservoir.nc

===============================================================================
"""

import xarray as xr
import numpy as np


# =============================================================================
# Input and output files
# =============================================================================

input_file = "./model/WaterGAP_2.3_global_parameters_gswp3_era5.nc"

output_file = "./model/WaterGAP_2.3_global_parameters_gswp3_era5_with_reservoir.nc"



# =============================================================================
# Open existing parameter file
# =============================================================================

# decode_times=False because this file contains model parameters,
# not time series data.

ds = xr.open_dataset(
    input_file,
    decode_times=False
)



# =============================================================================
# Add reservoir parameters
# =============================================================================
#
# Each parameter represents a two-month reservoir parameter:
#
# P1_reservoir -> January-February
# P2_reservoir -> March-April
# P3_reservoir -> May-June
# P4_reservoir -> July-August
# P5_reservoir -> September-October
# P6_reservoir -> November-December
#
# All land grid cells receive the initial value = 1.0
# Ocean cells remain NaN.
#



reservoir_parameters = {

    "P1_reservoir": "Reservoir parameter for January and February",

    "P2_reservoir": "Reservoir parameter for March and April",

    "P3_reservoir": "Reservoir parameter for May and June",

    "P4_reservoir": "Reservoir parameter for July and August",

    "P5_reservoir": "Reservoir parameter for September and October",

    "P6_reservoir": "Reservoir parameter for November and December"

}



# =============================================================================
# Create land mask
# =============================================================================
#
# WaterGAP parameters are defined only over land.
#
# cont_frac:
#     0      -> ocean
#     > 0    -> land
#
# Land cells will receive value 1.0.
# Ocean cells will remain NaN.
#


land_fraction = ds["snow_freeze_temp"]


land_mask = land_fraction > 0



# Create reservoir parameter field

reservoir_values = xr.where(

    land_mask,

    1.0,

    np.nan

)



# =============================================================================
# Add parameters to dataset
# =============================================================================

for param_name, description in reservoir_parameters.items():


    ds[param_name] = reservoir_values.copy()


    ds[param_name].attrs = {

        "long_name": description,

        "units": "-"

    }



# =============================================================================
# Save new NetCDF file
# =============================================================================

encoding = {}


for var in reservoir_parameters:

    encoding[var] = {

        "_FillValue": np.nan

    }



ds.to_netcdf(

    output_file,

    encoding=encoding

)



print(
    "New parameter file saved:"
)

print(
    output_file
)