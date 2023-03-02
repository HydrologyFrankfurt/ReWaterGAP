# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Optimised snow water storage."""

# =============================================================================
# This module calulates snow water water balance, including snow water storage
# and related fluxes based on section 4.3 of (Müller Schmied et al. (2021)).
# Simulation of the snow dynamics is calculated such that each grid is
# subdivided into 100 non localized subgrids that are assigned different land
# surface elevations according to GTOPO30 (U.S. Geological Survey, 1996).
# For model output, subgrid values are aggregated to 0.5 degree cell value.
# This module uses numba (See https://numba.pydata.org/) to optimizes the
# runtime speed of the snow water storage funtion by perfoming calulations in
# parallel (see subgrid_snow_balance_parallel function ).
# =============================================================================

import numpy as np
from numba import njit, prange

# @njit is a decorator from numba to optimised the python code for speed.


@njit(nogil=True)
def subgrid_snow_balance(snow_water_storage, snow_water_storage_subgrid,
                         temperature, precipitation, throughfall, pet_to_soil,
                         land_storage_change_sum, degreeday,
                         current_landarea_frac, landareafrac_ratio,
                         elevation, daily_storage_transfer,
                         adiabatic_lapse_rate,  snow_freeze_temp,
                         snow_melt_temp):
    """
    Compute snow water balance for subgrids including snow water storage and
    water flows entering and leaving the snow storage

    Parameters
    ----------
    snow_water_storage : array
        Snow water storage, Units: mm
    snow_water_storage_subgrid : array
        Snow water storage divided into 100 subgrids based on GTOPO30 (U.S.
        Geological Survey, 1996) land surface elevation map, Units: mm
    temperature : array
        Daily temperature climate forcing, Units: K.
    precipitation : array
        Daily precipitation,  Units: mm/day
    throughfall : array
       Throughfall,  Units: mm/day
    pet_to_soil : array
        Remaining energy for addtional soil evaporation, Units: mm/day
    land_storage_change_sum : array
        Sum of change in vertical balance storages, Units: mm
    degreeday : array
        Land cover specific degreeday values based on [2]_ .Units: mm/day/C
    current_landarea_frac : array
      Land area fraction of current time step,  Units: (-)
    landareafrac_ratio : array
       Ratio of land area fraction of previous to current time step, Units: (-)
    elevation : array
        and surface elevation map based on GTOPO30 (U.S.
        Geological Survey, 1996) [1]_. Units: m
    daily_storage_transfer : array
        Storage to be transfered to runoff when land area fraction of current
        time step is zero, Units: mm
    adiabatic_lapse_rate: array
        Adiabatic lapse rate , Units:  K/m or °C/m
    snow_freeze_temp: array
        Snow freeze temperature  , Units:  K
    snow_melt_temp: array
        Snow melt temperature  , Units:  K

    Returns
    -------
    snow_water_storage : array
        Updated snow water storage, Units: mm
    snow_water_storage_subgrid : array
        Updated snow water storage divided into 100 subgrids based on GTOPO30
        (U.S. Geological Survey, 1996) land surface elevation map, Units: mm
    snow_fall : array
        Snowfall, Units: mm/day
    sublimation : array
        Sublimation, Units: mm/day
    snow_melt : array
        Snow melt, Units: mm/day
    effective_precipitation : array
        Effective Precipitation, Units: mm/day
    max_temp_elev : array
        Maximum temperature from the 1st(lowest) elevation, Units: K
    land_storage_change_sum : array
       Sum of change in vertical balance storages, Units: mm
    daily_storage_transfer : array
       Updated storage to be transfered to runoff when land area fraction
       of current time step is zero, Units: mm

    References.

    .. [1] U.S. Geological Survey: USGS EROS archive – digital elevation–
                global 30 arc-second elevation (GTOPO30), available at:
                https://www.usgs.gov/centers/eros/science/usgs-eros-archivedigital-elevation-global-30-arc-second-elevation-gtopo30?qtscience_center_objects=0#qt-science_center_objects
                (last access: 25 MArch 2020), 1996

    """
    # Note!!! snow_water_storage_subgrid is averaged and added to
    # snow_water_storage ouput variable. Hence snow_water_storage is always
    # initilised to zero to prevent double counting for subsequent time steps.
    snow_water_storage *= 0

    # =====================================================================
    # Creating output variables
    # =====================================================================
    snow_fall = np.zeros(snow_water_storage.shape)
    sublimation = np.zeros(snow_water_storage.shape)
    snow_melt = np.zeros(snow_water_storage.shape)
    effective_precipitation = np.zeros(snow_water_storage.shape)
    max_temp_elev = np.zeros(snow_water_storage.shape)

    # =====================================================================
    # Extracting elevation and mean elevation  for subcells,  Units = m
    # =====================================================================
    mean_elevation = elevation[0, :, :]

    # extracting elevation for sub cells
    elevation_subgrid = elevation[1:, :, :]

    # Initializing elevation threshold to prevent excessive snow accumulation
    thresh_elev = np.zeros(snow_water_storage.shape)

    # =========================================================================
    #                       Looping through subgrids
    # =========================================================================
    for i in range(len(elevation_subgrid)):
        # =====================================================================
        # Check if  current_landarea_frac == 0 , then add previous storage to
        # daily_storage_tranfer. This storage will then  added to runoff.
        # (e.g. island)
        # =====================================================================

        dailystoragetransfer =\
            np.where(current_landarea_frac == 0, daily_storage_transfer +
                     snow_water_storage_subgrid[i], 0)
        # =====================================================================

        # Adapting  snow_water_storage_subgrid to dynamic land area fraction
        snow_water_storage_subgrid[i] *= landareafrac_ratio

        # Initial storage to calulate change in snow water storage.
        initial_storage = snow_water_storage_subgrid[i].copy()

        # =====================================================================
        # Calulating temperature (K) for the 100 subcells based on land surface
        # map elevation and a constant adiabatic lapse rate
        temp_elev = temperature - ((elevation_subgrid[i] - mean_elevation) *
                                   adiabatic_lapse_rate)

        # =================================================================
        #         Prevent excessive snow accumulation:
        # When snow storage reaches 1000 mm in a subcell in a previous
        # timestep, its elevation is used as a threshold for remaning upper
        # subcells (those in higher elevations).
        # New temperature is calulated for these remaning subcells so that
        # temperature doesn't decrease in these remaining subcells
        # =================================================================
        # Getting elevation threshold (thresh_elev) from subcell when snow
        # storage reaches 1000 mm in this subcell

        thresh_elev =  \
            np.where((snow_water_storage_subgrid[i] > 1000) &
                     (thresh_elev == 0),
                     elevation_subgrid[i], thresh_elev)

        # calculating new tempeture using elevation threshold.
        temp_elev = \
            np.where((snow_water_storage_subgrid[i] > 1000) &
                     (thresh_elev > 0),
                     temperature-((thresh_elev - mean_elevation)
                                  * adiabatic_lapse_rate), temp_elev)

        # =================================================================
        # Computing snow fall(mm) defined ass direct precipitation that
        # falls as snow and snow from through fall(mm)
        # =================================================================
        snow_fall_subgrid = \
            np.where(temp_elev <= snow_freeze_temp, precipitation, 0)

        snow_from_throughfall_subgrid = \
            np.where(temp_elev <= snow_freeze_temp, throughfall, 0)

        # =================================================================
        #  Compute sublimation (mm), and updating snow water storage (mm)
        #             Order of calculation is important!!!
        # =================================================================
        # Updating snow_water_subgrid  with snow_from_throughfall_subgrid
        # into a helper variable snow_water_storage_subgrid_new.
        snow_water_storage_subgrid_new = \
            snow_water_storage_subgrid[i] + snow_from_throughfall_subgrid

        # Sublimation is limited by snow storage.
        # Similar to EQ.14 in H. Müller Schmied et al 2021.
        sublimation_subgrid = \
            np.where(snow_water_storage_subgrid_new > pet_to_soil,
                     pet_to_soil, snow_water_storage_subgrid_new)

        # Sublimation only occurs when there is snow.
        sublimation_subgrid = np.where(temp_elev <= snow_freeze_temp,
                                       sublimation_subgrid, 0)

        # Updating snow_water_storage_subgrid_new after sublimation
        snow_water_storage_subgrid_new = \
            np.where(snow_water_storage_subgrid_new > pet_to_soil,
                     snow_water_storage_subgrid_new - pet_to_soil, 0)

        # When there is snow, snow_water_storage_subgrid becomes the updated
        # snow_water_storage_subgrid_new else it keeps it's initial values.
        snow_water_storage_subgrid[i] = \
            np.where(temp_elev <= snow_freeze_temp,
                     snow_water_storage_subgrid_new,
                     snow_water_storage_subgrid[i])

        # =================================================================
        # Compute snow melt (mm) and update snow water storage (mm)
        #               Order of calculation is important!!!
        # ==================================================================
        # snow_melt_subgrid_new is a helper variable to calulate actual
        # snow_melt_subgrid.
        # Also, no need to convert temperature to degrees since you are using
        # temperature difference with degreeday factor.
        snow_melt_subgrid_new = degreeday * (temp_elev - snow_melt_temp)

        # Making sure that snow_melt_subgrid_new is not greater than
        # snow_water_storage_subgrid.
        snow_melt_subgrid = \
            np.where(snow_melt_subgrid_new > snow_water_storage_subgrid[i],
                     snow_water_storage_subgrid[i], snow_melt_subgrid_new)

        # Melting only occurs when temp_elev > snow_melt_temp.
        snow_melt_subgrid = \
            np.where((temp_elev > snow_melt_temp) &
                     (snow_water_storage_subgrid[i] > 0),
                     snow_melt_subgrid, 0)

        # Updating snow_water_storage_subgrid_new after melting into a helper
        # variable snow_water_storage_subgrid_melt
        snow_water_storage_subgrid_melt = \
            np.where(snow_melt_subgrid_new > snow_water_storage_subgrid[i], 0,
                     snow_water_storage_subgrid[i] - snow_melt_subgrid_new)

        # When there is melt, snow_water_storage_subgrid becomes the updated
        # snow_water_storage_subgrid_melt else it keeps it's initial values.
        snow_water_storage_subgrid[i] = \
            np.where((temp_elev > snow_melt_temp) &
                     (snow_water_storage_subgrid[i] > 0),
                     snow_water_storage_subgrid_melt,
                     snow_water_storage_subgrid[i])

        # =================================================================
        #   compute effective precipitation based on elevation (mm/day).
        #  and change in snow water storage(mm)
        # ==================================================================
        # effective_precipitation is needed as input soil water balance.
        # Note!! np.where conditions computes throughfall minus snowfall
        effective_precipitation_elev =\
            np.where(temp_elev <= snow_freeze_temp, 0, throughfall) +\
            snow_melt_subgrid

        # computing change in snow_water_storage
        snow_water_storage_change = \
            snow_water_storage_subgrid[i] - initial_storage

        # land_storage_change_sum variable is the sum of all vertical water
        #  balance storage change (canopy, snow, soil)
        land_storage_change_sum += snow_water_storage_change

        # =================================================================
        #  Maximum Temperature based on elevation is used in soil actual
        # evapotransipration calculation.
        # ==================================================================
        # Maximum temperature is taking from the 1st(lowest) elevation
        if i == 0:
            max_temp_elev += temp_elev
        # Assign zero to storage if land area fraction is zero
        snow_water_storage_subgrid[i] = np.where(current_landarea_frac <= 0, 0,
                                                 snow_water_storage_subgrid[i])
        # =================================================================
        # Acuumulating subcells into output varaibles
        # =================================================================
        snow_water_storage += snow_water_storage_subgrid[i]
        snow_fall += snow_fall_subgrid
        sublimation += sublimation_subgrid
        snow_melt += snow_melt_subgrid
        effective_precipitation += effective_precipitation_elev

    # =================================================================
    # Aggretating subcells values to 0.5 degree cells.
    # =================================================================
    snow_water_storage = snow_water_storage / len(elevation_subgrid)
    snow_fall = snow_fall / len(elevation_subgrid)
    sublimation = sublimation / len(elevation_subgrid)
    snow_melt = snow_melt / len(elevation_subgrid)
    effective_precipitation = effective_precipitation / len(elevation_subgrid)
    dailystoragetransfer = dailystoragetransfer / len(elevation_subgrid)

    # =========================================================================
    # Assign zero to storage or flux, if land area fraction is zero
    # =========================================================================
    snow_water_storage = \
        np.where(current_landarea_frac <= 0, 0, snow_water_storage)

    snow_fall = np.where(current_landarea_frac <= 0, 0, snow_fall)
    sublimation = np.where(current_landarea_frac <= 0, 0, sublimation)
    snow_melt = np.where(current_landarea_frac <= 0, 0, snow_melt)
    effective_precipitation = \
        np.where(current_landarea_frac <= 0, 0, effective_precipitation)
    max_temp_elev = np.where(current_landarea_frac <= 0, 0, max_temp_elev)
    land_storage_change_sum = \
        np.where(current_landarea_frac <= 0, 0, land_storage_change_sum)

    return snow_water_storage, snow_water_storage_subgrid, snow_fall,\
        sublimation, snow_melt, effective_precipitation, max_temp_elev,\
        land_storage_change_sum, dailystoragetransfer


