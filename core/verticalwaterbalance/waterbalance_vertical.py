# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""vertical waterbalance function with optimised with numba."""

import numpy as np
from numba import njit
from core.verticalwaterbalance import radiation_evapotranspiration as rad_pet
from core.verticalwaterbalance import lai
from core.verticalwaterbalance import canopy
from core.verticalwaterbalance import snow
from core.verticalwaterbalance import soil


@njit(cache=True)
def vert_water_balance(rout_order, temperature, down_shortwave_radiation,
                       down_longwave_radiation, snow_water_storage,
                       snow_albedo_thresh, openwater_albedo, snow_albedo,
                       albedo, emissivity, humid_arid, pt_coeff_humid_arid, 
                       growth_status, lai_days, initial_days,
                       cum_precipitation, precipitation, min_leaf_area_index,
                       max_leaf_area_index, land_cover, canopy_storage,
                       current_landarea_frac, landareafrac_ratio,
                       max_storage_coefficient, minstorage_volume,
                       daily_storage_transfer,
                       snow_water_storage_subgrid, degreeday, elevation,
                       adiabatic_lapse_rate, snow_freeze_temp, snow_melt_temp,
                       runoff_frac_builtup, builtup_area, soil_water_content,
                       gamma, max_daily_pet, soil_texture, drainage_direction,
                       max_groundwater_recharge, groundwater_recharge_factor,
                       critcal_gw_precipitation, max_soil_water_content,
                       areal_corr_factor, region):
    # =========================================================================
    #   Creating outputs for storages, fluxes and factors
    # =========================================================================
    #                  =================================
    #                  ||    Radiation and PET        ||
    #                  =================================
    net_radiation = region.copy()
    openwater_net_radiation = region.copy()
    daily_potential_evap = region.copy()
    openwater_potential_evap = region.copy()

    #                  =================================
    #                  ||    Leaf area index          ||
    #                  =================================
    leaf_area_index = region.copy()

    #                  =================================
    #                  ||    Canopy (Intercrption)    ||
    #                  =================================
    canopy_storage_out = region.copy() + canopy_storage.copy()
    throughfall = region.copy()
    canopy_evap = region.copy()
    pet_to_soil = region.copy()
    land_storage_change_sum = region.copy()

    #                  =================================
    #                  ||           Snow              ||
    #                  =================================
    snow_water_storage_out = region.copy() + snow_water_storage.copy()
    snow_water_storage_subgrid_out = snow_water_storage_subgrid.copy()
    snow_fall = region.copy()
    sublimation = region.copy()
    snow_melt = region.copy()
    effective_precipitation = region.copy()
    max_temp_elev = region.copy()

    #                  =================================
    #                  ||           Soil             ||
    #                  =================================
    soil_water_content_out = region.copy() + soil_water_content.copy()
    immediate_runoff = region.copy()
    groundwater_recharge_from_soil_mm = region.copy()
    surface_runoff = region.copy()

    # =====================================================================
    # Loop through rout order
    # =====================================================================
    for routflow_looper in range(len(rout_order)):
        # Get invidividual cells based on routing order
        x, y = rout_order[routflow_looper]
        
        if np.isnan(region[x, y ]) == False:
            # =================================================================
            #       Radiation compononents and Priestley-Taylor PET
            # =================================================================
            radiation_for_potevap = rad_pet.\
                compute_radiation(temperature[x, y],
                                  down_shortwave_radiation[x, y],
                                  down_longwave_radiation[x, y],
                                  snow_water_storage[x, y],
                                  snow_albedo_thresh[x, y],
                                  openwater_albedo[x, y],
                                  snow_albedo[x, y], albedo[x, y],
                                  emissivity[x, y], x, y)
    
            net_rad, openwater_net_rad = radiation_for_potevap
            net_radiation[x, y] = net_rad
            openwater_net_radiation[x, y] = openwater_net_rad
    
            pot_evap, openwater_evap = \
                rad_pet.priestley_taylor(temperature[x, y],
                                         pt_coeff_humid_arid[x, y],
                                         net_radiation[x, y],
                                         openwater_net_radiation[x, y], x, y)
    
            daily_potential_evap[x, y] = pot_evap.item()
            openwater_potential_evap[x, y] = openwater_evap.item()
    
            # =================================================================
            #               	 Daily leaf area index
            # =================================================================
            daily_leaf_area_index = lai.\
                get_leaf_area_index(temperature[x, y], growth_status[x, y],
                                    lai_days[x, y], initial_days[x, y],
                                    cum_precipitation[x, y], precipitation[x, y],
                                    leaf_area_index[x, y], min_leaf_area_index[x, y],
                                    max_leaf_area_index[x, y], land_cover[x, y],
                                    humid_arid[x, y])
    
            # ouputs from the get_leaf_area_index" are
            # 0 = daily leaf area index (-),
            # 1 = days since start leaf area index profile (days),
            # 2 = cumulative precipitation (mm/day)  and 3 = growth status(-)
            # ouput(1-3)  get updated per time step.
    
            leaf_area_index[x, y] = daily_leaf_area_index[0]
            lai_days[x, y] = daily_leaf_area_index[1]
            cum_precipitation[x, y] = daily_leaf_area_index[2]
            growth_status[x, y] = daily_leaf_area_index[3]
    
            # =================================================================
            #               Canopy Water Balance
            # =================================================================
            daily_canopy_storage = canopy.\
                canopy_balance(canopy_storage[x, y],
                               leaf_area_index[x, y],
                               daily_potential_evap[x, y],
                               precipitation[x, y],
                               current_landarea_frac[x, y],
                               landareafrac_ratio[x, y],
                               max_storage_coefficient[x, y],
                               minstorage_volume)
    
            # ouputs from the  daily_canopy_storage are
            # 0 = canopy_storage (mm), 1 = throughfall (mm/day),
            # 2 = canopy_evap (mm/day) , 3 = pet_to_soil (mm/day),
            # 4 = land_storage_change_sum (mm)
            # 5 = daily_storage_tranfer (mm/day)
    
            canopy_storage_out[x, y] = daily_canopy_storage[0]
            throughfall[x, y] = daily_canopy_storage[1]
            canopy_evap[x, y] = daily_canopy_storage[2]
            pet_to_soil[x, y] = daily_canopy_storage[3]
            land_storage_change_sum[x, y] = daily_canopy_storage[4]
            daily_storage_transfer[x, y] = daily_canopy_storage[5]
    
            # =================================================================
            #               Snow Water Balance
            # =================================================================
            daily_snow_storage = \
                snow.subgrid_snow_balance(snow_water_storage[x, y],
                                          snow_water_storage_subgrid[:, x, y],
                                          temperature[x, y],
                                          precipitation[x, y],
                                          throughfall[x, y],
                                          pet_to_soil[x, y],
                                          land_storage_change_sum[x, y],
                                          degreeday[x, y],
                                          current_landarea_frac[x, y],
                                          landareafrac_ratio[x, y],
                                          elevation[:, x, y],
                                          daily_storage_transfer[x, y],
                                          adiabatic_lapse_rate[x, y],
                                          snow_freeze_temp[x, y],
                                          snow_melt_temp[x, y],
                                          minstorage_volume, x, y)
            # ouputs from the  daily_snow_storage  are
            # 0 = snow_water_storage (mm), 1 = snow_water_storage_subgrid (mm),
            # 2 = snow_fall (mm/day), 3 = sublimation (mm/day),
            # 4 = snow_melt (mm/day)
            # 5 = effective_precipitation (mm/day), 6 = max_elev_temp(K),
            # 7 = land_storage_change_sum (mm),  8 = daily_storage_tranfer (mm/day)
            # 9 = snow cover fraction (-)
    
            snow_water_storage_out[x, y] = daily_snow_storage[0]
            snow_water_storage_subgrid_out[:, x, y] = daily_snow_storage[1]
            snow_fall[x, y] = daily_snow_storage[2]
            sublimation[x, y] = daily_snow_storage[3]
            snow_melt[x, y] = daily_snow_storage[4]
            effective_precipitation[x, y] = daily_snow_storage[5]
            max_temp_elev[x, y] = daily_snow_storage[6]
            land_storage_change_sum[x, y] = daily_snow_storage[7]
            daily_storage_transfer[x, y] = daily_snow_storage[8]
            # # ===================================================================
            # #                       Soil Water Balance
            # # ===================================================================
            # Modified effective precipitation and immediate runoff
            modified_effective_precipitation = \
                soil.immediate_runoff(effective_precipitation[x, y],
                                      runoff_frac_builtup[x, y],
                                      builtup_area[x, y])
    
            # ouputs from the  modified_effective_precipitation are
            # 0 = effective_precipitation (mm/day)
            # 1 = immediate_runoff (mm/day)
            effective_precipitation[x, y] = modified_effective_precipitation[0]
            immediate_runoff[x, y] = modified_effective_precipitation[1]
    
            # compute daily soil water balance.
            daily_soil_storage = soil.\
                soil_balance(soil_water_content[x, y], pet_to_soil[x, y],
                             current_landarea_frac[x, y],
                             landareafrac_ratio[x, y],
                             max_temp_elev[x, y], canopy_evap[x, y],
                             effective_precipitation[x, y],
                             precipitation[x, y],
                             immediate_runoff[x, y],
                             land_storage_change_sum[x, y],
                             sublimation[x, y],
                             daily_storage_transfer[x, y],
                             snow_freeze_temp[x, y],
                             gamma[x, y], max_daily_pet[x, y], humid_arid[x, y],
                             soil_texture[x, y], drainage_direction[x, y],
                             max_groundwater_recharge[x, y],
                             groundwater_recharge_factor[x, y],
                             critcal_gw_precipitation[x, y],
                             max_soil_water_content[x, y],
                             areal_corr_factor[x, y],
                             minstorage_volume, x, y)
    
            # ouputs from the  daily_soil_storage  are
            # 0 = soil_water_content (mm),
            # 1 = groundwater_recharge_from_soil_mm (mm),
            # 2 = actual_soil_evap (mm/day), 3 =  soil_saturation (-),
            # 4 = surface_runoff (mm/day) , 5 = daily_storage_tranfer (mm/day)
            # 6 =  (RL) potential runoff from landcells including the amount of
            # gw-recharge (mm/day)
            # 7 = (R3) daily runoff from soil (mm/day)
            # 8 = (R2) soil overflow runoff from landcells (mm/day)
            # 9 = (R1) urban runoff from landcells (mm/day) : (accounts only
            # for built-up area)
    
            soil_water_content_out[x, y] = daily_soil_storage[0]
            groundwater_recharge_from_soil_mm[x, y] = daily_soil_storage[1]
            surface_runoff[x, y] = daily_soil_storage[4]
            daily_storage_transfer[x, y] = daily_soil_storage[5]

    return net_radiation, openwater_net_radiation, daily_potential_evap,\
        openwater_potential_evap, leaf_area_index, lai_days, cum_precipitation,\
        growth_status, canopy_storage_out, throughfall, canopy_evap, \
        pet_to_soil, snow_water_storage_out, snow_water_storage_subgrid_out, \
        snow_fall, sublimation, snow_melt, soil_water_content_out, \
        groundwater_recharge_from_soil_mm, surface_runoff, \
        land_storage_change_sum, daily_storage_transfer




