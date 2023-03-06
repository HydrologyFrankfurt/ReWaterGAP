# -*- coding: utf-8 -*-

# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Snow Storage Class."""

# =============================================================================
# This module calls the numba optimised snow water balance function from the
# snow_subgrid module to compute snow water balnce including,
# snow water storage and related fluxes for all grid cells in parallel.
# Note!!!: Each grid is subdivided into 100 non localized subgrids that are
# assigned different land surface elevations according to GTOPO30
# (U.S. Geological Survey, 1996).
# Grid cells are split  into 'n' chunks across rows for parallel computations
# Default is 20 (18x720 cells).  Total 0.5 grid cell size is (360 x 720)
# =============================================================================

import numpy as np
from core.verticalwaterbalance import snow_subgrid as ss


class Snow():
    """Compute snow storage and related fluxes.

    Parameters
    ----------
    static_data : contains the following data
            elevation : array
                Land surface elevation map based on GTOPO30 (U.S.
                Geological Survey, 1996) [1]_. Units: [m]
            degreeday : array
                Land cover specific degreeday values based on [2]_ .
                Units: [mm/day/C]
    precipitation : array
        Daily precipitation.  Units: [mm/day]

        References.

        .. [1] U.S. Geological Survey: USGS EROS archive – digital elevation–
                    global 30 arc-second elevation (GTOPO30), available at:
                    https://www.usgs.gov/centers/eros/science/usgs-eros-archivedigital-elevation-global-30-arc-second-elevation-gtopo30?qtscience_center_objects=0#qt-science_center_objects
                    (last access: 25 MArch 2020), 1996

        .. [2] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                    Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                    Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                    Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                    The global water resources and use model WaterGAP v2.2d:
                    model description and evaluation. Geoscientific Model
                    Development, 14(2), 1037–1079.
                    https://doi.org/10.5194/gmd-14-1037-2021


    Methods
    -------
    cal_snow:
        Compute daily snow storage.

    """

    def __init__(self, static_data, precipitation):

        parameters_snow = static_data.canopy_snow_soil_parameters
        land_cover = static_data.land_cover

        self.degreeday = np.zeros(land_cover.shape) * np.nan
        for i in range(len(parameters_snow)):
            self.degreeday[land_cover[:, :] == parameters_snow.loc[i, 'Number']] = \
                parameters_snow.loc[i, 'degree-day']

        self.elevation = static_data.gtopo30_elevation

        self.precipitation = precipitation

    def snow_balance(self, current_landarea_frac, landareafrac_ratio,
                     temperature, throughfall, snow_water_storage, pet_to_soil,
                     land_storage_change_sum, snow_water_storage_subgrid,
                     daily_storage_transfer, adiabatic_lapse_rate,
                     snow_freeze_temp,
                     snow_melt_temp):
        """
        Compute daily snow storage.

        Parameters
        ----------
        current_landarea_frac : array
          Land area fraction of current time step.  Units: [-]
        landareafrac_ratio : array
           Ratio of land area fraction of previous to current time step.
           Units: [-]
        temperature : array
            Daily temperature climate forcing. Units: [K]
        throughfall : array
            Throughfall. Units: [mm/day]
        snow_water_storage : array
           Snow water storage. Units: [mm]
        pet_to_soil : array
            Remaining energy for addtional evaporation from soil. Units: [mm/day]
        land_storage_change_sum : array
                Sum of change in vertical balance storages. Units: [mm]
        snow_water_storage_subgrid : array
            Snow water storage divided into 100 subgrids based on GTOPO30 (U.S.
            Geological Survey, 1996) land surface elevation map. Units: [mm]
        daily_storage_transfer : array
            Storage to be transfered to runoff when land area fraction of
            current time step is zero. Units: [mm]
        adiabatic_lapse_rate: array
            Adiabatic lapse rate. Units:  [K/m] or [°C/m]
        snow_freeze_temp: array
            Snow freezing temperature. Units: [K]
        snow_melt_temp: array
            Snow melting temperature. Units: [K]

        Returns
        -------
        snow_water_storage : array
            Updated snow water storage. Units: [mm]
        snow_water_storage_subgrid : array
            Updated snow water storage divided into 100 subgrids. Unit: [-]
        snow_fall : array
            Snowfall. Units: [mm/day]
        sublimation : array
            Sublimation. Units: [mm/day]
        snow_melt : array
            Snow melt. Units: [mm/day]
        effective_precipitation : array
            Effective Precipitation. Units: [mm/day]
        max_temp_elev : array
            Maximum temperature from the first (lowest) elevation. Units: [K]
        land_storage_change_sum : array
            Sum of change in vertical balance storages. Units: [mm]
        daily_storage_transfer : array
            Updated storage to be transfered to runoff when land area fraction
            of current time step is zero. Units: [mm]
        """
        # Strip off self object for numba to perfom calulations
        elevation = self.elevation
        precipitation = self.precipitation
        degreeday = self.degreeday

        # =====================================================================
        #  Spliiting arrays into 'n' chunks across rows for parallel run
        #  Default is 20 (18x720 cells)
        # =====================================================================
        chunk = 20
        snow_water_storage_chunk =\
            np.asarray(np.split(snow_water_storage, chunk))

        snow_water_storage_subgrid_chunk = \
            np.asarray(np.split(snow_water_storage_subgrid, chunk, axis=1))

        temperature_chunk = np.asarray(np.split(temperature, chunk))

        precipitation_chunk = np.asarray(np.split(precipitation, chunk))

        throughfall_chunk = np.asarray(np.split(throughfall, chunk))

        pet_to_soil_chunk = np.asarray(np.split(pet_to_soil, chunk))

        land_storage_change_sum_chunk = \
            np.asarray(np.split(land_storage_change_sum, chunk))

        degreeday_chunk = np.asarray(np.split(degreeday, chunk))

        current_landarea_frac_chunk = \
            np.asarray(np.split(current_landarea_frac, chunk))
        landareafrac_ratio_chunk = \
            np.asarray(np.split(landareafrac_ratio, chunk))

        elevation_chunk = np.asarray(np.split(elevation, chunk, axis=1))

        daily_storage_transfer_chunk = \
            np.asarray(np.split(daily_storage_transfer, chunk))

        adiabatic_lapse_rate_chunk = \
            np.asarray(np.split(adiabatic_lapse_rate, chunk))

        snow_freeze_temp_chunk = np.asarray(np.split(snow_freeze_temp, chunk))

        snow_melt_temp_chunk = np.asarray(np.split(snow_melt_temp, chunk))
        # =====================================================================
        #         Running numba snow water balance function
        # =====================================================================
        snow_output = \
            ss.subgrid_snow_balance_parallel(snow_water_storage_chunk,
                                             snow_water_storage_subgrid_chunk,
                                             temperature_chunk,
                                             precipitation_chunk,
                                             throughfall_chunk,
                                             pet_to_soil_chunk,
                                             land_storage_change_sum_chunk,
                                             degreeday_chunk,
                                             current_landarea_frac_chunk,
                                             landareafrac_ratio_chunk,
                                             elevation_chunk,
                                             daily_storage_transfer_chunk,
                                             adiabatic_lapse_rate_chunk,
                                             snow_freeze_temp_chunk,
                                             snow_melt_temp_chunk)

        # =====================================================================
        #         conbining chunks into original dimension
        # =====================================================================
        snow_water_storage = np.vstack(snow_output[0])
        snow_water_storage_subgrid = np.concatenate(snow_output[1], axis=1)
        snow_fall = np.vstack(snow_output[2])
        sublimation = np.vstack(snow_output[3])
        snow_melt = np.vstack(snow_output[4])
        effective_precipitation = np.vstack(snow_output[5])
        max_temp_elev = np.vstack(snow_output[6])
        land_storage_change_sum = np.vstack(snow_output[7])
        daily_storage_transfer = np.vstack(snow_output[8])

        return snow_water_storage, snow_water_storage_subgrid, snow_fall,\
            sublimation, snow_melt, effective_precipitation, max_temp_elev,\
            land_storage_change_sum, daily_storage_transfer
