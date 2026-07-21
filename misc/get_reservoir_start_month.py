# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 11:01:29 2026

@author: nyenah
"""
import xarray as xr
import numpy as np
from numba import njit
from pathlib import Path


@njit(cache=True)
def find_reservoir_start_month(monthly_mean, annual_mean, dry_start):
    """
    Find the starting month of the longest dry period for each grid cell.

    A month is considered dry when

        monthly_mean < annual_mean

    The search starts from the first wet month so that a dry season
    spanning December–January is treated as one continuous period.

    Parameters
    ----------
    monthly_mean : ndarray of float64
        Monthly climatological mean with shape (12, nlat, nlon).

    annual_mean : ndarray of float64
        Annual mean with shape (nlat, nlon).

    Returns
    -------
    ndarray of int32
        Array of shape (nlat, nlon).

        Values:
            1-12 : Start month of the longest dry season
             1    : Default value when no dry months exist
    """
    

    nlat, nlon = annual_mean.shape    
    print(dry_start)
    
    for i in range(nlat):
        for j in range(nlon):
            # Skip cells where annual mean is NaN
            if np.isnan(annual_mean[i, j]):
                continue
            
            # this cell will not be computed as a reservoir anyways since it recieves no inflow 
            if annual_mean[i, j] == 0:
                dry_start[i, j] = 1 
                continue
            # -----------------------------------------------------------------
            # Identify dry months
            # -----------------------------------------------------------------
            dry = np.empty(12, dtype=np.bool_)

            has_dry = False
            for m in range(12):
                dry[m] = monthly_mean[m, i, j] < annual_mean[i, j]
                if dry[m]:
                    has_dry = True

            if not has_dry:
                continue

            # -----------------------------------------------------------------
            # Find the first wet month.
            # Starting from here avoids splitting a dry season that spans
            # December -> January.
            # -----------------------------------------------------------------
            first_wet = 0
            while first_wet < 12 and dry[first_wet]:
                first_wet += 1

            longest_length = 0
            current_length = 0

            longest_start = 0
            current_start = 0

            last_dry = True

            # -----------------------------------------------------------------
            # Search one complete annual cycle
            # -----------------------------------------------------------------
            for k in range(12):

                month = (first_wet + k) % 12

                if dry[month]:
                    current_length += 1
                    if not last_dry:
                        current_start = month
                        last_dry = True
                        
                elif last_dry:

                    # Dry spell has just ended.
                    last_dry = False

                    # Update the longest dry spell if necessary.
                    if current_length > longest_length:
                        longest_length = current_length
                        longest_start = current_start

                        current_length = 0

            # Handle dry spell reaching the end of the loop
            if current_length > longest_length:
                longest_length = current_length
                longest_start = current_start

            dry_start[i, j] = longest_start + 1

    return dry_start


def save_start_month_netcdf(start_month, monthly_mean_file, output_dir="."):
    """
    Save start month result as NetCDF.
    
    Output name depends on input dataset:
        ERA5  -> startmonth_era5.nc
        W5E5  -> startmonth_w5e5.nc
    """

    # Identify dataset type from filename
    filename = monthly_mean_file.lower()

    if "watergap_22e_era5" in filename:
        dataset_name = "era5"
    elif "watergap_22e_w5e5" in filename:
        dataset_name = "w5e5"
    else:
        raise ValueError(
            "Cannot identify dataset. Filename must contain 'era5' or 'w5e5'."
        )

    output_file = f"{output_dir}/watergap_22e_{dataset_name}_startmonth.nc"

    # Open original file to get coordinates
    ds = xr.open_dataset(monthly_mean_file, decode_times=False)

    # Create DataArray
    start_month = start_month[np.newaxis, :, :]
    da = xr.DataArray(
        start_month,
        dims=("time", "lat", "lon"),
        coords={
            "time":[-1.9e+03], #just to match old version 
            "lat": ds.lat,
            "lon": ds.lon
        },
        name="startmonth"
    )

    # Add metadata
    da.attrs = {
        "long_name": "Reservoir start month",
        "description": (
            "Month when the longest continuous dry season begins. "
            "Dry months defined as monthly mean < annual mean."
        ),
        "units": "month"
    }

    # Save
    da.to_netcdf(output_file)

    print(f"Saved: {output_file}")

    return output_file


# =============================================================================
# Change path to input file for respective forcing 
# =============================================================================
monthly_mean_inflow_path = Path(
    "../static_input/reservoir_regulated_lake/reservoir_routing_era5/watergap_22e_era5_monthly_mean_inflow.nc4"
)
annual_mean_inflow_path = Path(
    "../static_input/reservoir_regulated_lake/reservoir_routing_era5/watergap_22e_era5_mean_inflow.nc4"
)

# Output directory
output_dir = Path("../static_input/reservoir_regulated_lake/reservoir_routing_era5/")

# Check that both input files exist
if monthly_mean_inflow_path.exists() and annual_mean_inflow_path.exists():

    annual_mean = xr.open_dataarray(
        annual_mean_inflow_path, decode_times=False
    )
    monthly_mean = xr.open_dataarray(
        monthly_mean_inflow_path, decode_times=False
    )

    annual_mean = annual_mean[0].values
    monthly_mean = monthly_mean.values

    dry_start = np.full(annual_mean.shape, np.nan, dtype=np.float32)
    valid = ~np.isnan(annual_mean)
    dry_start[valid] = 0

    start_month = find_reservoir_start_month(
        monthly_mean, annual_mean, dry_start
    )

    save_start_month_netcdf(
        start_month,
        str(monthly_mean_inflow_path),
        output_dir=str(output_dir)
    )

else:
    print("Required input file(s) not found.")
    if not monthly_mean_inflow_path.exists():
        print(f"Missing: {monthly_mean_inflow_path}")
    if not annual_mean_inflow_path.exists():
        print(f"Missing: {annual_mean_inflow_path}")