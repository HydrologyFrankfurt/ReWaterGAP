# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Vertical water balance coordinator."""

# =============================================================================
# This module brings all vertical water balance functions together to run
# =============================================================================

import numpy as np
from core.verticalwaterbalance import radiation_evapotranspiration as rad_pet
from core.verticalwaterbalance import leafareaindex
from core.verticalwaterbalance import canopy
from core.verticalwaterbalance import snow
from core.verticalwaterbalance import soil


class VerticalWaterBalance:
    """Computes vertical waterbalance."""

    # Getting all storages and fluxes in this dictionary container
    fluxes = {}
    storages = {}

    def __init__(self, forcings_static):
        self.forcings_static = forcings_static

        # =====================================================================
        #               State variables for:
        #  1. leaf area index Units : (-)
        # =====================================================================
        # Note!!! "get_daily_leaf_area_index" also takes additional input
        # which are defined below.

        # Days since start of leaf area index profile(counter for days with
        # growing conditions), units: day
        self.days = np.zeros((self.forcings_static.lat_length,
                              self.forcings_static.lon_length))

        # Variable Name: cumulative precipitation,  units: mm/day
        self.cum_precipitation = np.zeros((self.forcings_static.lat_length,
                                           self.forcings_static.lon_length))

        # Growth status per grid cell shows whether a specific land cover
        # is (not) growing (value=0) or fully grown (value=1).
        # Initially all landcovers are not growing
        self.growth_status = np.zeros((self.forcings_static.lat_length,
                                       self.forcings_static.lon_length))

        # =====================================================================
        #         # 2. canopy storage,  Units : mm
        # =====================================================================
        self.canopy_storage = np.zeros((self.forcings_static.lat_length,
                                        self.forcings_static.lon_length))

        # =====================================================================
        #         3. snow water storage,  Units : mm
        # =====================================================================
        self.snow_water_storage = np.zeros((self.forcings_static.lat_length,
                                            self.forcings_static.lon_length))
        # Getting size of elevation data to create subgrid array for snow
        # water storage
        elev_size = \
            self.forcings_static.static_data.gtopo30_elevation[1:].shape

        # Snow water storage divided into 100 subgrids based on GTOPO30 (U.S.
        # Geological Survey, 1996) land surface elevation map, Units: mm
        self.snow_water_storage_subgrid = np.zeros(elev_size)

        # =====================================================================
        #         4. soil water storage,  Units : mm
        # =====================================================================
        self.soil_water_content = np.zeros((self.forcings_static.lat_length,
                                            self.forcings_static.lon_length))

    def calculate(self, date):
        """
        Calculate vertical waterbalance.

        Parameters
        ----------
        time_step : int
            Daily timestep.
        date : numpy.datetime64
            Timestamp or date of a daily simulation.

        Returns
        -------
        None.

        """
        # =================================================================
        # Computes daily radiation compononents and Priestley-Taylor PET
        # ,  Units : mm/day
        # =================================================================
        # Initialises daily radiation components for PET calcultion
        # All daily radiation componnents can be also wriitten out
        radiation_for_potevap = rad_pet.\
            RadiationPotentialEvap(self.forcings_static.climate_forcing,
                                   self.forcings_static.static_data, date,
                                   self.snow_water_storage)

        # Computes Priestley-Taylor PET from radiation components directly.
        # Ouput from priestley_taylor() is 0 = daily PET values and
        # 1= openwater PET values.

        potential_evap = radiation_for_potevap.priestley_taylor()
        daily_potential_evap = potential_evap[0]
        openwater_potential_evap = potential_evap[1]

        # =================================================================
        # Compute daily leaf area index ,  Units : (-)
        # =================================================================

        # Initialises leaf area index data for computing  leaf area index
        # in parallel
        initialize_leaf_area_index = leafareaindex.\
            LeafAreaIndex(self.forcings_static.climate_forcing,
                          self.forcings_static.static_data, date)

        daily_leaf_area_index = initialize_leaf_area_index.\
            get_daily_leaf_area_index(self.days, self.growth_status,
                                      self.cum_precipitation)

        # ouputs from the get_daily_leaf_area_index" are
        # 0 = daily leaf area index, 1 = days since start,
        # 2 = cumulative precipitation  and 3 = growth status
        # ouput(1-3)  get updated per time step.
        leaf_area_index = daily_leaf_area_index[0]
        self.days = daily_leaf_area_index[1]
        self.cum_precipitation = daily_leaf_area_index[2]
        self.growth_status = daily_leaf_area_index[3]

        # ====================================================================
        #  Forcing required for storage and flux caluation specipically canopy
        #  and snow
        # =====================================================================
        precipitation = self.forcings_static.climate_forcing.\
            precipitation.sel(time=str(date))
        # coverting precipitation to mm/day
        to_mm_per_day = 86400
        precipitation = precipitation.pr.values * to_mm_per_day

        temperature = self.forcings_static.climate_forcing.\
            temperature.sel(time=str(date))
        temperature = temperature.tas.values

        # =====================================================================
        # Compute canopy storage,  Units : mm
        # =====================================================================
        daily_canopy_storage = canopy.\
            canopy_balance(self.canopy_storage,
                           leaf_area_index,
                           daily_potential_evap, precipitation,
                           self.forcings_static.updated_landareafrac)

        # # ouputs from the  daily_canopy_storage are
        # # 0 = canopy_storage, 1 = throughfall,
        # # 2 = canopy_evap , 3 = pet_to_soil, 4 = land_storage_change_sum

        self.canopy_storage = daily_canopy_storage[0]
        throughfall = daily_canopy_storage[1]
        canopy_evap = daily_canopy_storage[2]
        pet_to_soil = daily_canopy_storage[3]
        land_storage_change_sum = daily_canopy_storage[4]

        # =====================================================================
        # Compute snow storage,  Units : mm
        # =====================================================================
        initialize_snow_storage = \
            snow.Snow(self.forcings_static.static_data, precipitation)

        daily_snow_storage = initialize_snow_storage.\
            snow_balance(self.forcings_static.updated_landareafrac,
                         temperature, throughfall, self.snow_water_storage,
                         pet_to_soil, land_storage_change_sum,
                         self.snow_water_storage_subgrid)

        # ouputs from the  daily_snow_storage  are
        # 0 = snow_water_storage,  1 = snow_water_storage_subgrid,
        # 2 = snow_fall, 3 = sublimation, 4 = snow_melt,
        # 5 = effective_precipitation, 6 = max_temp_elev,
        # 7 = land_storage_change_sum

        self.snow_water_storage = daily_snow_storage[0]
        self.snow_water_storage_subgrid = daily_snow_storage[1]
        snow_fall = daily_snow_storage[2]
        sublimation = daily_snow_storage[3]
        snow_melt = daily_snow_storage[4]
        effective_precipitation = daily_snow_storage[5]
        max_temp_elev = daily_snow_storage[6]
        land_storage_change_sum = daily_snow_storage[7]

        # =====================================================================
        # Compute soil storage, Units : mm
        # =====================================================================
        initilaize_soil_storage = \
            soil.Soil(self.forcings_static.static_data)

        # Modified effective precipitation and immediate runoff
        modified_effective_precipitation = \
            initilaize_soil_storage.immediate_runoff(effective_precipitation)

        # ouputs from the  modified_effective_precipitation are
        # 0 = effective_precipitation,  1 =  immediate_runoff
        effective_precipitation_corr = modified_effective_precipitation[0]
        immediate_runoff = modified_effective_precipitation[1]

        # Running daily soil storage.
        daily_soil_storage = initilaize_soil_storage.\
            soil_balance(self.soil_water_content, pet_to_soil,
                         self.forcings_static.updated_landareafrac,
                         max_temp_elev, canopy_evap,
                         effective_precipitation_corr, precipitation,
                         immediate_runoff, land_storage_change_sum,
                         sublimation)

        # ouputs from the  daily_soil_storage  are
        # 0 = soil_water_content,  1 = groundwater_recharge_from_soil_mm,
        # 2 = actual_soil_evap, 3 =  soil_saturation,
        # 4 = surface_runoff

        self.soil_water_content = daily_soil_storage[0]
        groundwater_recharge_from_soil_mm = daily_soil_storage[1]
        surface_runoff = daily_soil_storage[4]
        # =====================================================================
        # Getting all storages
        # =====================================================================
        VerticalWaterBalance.storages.\
            update({'canopystor': self.canopy_storage,
                    'swe': self.snow_water_storage,
                    'soilmoist':  self.soil_water_content})

        # =====================================================================
        # Getting all fluxes
        # =====================================================================

        VerticalWaterBalance.fluxes.\
            update({'netrad': radiation_for_potevap.net_radiation,
                    'potevap': daily_potential_evap,
                    'lai': leaf_area_index,
                    'canopy_evap': canopy_evap,
                    'throughfall': throughfall,
                    'snow_fall': snow_fall,
                    'snow_melt': snow_melt,
                    'snow_evap': sublimation,
                    'groundwater_recharge': groundwater_recharge_from_soil_mm,
                    'surface_runoff': surface_runoff,
                    'openwater_PET': openwater_potential_evap,
                    'daily_precipitation': precipitation})

    def get_storages_and_fluxes(self):
        """
        Get daily storages and fluxes for vertical waterbalance.

        Returns
        -------
        dict
            Dictionary of all storages.
        dict
           Dictionary of all fluxes.

        """
        return VerticalWaterBalance.storages, VerticalWaterBalance.fluxes
