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
from numba import njit


@njit(cache=True)
def canopy_balance(canopy_storage, daily_leaf_area_index, potential_evap,
                   precipitation, current_landarea_frac, landareafrac_ratio,
                   max_storage_coefficient, minstorage_volume):
    """
    Calulate daily canopy balanceincluding canopy storage and water flows
    entering and leaving the canopy storage.

    Parameters
    ----------
    canopy_storage : float
        Daily canopy storage,  Units: [mm]
    daily_leaf_area_index : float
       Daily leaf area index  Units: [-]
    potential_evap : float
        Daily potential  evapotranspiration,  Units: [mm/day]
    precipitation : float
        Daily precipitation,  Units: [mm/day]
    current_landarea_frac : float
      Land area fraction of current time step,  Units: [-]
    landareafrac_ratio : float
       Ratio of land area fraction of previous to current time step, Units: [-]
    max_storage_coefficient:
        coefficient for computing maximum canopy storage, Units: [-]
    minstorage_volume: float
        Volumes at which storage is set to zero, units: [km3]

    Returns
    -------
    canopy_storage : float
        Updated daily canopy stroage,  Units: [mm]
    throughfall : float
        Throughfall,  Units: [mm/day]
    canopy_evap : float
        Canopy evaporation,  Units: [mm/day]
    pet_to_soil : float
        Remaining energy for addtional soil evaporation, Units: [mm/day]
    land_storage_change_sum : float
        Sum of change in vertical balance storages, Units: [mm]
    daily_storage_transfer : float
        Storage to be transfered to runoff when land area fraction of current
        time step is zero, Units: [mm]
    """
    if current_landarea_frac > 0:
        # =========================================================
        # Adapt for change in land area fraction on canopy storage
        # =========================================================
        canopy_storage *= landareafrac_ratio

        # minimal storage volume =1e15 (smaller volumes set to zero) to counter
        # numerical inaccuracies
        if np.abs(canopy_storage) <= minstorage_volume:
            canopy_storage = 0

        # print(landareafrac_ratio[116, 454])
        # Initial storage to calulate change in canopy_storage.
        initial_storage = canopy_storage

        if daily_leaf_area_index > 0:
            # =================================================================
            # Calculating maxumum storage and canopy storage deficit (mm)
            # =================================================================
            # See Eq. 4 in Müller Schmied et al 2021. for maximum storage
            # equation
            max_canopy_storage = max_storage_coefficient * daily_leaf_area_index
            canopy_storage_difference = max_canopy_storage - canopy_storage

            # =================================================================
            # Calculating throughfall (mm/day) and canopy storage (mm)
            # ================================================================
            # See Eq. 3 in Müller Schmied et al 2021. for throughfall equation

            if precipitation < canopy_storage_difference:
                throughfall = 0
                canopy_storage += precipitation
            else:
                throughfall = precipitation - canopy_storage_difference
                canopy_storage = max_canopy_storage

            # =================================================================
            # Calculating Canopy Evaporation (mm/day)
            # =================================================================
            # Check non zero division for canopy_storage and max_canopy_storage
            # required for canopy evaporation
            if max_canopy_storage > 0:
                canopy_evap = potential_evap * \
                    (canopy_storage / max_canopy_storage)**(2 / 3)
            else:
                canopy_evap = 0

            if canopy_evap > canopy_storage:
                canopy_evap = canopy_storage

                # Note!!! not all PET is used for canopy evaporation.
                # Part goes to the soil which is the variable pet_to_soil.
                pet_to_soil = potential_evap - canopy_storage
                canopy_storage = 0
            else:
                canopy_storage -= canopy_evap
                pet_to_soil = potential_evap - canopy_evap

        else:
            throughfall = precipitation
            pet_to_soil = potential_evap
            canopy_evap = 0

        # Computing change in canopy storage
        canopy_storage_change = canopy_storage - initial_storage

        # land_storage_change_sum variable is the sum of all vertical water
        # balance storage change (canopy, snow, soil):
        # used for AET correction. see soil.py  module
        land_storage_change_sum = canopy_storage_change

    else:
        # =========================================================================
        # Check if  current_landarea_frac == 0 , then add previous storage to
        # daily_storage_tranfer. This storage will then  added to runoff.
        # (e.g. island)
        # =========================================================================
        daily_storage_transfer = canopy_storage
        canopy_storage = 0
        canopy_evap = 0

    if pet_to_soil < 0:
        pet_to_soil = 0

    return canopy_storage, throughfall, canopy_evap, pet_to_soil, \
        land_storage_change_sum, daily_storage_transfer
