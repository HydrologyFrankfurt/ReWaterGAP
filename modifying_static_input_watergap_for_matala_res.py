# -*- coding: utf-8 -*-

"""
Created on Tue July 6, 2026

## @author: hosseini

Description:

This script modifies the static WaterGAP input NetCDF files to convert the Matala Reservoir
(lon: 15.25, lat: -14.75) from a local reservoir to a global reservoir in the Cunene Basin.

The following files are modified:

1. GLWD_UNIT ("watergap_22e_glwdunits.nc")

   * Assigns a new GLWD_UNIT value (2473) to the corresponding grid cell.

2. Outflow cell (gcrc) ("reservoir_regulated_lake/watergap_22e_outflowcell_assignment_glores.nc")

   * Assigns a new outflow cell value (59328) to the corresponding grid cell.

3. Maximum reservoir area ("land_water_fractions/watergap_22e_reservoir_and_regulated_lake_area.nc")

   * Sets the value of the corresponding grid cell to 19.3 km² (estimated from GRanD and Google Earth).

4. Maximum reservoir storage capacity ("reservoir_regulated_lake/watergap_22e_res_stor_cap.nc4")

   * Sets the value of the corresponding grid cell to 0.06 km³ (estimated from Google).

5. Maximum fraction of local reservoir ("land_water_fractions/watergap_22e_locres.nc4")

   * Sets the value of the corresponding grid cell to zero.

6. Reservoir type ("reservoir_regulated_lake/watergap_22e_reservoir_type.nc4")

   * Sets the value of the corresponding grid cell to 2 (main purpose: hydropower generation).

7. Reservoir start year ("reservoir_regulated_lake/watergap_22e_startyear.nc4")

   * Sets the value of the corresponding grid cell to 1954.

8. Global reservoir fraction ("watergap_22e_gloresfrac_1901_2025.nc")

   * Sets the value of the corresponding grid cell to reservoir_area / cell_area (constant for all years).

The target grid cell is identified using the longitude and latitude coordinates.
"""
#%%
import xarray as xr
from pathlib import Path

base = Path("U:/Co-HYDIM-SA/ReWaterGAP/input_data/static_input")

# Target grid cell coordinates (Matala Reservoir)
target_lon = 15.25
target_lat = -14.75

#%%
# -------------------------------------------------
# GLWD unit
# -------------------------------------------------
print(40* "#")
print("modifying GLWD unit")

glwd_file = base / "watergap_22e_glwdunits.nc"

ds = xr.open_dataset(glwd_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 2473

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "watergap_22e_glwdunits_modified.nc")

print("Done!")
del ds
#%%
# -------------------------------------------------
# Outflow cell (GCRC)
# -------------------------------------------------
print(40* "#")
print("modifying Outflow cell")

outflow_cell_file = base / "reservoir_regulated_lake/watergap_22e_outflowcell_assignment_glores.nc"

ds = xr.open_dataset(outflow_cell_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 59328

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "reservoir_regulated_lake/watergap_22e_outflowcell_assignment_glores_modified.nc")
print("Done!")
del ds
#%%
# -------------------------------------------------
# Reservoir area [km²]
# -------------------------------------------------
print(40* "#")
print("modifying Reservoir area")

reservoir_area_file = base / "land_water_fractions/watergap_22e_reservoir_and_regulated_lake_area.nc"

ds = xr.open_dataset(reservoir_area_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 19.3

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "land_water_fractions/watergap_22e_reservoir_and_regulated_lake_area_modified.nc")
print("Done!")
del ds
#%%
# -------------------------------------------------
# Reservoir storage capacity [km³]
# -------------------------------------------------
print(40* "#")
print("modifying Reservoir storage capacity")

reservoir_storage_file = base / "reservoir_regulated_lake/watergap_22e_res_stor_cap.nc4"

ds = xr.open_dataset(reservoir_storage_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 0.06

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "reservoir_regulated_lake/watergap_22e_res_stor_cap_modified.nc4")
print("Done!")
del ds
#%%
# -------------------------------------------------
# Local reservoir fraction
# -------------------------------------------------
print(40* "#")
print("modifying Local reservoir fraction")

locres_fractions_file = base / "land_water_fractions/watergap_22e_locres.nc4"

ds = xr.open_dataset(locres_fractions_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 0.0

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "land_water_fractions/watergap_22e_locres_modified.nc4")
print("Done!")
del ds
#%%
# -------------------------------------------------
# Reservoir type
# -------------------------------------------------
print(40* "#")
print("modifying Reservoir type")

reservoir_type_file = base / "reservoir_regulated_lake/watergap_22e_reservoir_type.nc4"

ds = xr.open_dataset(reservoir_type_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 2

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "reservoir_regulated_lake/watergap_22e_reservoir_type_modified.nc4")
print("Done!")
del ds
#%%
# -------------------------------------------------
# Reservoir start year
# -------------------------------------------------
print(40* "#")
print("modifying Reservoir start year")

reservoir_start_year_file = base / "reservoir_regulated_lake/watergap_22e_startyear.nc4"

ds = xr.open_dataset(reservoir_start_year_file, decode_times=False)
var = list(ds.data_vars)[0]

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 1954

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "reservoir_regulated_lake/watergap_22e_startyear_modified.nc4")
print("Done!")
del ds
#%%
# -------------------------------------------------
# Global reservoir fraction
# -------------------------------------------------
print(40* "#")
print("Global reservoir fraction")

gloresfrac_file = base / "watergap_22e_gloresfrac_1901_2025.nc"
cell_area_file = base / "watergap_22e_continentalarea.nc"

ds = xr.open_dataset(gloresfrac_file, decode_times=False)
ds_area = xr.open_dataset(cell_area_file, decode_times=False)

var = list(ds.data_vars)[0]
var_area = list(ds_area.data_vars)[0]

cell_area = ds_area[var_area].sel(lon=target_lon, lat=target_lat, method="nearest").values

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds[var].loc[dict(lon=target_lon, lat=target_lat)] = 19.3 / cell_area * 100

print(ds[var].sel(lon=target_lon, lat=target_lat, method="nearest").values)

ds.to_netcdf(base / "watergap_22e_gloresfrac_1901_2025_modified.nc")
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