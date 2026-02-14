# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 20:48:58 2026

@author: hosseini
"""

import xarray as xr
import glob
import os

lake_tharthar_lon = 43.25
lake_tharthar_lat = 33.75

# ---------------------------------------
# Define period you want to read
# ---------------------------------------
start_year = 2003
end_year   = 2019

# Get all files
all_files = sorted(glob.glob("output_data_test/glores_outflow_*-12-31.nc"))

# ---------------------------------------
# Filter files based on year in filename
# ---------------------------------------
selected_files = []

for f in all_files:
    filename = os.path.basename(f)
    
    # Extract year from filename
    # Example: glores_outflow_1987-12-31.nc
    year = int(filename.split("_")[2].split("-")[0])
    
    if start_year <= year <= end_year:
        selected_files.append(f)

print(f"Selected {len(selected_files)} files from {start_year} to {end_year}")

all_monthly = []

for f in selected_files:
    
    ds = xr.open_dataset(f)
    
    point = ds.sel(lon=lake_tharthar_lon,
                   lat=lake_tharthar_lat,
                   method="nearest")
    
    var = point['glores_outflow']
    
    monthly = var.resample(time="MS").mean()
    
    all_monthly.append(monthly)
    
    ds.close()

monthly_series = xr.concat(all_monthly, dim="time")
monthly_series = monthly_series.sortby("time")

output_filename = f"monthly_outflow_{start_year}_{end_year}.csv"
monthly_series.to_dataframe().to_csv(output_filename)

print(f"Saved file: {output_filename}")
print(monthly_series)