@njit(parallel=True, nogil=True, cache=True)
def subgrid_snow_balance_parallel(snow_water_storage_chunk,
                                  snow_water_storage_subgrid_chunk,
                                  temperature_chunk, precipitation_chunk,
                                  throughfall_chunk, pet_to_soil_chunk,
                                  land_storage_change_sum_chunk,
                                  degreeday_chunk, current_landarea_frac_chunk,
                                  landareafrac_ratio_chunk, elevation_chunk,
                                  daily_storage_transfer_chunk,
                                  adiabatic_lapse_rate_chunk,
                                  snow_freeze_temp_chunk,
                                  snow_melt_temp_chunk):
    """
    Compute snow water balance and related storages and fluxes in parallel.

    The default 360x720 degree cell is divided into desired chunks.
    Defualt is 20 along the rows thus 20 chunks of 18x720 cells. Return
    variables are also in same chunks size.

    Parameters
    ----------
    snow_water_storage_chunk : array
       Snow water storage, Units: mm
    snow_water_storage_subgrid_chunk : array
        Snow water storage divided into 100 subgrids based on GTOPO30 (U.S.
        Geological Survey, 1996) land surface elevation map, Units: mm
    temperature_chunk : array
        Daily temperature climate forcing, Units: K.
    precipitation_chunk : array
        Daily precipitation,  Units: mm/day
    throughfall_chunk : array
        Throughfall,  Units: mm/day
    pet_to_soil_chunk : array
        Remaining energy for addtional soil evaporation, Units: mm/day
    land_storage_change_sum_chunk : array
        Sum of change in vertical balance storages, Units: mm
    degreeday_chunk : array
        Land cover specific degreeday values based on [2]_ .Units: mm/day/C
    current_landarea_frac_chunk : array
        Land area fraction of current time step,  Units: (-)
    landareafrac_ratio_chunk : array
        Ratio of land area fraction of previous to current time step, Units:(-)
    elevation_chunk : array
        and surface elevation map based on GTOPO30 (U.S.
        Geological Survey, 1996) [1]_. Units: m
    daily_storage_transfer_chunk : array
        storage to be transfered to runoff when land area fraction of current
        time step is zero, Units: mm
    adiabatic_lapse_rate_chunk: array
        Adiabatic lapse rate , Units:  K/m or °C/m
    snow_freeze_temp_chunk: array
        Snow freeze temperature  , Units:  K
    snow_melt_temp_chunk: array
        Snow melt temperature  , Units:  K

    Returns
    -------
    snow_water_storage : array
        Updated snow water storage chunks, Units: mm
    snow_water_storage_subgrid : array
        Updated snow water storage subgrid chunks,  Units: mm
    snow_fall : array
        Snowfall chunks, Units: mm/day
    sublimation : array
        sublimation chunks, Units: mm/day
    snow_melt : array
        Snow melt chunks, Units: mm/day
    effective_precipitation : array
        Effective Precipitation chunks, Units: mm/day
    max_temp_elev : array
        Chunk of maximum temperature from the 1st(lowest) elevation, Units: K
    land_storage_change_sum : array
        Sum of change in vertical balance storages (chunks), Units: mm
    daily_storage_transfer : array
        Updated storage to be transfered to runoff when land area fraction
        of current time step is zero, Units: mm

    References.

    .. [1] U.S. Geological Survey: USGS EROS archive – digital elevation–
                global 30 arc-second elevation (GTOPO30), available at:
                https://www.usgs.gov/centers/eros/science/usgs-eros-archivedigital-elevation-global-30-arc-second-elevation-gtopo30?qtscience_center_objects=0#qt-science_center_objects
                (last access: 25 MArch 2020), 1996

    """
    # creating empty arrays to store output values from numba_snow function.
    snow_water_storage = np.zeros(snow_water_storage_chunk.shape)
    snow_water_storage_subgrid = \
        np.zeros(snow_water_storage_subgrid_chunk.shape)
    snow_fall = np.zeros(snow_water_storage_chunk.shape)
    sublimation = np.zeros(snow_water_storage_chunk.shape)
    snow_melt = np.zeros(snow_water_storage_chunk.shape)
    effective_precipitation = np.zeros(snow_water_storage_chunk.shape)
    max_temp_elev = np.zeros(snow_water_storage_chunk.shape)
    land_storage_change_sum = np.zeros(snow_water_storage_chunk.shape)
    daily_storage_transfer = np.zeros(snow_water_storage_chunk.shape)

    # Numba uses prange to automatically run loops in parallel.
    for i in prange(len(snow_water_storage_chunk)):

        results = \
            subgrid_snow_balance(snow_water_storage_chunk[i],
                                 snow_water_storage_subgrid_chunk[i],
                                 temperature_chunk[i], precipitation_chunk[i],
                                 throughfall_chunk[i], pet_to_soil_chunk[i],
                                 land_storage_change_sum_chunk[i],
                                 degreeday_chunk[i],
                                 current_landarea_frac_chunk[i],
                                 landareafrac_ratio_chunk[i],
                                 elevation_chunk[i],
                                 daily_storage_transfer_chunk[i],
                                 adiabatic_lapse_rate_chunk[i],
                                 snow_freeze_temp_chunk[i],
                                 snow_melt_temp_chunk[i])

        snow_water_storage[i] = results[0]
        snow_water_storage_subgrid[i] = results[1]
        snow_fall[i] = results[2]
        sublimation[i] = results[3]
        snow_melt[i] = results[4]
        effective_precipitation[i] = results[5]
        max_temp_elev[i] = results[6]
        land_storage_change_sum[i] = results[7]
        daily_storage_transfer[i] = results[8]

    return snow_water_storage, snow_water_storage_subgrid, snow_fall,\
        sublimation, snow_melt, effective_precipitation, max_temp_elev,\
        land_storage_change_sum, daily_storage_transfer
