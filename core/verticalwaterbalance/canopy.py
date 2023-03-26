# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Canopy storage."""

# =============================================================================
# This modules computes the canopy water balance, including canopy storage and
# water flows entering and leaving the canopy storage.
# Based on section 4.2 of (Müller Schmied et al. (2021)).
# =============================================================================

import numpy as np



def canopy_balance(canopy_storage, daily_leaf_area_index, potential_evap,
                   precipitation, current_landarea_frac, landareafrac_ratio,
                   max_storage_coefficient):
    """
    Calulate daily canopy balanceincluding canopy storage and water flows
    entering and leaving the canopy storage.

    Parameters
    ----------
    canopy_storage : array
        Daily canopy storage,  Units: [mm]
    daily_leaf_area_index : array
       Daily leaf area index  Units: [-]
    potential_evap : array
        Daily potential  evapotranspiration,  Units: [mm/day]
    precipitation : array
        Daily precipitation,  Units: [mm/day]
    current_landarea_frac : array
      Land area fraction of current time step,  Units: [-]
    landareafrac_ratio : array
       Ratio of land area fraction of previous to current time step, Units: [-]
    max_storage_coefficient:
        coefficient for computing maximum canopy storage, Units: [-]

    Returns
    -------
    canopy_storage : array
        Updated daily canopy stroage,  Units: [mm]
    throughfall : array
        Throughfall,  Units: [mm/day]
    canopy_evap : array
        Canopy evaporation,  Units: [mm/day]
    pet_to_soil : array
        Remaining energy for addtional soil evaporation, Units: [mm/day]
    land_storage_change_sum : array
        Sum of change in vertical balance storages, Units: [mm]
    daily_storage_transfer : array
        Storage to be transfered to runoff when land area fraction of current
        time step is zero, Units: [mm]
    """
    # =========================================================================
    # Check if  current_landarea_frac == 0 , then add previous storage to
    # daily_storage_tranfer. This storage will then  added to runoff.
    # (e.g. island)
    # =========================================================================
    daily_storage_transfer = \
        np.where(current_landarea_frac == 0, canopy_storage.copy(), 0)

    # =========================================================================
    # Adapt for change in land area fraction on canopy storage
    # =========================================================================
    canopy_storage *= landareafrac_ratio
    # print(landareafrac_ratio[116, 454])
    # Initial storage to calulate change in canopy_storage.
    initial_storage = canopy_storage.copy()

    # =================================================================
    # Calculating maxumum storage and canopy storage deficit (mm)
    # =================================================================
    # See Eq. 4 in Müller Schmied et al 2021. for maximum storage equation
    max_canopy_storage = max_storage_coefficient * daily_leaf_area_index
    canopy_storage_difference = max_canopy_storage - canopy_storage

    # =================================================================
    # Calculating throughfall (mm/day) and canopy storage (mm)
    # ================================================================
    # See Eq. 3 in Müller Schmied et al 2021. for throughfall equation
    throughfall = np.where(precipitation < canopy_storage_difference, 0,
                           precipitation - canopy_storage_difference)

    throughfall = np.where(daily_leaf_area_index > 0,
                           throughfall, precipitation)
    throughfall[current_landarea_frac <= 0] = 0

    # canopy storage state new is a helper variable for computing the actual
    # canopy storage state.

    canopy_storage_new = \
        np.where(precipitation < canopy_storage_difference,
                 canopy_storage + precipitation,
                 max_canopy_storage)

    # =================================================================
    # Calculating Canopy Evaporation (mm/day)
    # ================================================================
    # Check non zero division for  canopy_storage and  max_canopy_storage
    # required for canopy evaporation

    canopy_storage_fraction = np.divide(canopy_storage_new,
                                        max_canopy_storage,
                                        out=np.zeros_like(max_canopy_storage),
                                        where=max_canopy_storage != 0)

    # Note!! canopy_evap_cal is a helper variable which is then passed to the
    # actual variable 'canopy_evap' after comparison with canopy_storage_new.
    # canopy_evap_cal is calulated using Eq.6 in Müller Schmied et al 2021.
    canopy_evap_cal = potential_evap * \
        np.power(canopy_storage_fraction, (2 / 3),
                 out=np.zeros_like(canopy_storage_fraction),
                 where=canopy_storage_fraction >= 0)

    canopy_evap = np.where(canopy_evap_cal > canopy_storage_new,
                           canopy_storage_new, canopy_evap_cal)
    canopy_evap = np.where(daily_leaf_area_index > 0, canopy_evap, 0)
    canopy_evap[current_landarea_frac <= 0] = 0

    # =========================================================================
    # Calculating potential evapotranspiration to soil (Pet_to_soil (mm/day))
    # =========================================================================
    # Note!!! not all PET is used for canopy evaporation. Part goes to the soil
    # which is the variable pet_to_soil.

    pet_to_soil = np.where(canopy_evap_cal > canopy_storage_new,
                           potential_evap - canopy_storage_new,
                           potential_evap - canopy_evap_cal)

    pet_to_soil = np.where(daily_leaf_area_index > 0, pet_to_soil,
                           potential_evap)
    pet_to_soil[pet_to_soil < 0] = 0
    pet_to_soil[current_landarea_frac <= 0] = 0

    # Updating  canopy_storage_new after canopy evaporation
    canopy_storage_new = \
        np.where(canopy_evap_cal > canopy_storage_new, 0,
                 canopy_storage_new - canopy_evap_cal)

    # =========================================================================
    # Updating  Canopy storage (mm)
    # =========================================================================
    # canopy_storage becomes canopy_storage_new when daily_leaf_area_index > 0
    # else keep its initial storage values
    canopy_storage = np.where(daily_leaf_area_index > 0, canopy_storage_new,
                              initial_storage)

    canopy_storage[current_landarea_frac <= 0] = 0

    # computing change in canopy storage
    canopy_storage_change = canopy_storage - initial_storage

    # land_storage_change_sum variable is the sum of all vertical water balance
    # storage change (canopy, snow, soil)
    land_storage_change_sum = canopy_storage_change
    land_storage_change_sum[current_landarea_frac <= 0] = 0

    return canopy_storage, throughfall, canopy_evap, pet_to_soil, \
        land_storage_change_sum, daily_storage_transfer
