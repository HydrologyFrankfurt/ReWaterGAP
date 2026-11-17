# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Temperature reduction factor (Tdiff) for modified Priestley-Taylor PET.

It is used by the modified Priestley-Taylor PET formulation of
Peiris & Doell (2023, https://doi.org/10.5194/hess-27-3663-2023) and is only
applied to climate change studies.

"""

import os
import glob
import xarray as xr


def temperature_reduction_factor(gcm, scenario, historical_tas_path,
                                 future_tas, ref_startyear, ref_endyear):
    
    """
    Calculate temperature reduction factor  using a 20-year moving window
    relative to the historical baseline period according to Peiris, T. A. and Döll, P, 2023.

    Parameters
    ----------
    gcm : str
        Global Climate Model.
    scenario : str
        Climate scenario.
    historical_tas_path : str
        Path to historical temperature data.
    future_tas : xarray.Dataset
        Future temperature data.
    ref_startyear : int
        Start year of the reference period.
    ref_endyear : int
        End year of the reference period.

    Returns
    -------
    xarray.DataArray
        Annual temperature difference in Kelvin.
    """

    # =================================================
    # 1. DEFINE OUTPUT FILE AND CHECK IF IT EXISTS
    # =================================================

    output_dir = "./output_data"

    existing_file = glob.glob(
    f"{output_dir}/{gcm}_{scenario}_temp_red_factor_*.nc")

    # If output already exists, read and return it
    if existing_file:
        print(f"Temperature reduction factor already exists for {gcm}_{scenario}")
        print("Loading existing file...")

        temp_red_factor = xr.open_dataset(existing_file[0])
        return temp_red_factor["Tdiff"]

    # =================================================
    # 2. LOAD HISTORICAL AND FUTURE DATA
    # =================================================

    historical_file = f"{historical_tas_path}*.nc"
    historical_files = sorted(glob.glob(historical_file))

    if not historical_files:
        raise FileNotFoundError(
            "No matching NetCDF files found for historical temperature."
        )

    ds_hist = xr.open_mfdataset(
        historical_files,
        chunks={"time": 365}
    )

    ds_future = future_tas.climate_forcing.temperature

    ds = xr.concat(
        [ds_hist, ds_future],
        dim="time"
    )

    temperature = ds["tas"]

    # =================================================
    # 3. DETERMINE AVAILABLE DATA PERIOD
    # =================================================
    available_years = temperature.time.dt.year.values

    data_start = int(available_years.min())
    data_end = int(available_years.max())
    
    # trend removal starts in 2001 according to Peiris, T. A. and Döll, P, 2023  
    target_start = 2001 
    target_end = min(2099, data_end)

    print(f"Available data period: {data_start}-{data_end}")

    # =================================================
    # 4. CHECK HISTORICAL REFERENCE PERIOD
    # =================================================

    reference_start = ref_startyear
    reference_end = ref_endyear

    required_reference_years = set(
        range(reference_start, reference_end + 1)
    )

    available_reference_years = set(
        int(y) for y in available_years
        if reference_start <= y <= reference_end
    )

    missing_years = sorted(
        required_reference_years - available_reference_years
    )

    if missing_years:
        raise ValueError(
            f"Historical reference period {ref_startyear}-{ref_endyear} "
            f"is incomplete. Missing years: {missing_years}"
        )

    # =================================================
    # 5. CALCULATE ANNUAL MEAN TEMPERATURE
    # =================================================
    month_temp = temperature.resample(time="1MS").mean()
    annual_temp = month_temp.resample(time="YS").mean()

    annual_years = annual_temp.time.dt.year.values

    annual_temp = annual_temp.assign_coords(
        time=annual_years
    ).rename({"time": "year"})

    # =================================================
    # 6. CALCULATE HISTORICAL BASELINE TEMPERATURE
    # =================================================

    Tbase = annual_temp.sel(
        year=slice(reference_start, reference_end)
    ).mean(
        dim="year",
        skipna=True
    )

    # =================================================
    # 7. CALCULATE MOVING-WINDOW TEMPERATURE DIFFERENCE
    # =================================================
    Tdiff_list = []

    for year in range(target_start, target_end + 1):

        window_start = max(year - 10, data_start)
        window_end = min(year + 9, data_end, 2099)

        Twindow_data = annual_temp.sel(
            year=slice(window_start, window_end)
        )

        if Twindow_data.sizes["year"] == 0:
            raise ValueError(
                f"No temperature data available for moving window of {year}."
            )

        Twindow = Twindow_data.mean(
            dim="year",
            skipna=True
        )

        Tdiff = Twindow - Tbase

        Tdiff = Tdiff.expand_dims(year=[year])

        Tdiff_list.append(Tdiff)

    # =================================================
    # 8. COMBINE RESULTS
    # =================================================

    Tdiff_all = xr.concat(
        Tdiff_list,
        dim="year"
    )

    Tdiff_all.name = "Tdiff"

    Tdiff_all.attrs["long_name"] = (
        "Temperature reduction factor")

    Tdiff_all.attrs["units"] = "K"

    Tdiff_all.attrs["reference_period"] = (
        f"{reference_start}-{reference_end}"
    )

    Tdiff_all.attrs["target_period"] = (
        f"{target_start}-{target_end}"
    )

    Tdiff_all.attrs["method"] = (
        "Moving 20-year annual mean temperature "
        "minus historical baseline annual mean temperature"
    )

   

    # =================================================
    # 9. SAVE RESULTS
    # =================================================
    output_file = (
        f"{output_dir}/{gcm}_{scenario}_temp_red_factor_"
        f"{target_start}_{target_end}.nc"
    )
    
    temp_red_factor = Tdiff_all
    temp_red_factor.to_netcdf(output_file)
    return temp_red_factor
