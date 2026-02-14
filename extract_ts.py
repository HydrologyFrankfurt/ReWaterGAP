# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 20:48:58 2026

@author: hosseini
"""

import xarray as xr
import glob

lake_tharthar_lon = 43.25
lake_tharthar_lat = 33.75

# Path to your files
files = sorted(glob.glob("output_data_test/glores_outflow_*-12-31.nc"))

all_monthly = []

for f in files:
    
    # Open ONE file at a time (no combine)
    ds = xr.open_dataset(f)
    
    # Select nearest grid point
    point = ds.sel(lon=lake_tharthar_lon,
                   lat=lake_tharthar_lat,
                   method="nearest")
    
    # Replace 'outflow' with your real variable name if different
    var = point['glores_outflow']
    
    # Monthly mean (for m3/sec)
    monthly = var.resample(time="MS").mean()
    
    all_monthly.append(monthly)
    
    ds.close()

# Concatenate manually along time
monthly_series = xr.concat(all_monthly, dim="time")

# Sort time (important)
monthly_series = monthly_series.sortby("time")

# Save to CSV
monthly_series.to_dataframe().to_csv("monthly_outflow_1995_2019.csv")

print(monthly_series)
