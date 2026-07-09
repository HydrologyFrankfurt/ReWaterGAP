# -*- coding: utf-8 -*-

"""
Created on Tue July 6, 2026

@author: hosseini

Description:

This script modifies the static WaterGAP input NetCDF files to update the
Calueque reservoir capacity from 5 km3 to 0.535 km3. According to the report,
the Full Supply value is 475 million m3; however, the maximum estimated storage
capacity is 535 million m3.

Location:
    Longitude: 14.25
    Latitude: -17.25

The following file is modified:

    Maximum reservoir storage capacity:
    "reservoir_regulated_lake/watergap_22e_res_stor_cap.nc4"

Modification:
    * The value of the corresponding grid cell is updated to 0.535 km³.
"""
#%%
import xarray as xr
from pathlib import Path

base = Path("U:/Co-HYDIM-SA/ReWaterGAP/input_data/static_input")

# Target grid cell coordinates (calueque Reservoir)
target_lon = 14.25
target_lat = -17.25

# -------------------------------------------------
# Reservoir storage capacity [km³]
# -------------------------------------------------
print(40* "#")
print("modifying Reservoir storage capacity")

reservoir_storage_file = base / "reservoir_regulated_lake/watergap_22e_res_stor_cap.nc4"

ds = xr.open_dataset(reservoir_storage_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 0.535

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "reservoir_regulated_lake/watergap_22e_res_stor_cap_modified.nc4")
print("Done!")
del ds
#%%
print("Do you want to replace original files with *_modified versions?")
d = input("Please select y/n: ")
 
if d.lower() == "y":
    import gc

    # Make sure no dangling references / file handles remain before
    # touching the files on disk (important on Windows / network shares).
    gc.collect()
 
    for file in base.rglob("*_modified*"):
 
        # original filename = remove "_modified"
        original_file = Path(str(file).replace("_modified", ""))
 
        if original_file.exists():
            original_file.unlink()  # delete original
 
        # rename modified -> original name
        file.rename(original_file)
 
    print("Replacement complete.")