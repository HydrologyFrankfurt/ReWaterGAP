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
from core.utility import units_conveter_check_neg_precip as check_or_convert
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

    def __init__(self, forcings_static, parameters):
        self.forcings_static = forcings_static
        self.cont_frac = forcings_static.static_data.\
            land_surface_water_fraction.contfrac.values.astype(np.float64)/100
        self.parameters = parameters
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
        self.canopy_storage = \
            np.zeros((self.forcings_static.lat_length,
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

    def calculate(self, date, current_landarea_frac, landareafrac_ratio):
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
        # =====================================================================
        # Select daily climate forcing and convert units (only precipitation
        #  and tempearture)
        # =====================================================================
        #                  =========================
        #                  ||     Precipitation   ||
        #                  =========================
        #  Actual name: Precipitation
        precipitation = self.forcings_static.climate_forcing.precipitation.sel(
            time=str(date))

        #  Checking negative precipittaion
        check_or_convert.check_neg_precipitation(precipitation.pr)

        # Covert precipitation units to mm/day
        precipitation = check_or_convert.to_mm_per_day(precipitation.pr)

        #                  =========================
        #                  ||     Air tempeature  ||
        #                  =========================
        #  Actual name: Air tempeature
        temperature = self.forcings_static.climate_forcing.temperature.sel(
            time=str(date))

        # Covert air tempeature to Kelvin
        temperature = check_or_convert.to_kelvin(temperature.tas)

        #                  ==================================
        #                  || Downward shortwave radiation ||
        #                  ==================================
        #  Actual name: Downward shortwave radiation  Units: Wm−2
        down_shortwave_radiation = \
            self.forcings_static.climate_forcing.down_shortwave_radiation.sel(
                time=str(date))
        down_shortwave_radiation = \
            down_shortwave_radiation.rsds.values.astype(np.float64)

        #                  ==================================
        #                  ||  Downward longwave radiation ||
        #                  ==================================
        #  Actual name: Downward longwave radiation  Units: Wm−2
        down_longwave_radiation = \
            self.forcings_static.climate_forcing.down_longwave_radiation.sel(
                time=str(date))
        down_longwave_radiation = \
            down_longwave_radiation.rlds.values.astype(np.float64)

        # =================================================================
        #       Radiation compononents and Priestley-Taylor PET
        # =================================================================
        # Initialising daily radiation components for PET calcultion
        # All daily radiation componnents can be also wriitten out
        radiation_for_potevap = rad_pet.\
            RadiationPotentialEvap(temperature, down_shortwave_radiation,
                                   down_longwave_radiation,
                                   self.forcings_static.static_data,
                                   self.snow_water_storage,
                                   self.parameters)

        # Computes Priestley-Taylor PET from radiation components directly.
        # Output from priestley_taylor() is 0 = daily PET  (mm/day) and
        # 1= openwater PET (mm/day).
        potential_evap = radiation_for_potevap.priestley_taylor()
        daily_potential_evap = potential_evap[0]
        openwater_potential_evap = potential_evap[1]

        # =================================================================
        #               	 Daily leaf area index
        # =================================================================
        # Initialising leaf area index data for computing  leaf area index
        # in parallel
        initialize_leaf_area_index = leafareaindex.\
            LeafAreaIndex(temperature, precipitation,
                          self.forcings_static.static_data)

        daily_leaf_area_index = initialize_leaf_area_index.\
            get_daily_leaf_area_index(self.days, self.growth_status,
                                      self.cum_precipitation)

        # ouputs from the get_daily_leaf_area_index" are
        # 0 = daily leaf area index (-), 1 = days since start (days),
        # 2 = cumulative precipitation (mm/day)  and 3 = growth status(-)
        # ouput(1-3)  get updated per time step.

        leaf_area_index = daily_leaf_area_index[0]
        self.days = daily_leaf_area_index[1]
        self.cum_precipitation = daily_leaf_area_index[2]
        self.growth_status = daily_leaf_area_index[3]

        # =====================================================================
        #               Canopy Water Balance
        # =====================================================================
        daily_canopy_storage = canopy.\
            canopy_balance(self.canopy_storage,
                           leaf_area_index,
                           daily_potential_evap, precipitation,
                           current_landarea_frac, landareafrac_ratio,
                           self.parameters.max_storage_coefficient)

        # ouputs from the  daily_canopy_storage are
        # 0 = canopy_storage (mm), 1 = throughfall (mm/day),
        # 2 = canopy_evap (mm/day) , 3 = pet_to_soil (mm/day),
        # 4 = land_storage_change_sum (mm)
        # 5 = daily_storage_tranfer (mm/day)

        self.canopy_storage = daily_canopy_storage[0]
        throughfall = daily_canopy_storage[1]
        canopy_evap = daily_canopy_storage[2]
        pet_to_soil = daily_canopy_storage[3]
        land_storage_change_sum = daily_canopy_storage[4]
        daily_storage_transfer = daily_canopy_storage[5]

        # =====================================================================
        #               Snow Water Balance
        # =====================================================================
        initialize_snow_storage = \
            snow.Snow(self.forcings_static.static_data, precipitation)

        daily_snow_storage = initialize_snow_storage.\
            snow_balance(current_landarea_frac, landareafrac_ratio,
                         temperature, throughfall, self.snow_water_storage,
                         pet_to_soil, land_storage_change_sum,
                         self.snow_water_storage_subgrid,
                         daily_storage_transfer,
                         self.parameters.adiabatic_lapse_rate,
                         self.parameters.snow_freeze_temp,
                         self.parameters.snow_melt_temp)

        # ouputs from the  daily_snow_storage  are
        # 0 = snow_water_storage (mm), 1 = snow_water_storage_subgrid (mm),
        # 2 = snow_fall (mm/day), 3 = sublimation (mm/day),
        # 4 = snow_melt (mm/day)
        # 5 = effective_precipitation (mm/day), 6 = max_elev_temp(K),
        # 7 = land_storage_change_sum (mm),  8 = daily_storage_tranfer (mm/day)

        self.snow_water_storage = daily_snow_storage[0]
        self.snow_water_storage_subgrid = daily_snow_storage[1]
        snow_fall = daily_snow_storage[2]
        sublimation = daily_snow_storage[3]
        snow_melt = daily_snow_storage[4]
        effective_precipitation = daily_snow_storage[5]
        max_temp_elev = daily_snow_storage[6]
        land_storage_change_sum = daily_snow_storage[7]
        daily_storage_transfer = daily_snow_storage[8]

        # =====================================================================
        #                       Soil Water Balance
        # =====================================================================
        initilaize_soil_storage = \
            soil.Soil(self.forcings_static.static_data, self.parameters)

        # Modified effective precipitation and immediate runoff
        modified_effective_precipitation = \
            initilaize_soil_storage.immediate_runoff(effective_precipitation)

        # ouputs from the  modified_effective_precipitation are
        # 0 = effective_precipitation (mm/day),  1 = immediate_runoff (mm/day)
        effective_precipitation_corr = modified_effective_precipitation[0]
        immediate_runoff = modified_effective_precipitation[1]

        # compute daily soil water balance.
        daily_soil_storage = initilaize_soil_storage.\
            soil_balance(self.soil_water_content, pet_to_soil,
                         current_landarea_frac, landareafrac_ratio,
                         max_temp_elev, canopy_evap,
                         effective_precipitation_corr, precipitation,
                         immediate_runoff, land_storage_change_sum,
                         sublimation, daily_storage_transfer,
                         self.parameters.snow_freeze_temp)

        # ouputs from the  daily_soil_storage  are
        # 0 = soil_water_content (mm),
        # 1 = groundwater_recharge_from_soil_mm (mm),
        # 2 = actual_soil_evap (mm/day), 3 =  soil_saturation (-),
        # 4 = surface_runoff (mm/day) , 5 = daily_storage_tranfer (mm/day)

        self.soil_water_content = daily_soil_storage[0]
        groundwater_recharge_from_soil_mm = daily_soil_storage[1]
        surface_runoff = daily_soil_storage[4]
        daily_storage_transfer = daily_soil_storage[5]

        # =====================================================================
        # Getting all storages
        # =====================================================================
        # write out data per continental fraction
        per_contfrac = current_landarea_frac / self.cont_frac

        VerticalWaterBalance.storages.\
            update({'canopystor': self.canopy_storage * per_contfrac,
                    'swe': self.snow_water_storage * per_contfrac,
                    'soilmoist':  self.soil_water_content * per_contfrac})

        # =====================================================================
        # Getting all fluxes
        # =====================================================================

        VerticalWaterBalance.fluxes.\
            update({'netrad': radiation_for_potevap.net_radiation,
                    'potevap': daily_potential_evap,
                    'lai': leaf_area_index,
                    'canopy_evap': canopy_evap * per_contfrac,
                    'throughfall': throughfall * per_contfrac,
                    'snow_fall': snow_fall * per_contfrac,
                    'snow_melt': snow_melt * per_contfrac,
                    'snow_evap': sublimation * per_contfrac,
                    'groundwater_recharge': groundwater_recharge_from_soil_mm,
                    'surface_runoff': surface_runoff,
                    'openwater_PET': openwater_potential_evap,
                    'daily_storage_transfer': daily_storage_transfer,
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
