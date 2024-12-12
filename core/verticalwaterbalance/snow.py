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
# runtime speed of the snow water storage funtion
# =============================================================================

import numpy as np
from numba import njit

# @njit is a decorator from numba to optimised the python code for speed.


@njit(cache=True)
def subgrid_snow_balance(snow_water_storage, snow_water_storage_subgrid,
                         temperature, precipitation, throughfall, pet_to_soil,
                         land_storage_change_sum, degreeday,
                         current_landarea_frac, landareafrac_ratio,
                         elevation, daily_storage_transfer,
                         adiabatic_lapse_rate,  snow_freeze_temp,
                         snow_melt_temp, minstorage_volume, x, y):
    """
    Compute snow water balance for subgrids including snow water storage and
    water flows entering and leaving the snow storage

    Parameters
    ----------
    snow_water_storage :float
        Snow water storage, Units: [mm]
    snow_water_storage_subgrid : array
        Snow water storage divided into 100 subgrids based on GTOPO30 (U.S.
        Geological Survey, 1996) land surface elevation map, Units: [mm]
    temperature :float
        Daily temperature climate forcing, Units: [K]
    precipitation :float
        Daily precipitation,  Units: [mm/day]
    throughfall :float
       Throughfall,  Units: [mm/day]
    pet_to_soil :float
        Remaining energy for addtional soil evaporation, Units: [mm/day]
    land_storage_change_sum :float
        Sum of change in vertical balance storages, Units: [mm]
    degreeday :float
        Land cover specific degreeday values based on [1]_ .Units: [mm/day/C]
    current_landarea_frac :float
      Land area fraction of current time step,  Units: [-]
    landareafrac_ratio :float
       Ratio of land area fraction of previous to current time step, Units: [-]
    elevation :array
        and surface elevation map based on GTOPO30 (U.S.
        Geological Survey, 1996) [1]_. Units: [m]
    daily_storage_transfer :float
        Storage to be transfered to runoff when land area fraction of current
        time step is zero, Units: [mm]
    adiabatic_lapse_rate:float
        Adiabatic lapse rate , Units:  [K/m or °C/m]
    snow_freeze_temp:float
        Snow freeze temperature  , Units:  [K]
    snow_melt_temp:float
        Snow melt temperature  , Units:  [K]
    minstorage_volume: float
        Volume at which storage is set to zero, units: [km3]
    x, y : Latititude and longitude indexes of grid cells.


    Returns
    -------
    snow_water_storage :float
        Updated snow water storage, Units: [mm]
    snow_water_storage_subgrid :array
        Updated snow water storage divided into 100 subgrids based on GTOPO30
        (U.S. Geological Survey, 1996) land surface elevation map, Units: mm
    snow_fall :float
        Snowfall, Units: [mm/day]
    sublimation :float
        Sublimation, Units: [mm/day]
    snow_melt :float
        Snow melt, Units: [mm/day]
    effective_precipitation :float
        Effective Precipitation, Units: [mm/day]
    max_temp_elev :float
        Maximum temperature from the 1st(lowest) elevation, Units: [K]
    land_storage_change_sum :float
       Sum of change in vertical balance storages, Units: [mm]
    daily_storage_transfer :float
       Updated storage to be transfered to runoff when land area fraction
       of current time step is zero, Units: [mm]
    snowcover_frac: float
        Snow cover fraction

    References.

    .. [1] U.S. Geological Survey: USGS EROS archive – digital elevation–
                global 30 arc-second elevation (GTOPO30), available at:
                https://www.usgs.gov/centers/eros/science/usgs-eros-archivedigital-elevation-global-30-arc-second-elevation-gtopo30?qtscience_center_objects=0#qt-science_center_objects
                (last access: 25 MArch 2020), 1996

    """
    # Index (x, y) to  print out varibales of interest
    # e.g.  if x==65 and y==137: print(mean_elevation)

    # =====================================================================
    # Extracting elevation and mean elevation  for subcells,  Units = m
    # =====================================================================
    mean_elevation = elevation[0]

    # extracting elevation for sub cells
    elevation_subgrid = elevation[1:]

    # Initializing elevation threshold to prevent excessive snow accumulation
    thresh_elev = 0.0

    # =====================================================================
    # Creating subgrid variable
    # =====================================================================
    sublimation_subgrid = np.zeros(elevation_subgrid.shape)
    snow_from_throughfall_subgrid = np.zeros(elevation_subgrid.shape)
    snow_fall_subgrid = np.zeros(elevation_subgrid.shape)
    throughfall_before_melt = np.zeros(elevation_subgrid.shape)
    snow_melt_subgrid = np.zeros(elevation_subgrid.shape)
    snowcover_frac_subgrid = np.zeros(elevation_subgrid.shape)
    # =====================================================================
    # Calulating temperature (K) for the 100 subcells based on land surface
    # map elevation and a constant adiabatic lapse rate
    temp_elev = temperature - ((elevation_subgrid - mean_elevation) *
                               adiabatic_lapse_rate)

    if current_landarea_frac > 0:
        # Adapting snow_water_storage_subgrid to dynamic land area fraction
        snow_water_storage_subgrid *= landareafrac_ratio

        # minimal storage volume =1e15 (smaller volumes set to zero)
        # to counter numerical inaccuracies
        mask_zero = np.abs(snow_water_storage_subgrid) <= minstorage_volume
        snow_water_storage_subgrid[mask_zero] = 0

        # Initial storage to calulate change in snow water storage.
        # copy works in numba since snow_water_storage_subgrid is numpys array
        # without initial storage is chnaged when snow_water_storage_subgrid changes 
        initial_storage = snow_water_storage_subgrid.copy()

        for i in range(len(elevation_subgrid)):
            # =================================================================
            #         Prevent excessive snow accumulation:
            # When snow storage reaches 1000 mm in a subcell in a previous
            # timestep, its elevation is used as a threshold for remaning upper
            # subcells (those in higher elevations).
            # New temperature is calulated for these remaning subcells so that
            # temperature doesn't decrease in these remaining subcells
            # This should prevent uncontrolled snow accumulation.
            # =================================================================
            # Getting elevation threshold (thresh_elev) from subcell when snow
            # storage reaches 1000 mm in this subcell

            if snow_water_storage_subgrid[i] > 1000:
                if thresh_elev == 0.0:
                    thresh_elev = elevation_subgrid[i]
                elif thresh_elev > 0:
                    temp_elev[i] = \
                        temperature - ((thresh_elev - mean_elevation) *
                                       adiabatic_lapse_rate)

            if temp_elev[i] <= snow_freeze_temp:
                # Computing snow fall(mm) [defined as direct precipitation that
                # falls as snow] and snow from through fall(mm)
                snow_fall_subgrid[i] = precipitation
                snow_from_throughfall_subgrid[i] = throughfall
                throughfall_before_melt[i] = 0

                #  Compute sublimation (mm), and updating snow water storage
                snow_water_storage_subgrid[i] += \
                    snow_from_throughfall_subgrid[i]

                # Sublimation is limited by snow storage.
                # Similar to EQ.14 in H. Müller Schmied et al 2021.
                if snow_water_storage_subgrid[i] > pet_to_soil:
                    sublimation_subgrid[i] = pet_to_soil
                    snow_water_storage_subgrid[i] -= pet_to_soil
                else:
                    sublimation_subgrid[i] = snow_water_storage_subgrid[i]
                    snow_water_storage_subgrid[i] = 0
            else:
                throughfall_before_melt[i] = throughfall

            # Compute snow melt (mm) and update snow water storage (mm)
            if temp_elev[i] > snow_melt_temp:
                if snow_water_storage_subgrid[i] > 0:
                    snow_melt_subgrid[i] = \
                        degreeday * (temp_elev[i] - snow_melt_temp)
                    if snow_melt_subgrid[i] > snow_water_storage_subgrid[i]:
                        snow_melt_subgrid[i] = snow_water_storage_subgrid[i]
                        snow_water_storage_subgrid[i] = 0
                    else:
                        snow_water_storage_subgrid[i] -= snow_melt_subgrid[i]

            # =================================================================
            #  Maximum Temperature based on elevation is used in soil actual
            # evapotransipration calculation.
            # ==================================================================
            # Maximum temperature is taking from the 1st(lowest) elevation
            if i == 0:
                max_temp_elev = temp_elev[i]

        # =====================================================================
        #  Compute snow cover fraction
        # =====================================================================
        snowcover_frac_subgrid = np.where(snow_water_storage_subgrid > 0, 1, 0)

        # =================================================================
        #  Compute effective precipitation based on elevation (mm/day).
        #  and change in snow water storage(mm)
        # ==================================================================
        # effective_precipitation is needed as input soil water balance.

        effective_precipitation_elev = \
            snow_melt_subgrid + throughfall_before_melt

        # computing change in snow_water_storage
        snow_water_storage_change = \
            snow_water_storage_subgrid - initial_storage

        # =================================================================
        # Aggretating subcells values to 0.5 degree cells.
        # =================================================================
        # land_storage_change_sum variable is the sum of all vertical water
        #  balance storage change (canopy, snow, soil)
        land_storage_change_sum += (np.sum(snow_water_storage_change) /
                                    len(elevation_subgrid))

        snow_water_storage = \
            (np.sum(snow_water_storage_subgrid) / len(elevation_subgrid))
        snow_fall = (np.sum(snow_fall_subgrid) / len(elevation_subgrid))
        sublimation = (np.sum(sublimation_subgrid) / len(elevation_subgrid))
        snow_melt = (np.sum(snow_melt_subgrid) / len(elevation_subgrid))
        effective_precipitation = \
            (np.sum(effective_precipitation_elev) / len(elevation_subgrid))

        snowcover_frac = \
            (np.sum(snowcover_frac_subgrid) / len(elevation_subgrid))
    else:
        # =================================================================
        # Check if  current_landarea_frac == 0 , then add previous storage
        # to daily_storage_tranfer. This storage will then  added to runoff
        # (e.g. island)
        # =================================================================
        daily_storage_transfer += \
            (np.sum(snow_water_storage_subgrid) / len(elevation_subgrid))
        snow_water_storage_subgrid[:] = 0
        snow_water_storage = 0

    return snow_water_storage, snow_water_storage_subgrid, snow_fall, \
        sublimation, snow_melt, effective_precipitation, max_temp_elev,\
        land_storage_change_sum,  daily_storage_transfer, snowcover_frac
