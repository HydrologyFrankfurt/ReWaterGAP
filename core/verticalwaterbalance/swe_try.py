# -*- coding: utf-8 -*-
"""Snow Storage Function."""

import numpy as np


def snow(snow_water_storage, temperature, precipitation, throughfall,
         PET_to_soil, static_data, snow_water_storage_subgrid, thresh_elev,
         landAreaFrac):
    """
    Calulcate snow storage and fluxes.

    Parameters
    ----------
    snow_water_storage : TYPE
        DESCRIPTION.
    temperature : TYPE
        DESCRIPTION.
    precipitation : TYPE
        DESCRIPTION.
    throughfall : TYPE
        DESCRIPTION.
    PET_to_soil : TYPE
        DESCRIPTION.
    static_data : TYPE
        DESCRIPTION.
    snow_water_storage_subgrid : TYPE
        DESCRIPTION.

    Returns
    -------
    snow_water_storage : TYPE
        DESCRIPTION.
    snow_fall : TYPE
        DESCRIPTION.
    snow_melt : TYPE
        DESCRIPTION.
    sublimation : TYPE
        DESCRIPTION.
    snow_water_storage_subgrid : TYPE
        DESCRIPTION.

    """
    elevation = static_data.GTOPO30_elevation
    elevation = elevation.elevrange.values

    parameters = static_data.canopy_model_parameters
    land_cover = static_data.land_cover.landcover[0].values

    Degreeday = np.zeros(temperature.shape) * np.nan
    for i in range(len(parameters)):
        Degreeday[land_cover[:, :] == parameters.loc[i, 'Number']] = \
            parameters.loc[i, 'degree-day']

    # =========================================================================
    # coverting precipitation to mm/day
    # =======================================================================
    to_mm_per_day = 86400
    precipitation = precipitation * to_mm_per_day

    # =========================================================================
    # constants
    # =========================================================================
    adiabatic_lapse_rate = (0.6/100)  # K/100m or °C/m
    snow_freeze_temp = 273.15
    snow_melt_temp = 273.15

    # =========================================================================
    # variables
    # =========================================================================
    snow_fall = 0
    snow_melt = 0
    sublimation = 0

    for i in range(elevation.shape[0]-1):
        # =====================================================================
        # Definition of subgrid variables
        # =====================================================================
        snow_fall_subgrid = 0
        snow_from_throughfall_subgrid = 0
        snow_melt_subgrid = 0

        # main calculation
        temp_elev = temperature - ((elevation[i+1, :, :] -
                                    elevation[0, :, :]) *
                                   adiabatic_lapse_rate)

        # =====================================================================
        # correcting snow water storage for land area fraction
        # =====================================================================
        snow_water_storage_subgrid[i, :, :] =  \
            snow_water_storage_subgrid[i, :, :] * landAreaFrac

        # =====================================================================
        #         # Threshold elevation condition
        # =====================================================================
        condition =\
            (snow_water_storage_subgrid[i, :, :] > 1000) & (thresh_elev > 0)

        temp_elev = np.where(condition,
                             temperature-((thresh_elev -
                                           elevation[0, :, :]) *
                                          adiabatic_lapse_rate),
                             temp_elev)

        condition =\
            (snow_water_storage_subgrid[i, :, :] > 1000) & (thresh_elev == 0)

        thresh_elev = np.where(condition, elevation[i+1, :, :],  thresh_elev)

        # =====================================================================
        #          Direct precipitation that falls as snow  (Snow fall)
        # =====================================================================
        snow_fall_subgrid = np.where(temp_elev <= snow_freeze_temp,
                                     precipitation, 0)

        snow_from_throughfall_subgrid = np.where(temp_elev <= snow_freeze_temp,
                                                 throughfall, 0)

        # snow_water storage

        # =====================================================================
        #                           Sublimation
        # =====================================================================
        snow_water_storage_subgrid_new = \
            snow_water_storage_subgrid[i, :, :] + snow_from_throughfall_subgrid

        sublimation_subgrid = \
            np.where(snow_water_storage_subgrid_new > PET_to_soil,
                     PET_to_soil, snow_water_storage_subgrid_new)

        sublimation_subgrid = np.where(temp_elev <= snow_freeze_temp,
                                       0, sublimation_subgrid)

        # snow_water storage

        snow_water_storage_subgrid_new = \
            np.where(snow_water_storage_subgrid_new > PET_to_soil,
                     snow_water_storage_subgrid_new - PET_to_soil, 0)

        snow_water_storage_subgrid[i, :, :] = \
            np.where(temp_elev <= snow_freeze_temp,
                     snow_water_storage_subgrid_new,
                     snow_water_storage_subgrid[i, :, :])
        # =====================================================================
        # Melt
        # =====================================================================
        snow_melt_subgrid = Degreeday * (temp_elev - snow_melt_temp)

        snow_water_storage_subgrid_new = \
            np.where(snow_melt_subgrid > snow_water_storage_subgrid[i, :, :],
                     0, snow_water_storage_subgrid[i, :, :] -
                     snow_melt_subgrid)
        snow_water_storage_subgrid_new = \
            np.where(snow_water_storage_subgrid[i, :, :] > 0,
                     snow_water_storage_subgrid_new,
                     snow_water_storage_subgrid[i, :, :])

        snow_melt_subgrid = \
            np.where(snow_melt_subgrid > snow_water_storage_subgrid[i, :, :],
                     snow_water_storage_subgrid[i, :, :], snow_melt_subgrid)
        snow_melt_subgrid = \
            np.where(snow_water_storage_subgrid[i, :, :] > 0,
                     snow_melt_subgrid, 0)

        snow_melt_subgrid = \
            np.where(temp_elev > snow_melt_temp, snow_melt_subgrid, 0)

        snow_water_storage_subgrid[i, :, :] = \
            np.where(temp_elev > snow_melt_temp,
                     snow_water_storage_subgrid_new,
                     snow_water_storage_subgrid[i, :, :])

        # =====================================================================
        # Land fraction condition
        # =====================================================================
        snow_water_storage = np.where(landAreaFrac <= 0, 0, snow_water_storage)
        snow_water_storage_subgrid[i, :, :] = \
            np.where(landAreaFrac <= 0, 0, snow_water_storage_subgrid[i, :, :])

        # sumup
        snow_water_storage += snow_water_storage_subgrid[i, :, :]
        snow_melt += snow_melt_subgrid
        sublimation += sublimation_subgrid
        snow_fall += snow_fall_subgrid
    snow_water_storage = snow_water_storage / 100
    sublimation = sublimation / 100
    snow_melt = snow_melt / 100
    snow_fall = snow_fall / 100

    return snow_water_storage, snow_fall, snow_melt, sublimation,\
        snow_water_storage_subgrid, thresh_elev
