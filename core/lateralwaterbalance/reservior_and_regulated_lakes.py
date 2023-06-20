# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Reserviors and Regulated lakes"""

# =============================================================================
# This module computes water balance for reserviors and regulated lakes,
# including storage and related fluxes for all grid cells based on section
#   4.6.1 of (Müller Schmied et al. (2021)).
# =============================================================================

import numpy as np
from numba import njit
from core.lateralwaterbalance import reduction_factor as rf
from core.lateralwaterbalance import hanasaki_reslease_alg as hanaski


@njit(cache=True)
def reservior_and_regulated_lake(rout_order, routflow_looper, outflow_cell,
                                 storage, stor_capacity, precipitation,
                                 openwater_pot_evap, aridity, drainage_direction,
                                 inflow_to_swb, swb_outflow_coeff,
                                 groundwater_recharge_constant, reservior_area,
                                 reduction_exponent_res, areal_corr_factor,
                                 res_start_month, simulation_momth_day,
                                 k_release, reservoir_type,
                                 allocation_coeff, monthly_demand,
                                 mean_annual_demand, mean_annual_inflow,):
    # ************************************************************************
    # Note: To estimate the water demand of 5 cells downstream from a
    # reservoir, the reservoir area for all grid cells is read in and the
    # relevant 5 downstream cells are selected for water demand calculation.
    # ************************************************************************

    # Index to  print out varibales of interest
    # e.g  if x==65 and y==137: print(prev_gw_storage)
    x, y = rout_order[routflow_looper]

    # =========================================================================
    #     Parameters for reservior and regulated lake.
    # =========================================================================
    # convert m to km
    m_to_km = 0.001

    # =========================================================================
    storage_prevstep = storage

    # =========================================================================
    # Computing evaoration reduction factor (km2/day) for
    # reservior and regulated lake. Equation 24 & 25 in
    # (Müller Schmied et al. (2021)) .
    # =========================================================================
    max_storage = stor_capacity

    # For reservior and regulated lake, reduction factor is used for reducing
    # evaporation and not area since area is assumed not to be dynamic.
    # This would prevent continuous decline of storage levels in some regions
    # i.e. ((semi)arid regions)

    evapo_redfactor = \
        rf.swb_redfactor(storage_prevstep, max_storage, reduction_exponent_res)

    # =========================================================================
    # Computing reservior or regulated lake corrected evaporation
    # (openwater_evapo_cor[km3/day])
    # =========================================================================
    # /////////////////////////////////////////////////////////////////////////
    # Areal correction factor (CFA) approach for correcting
    # open water evaporation.

    # Water balance of surface waterbodies (lakes,wetlands and reservoir)
    # except rivers is given as: See Eqn. 22 in Müller Schmied et al. (2021).
    # dS/dt = A(P - PET) + Qin - NAs - gwr_swb - Qout

    # (P - PET) is considered (crudely) as the runoff from the respective SWB.
    # Therefore, CFA is applied as a correction factor on  only (P - PET)
    # and only P and PET are taken into account to compute corrected PET.

    # Approach to compute PET_corrected:
    # equation 1) P - PET = Runoff

    # equation 2) P - PET_corr = Runoff * CFA
    # 		      Runoff = (P - PET_corr)/CFA
    #
    # 	equation 2) in equation 1):
    # 	P - PET = (P - PET_corr)/CFA
    # 	(P - PET) * CFA = P - PET_corr
    #
    # 	CFA*P - CFA * PET = P - PET_corr
    # 	PET_corr = P - CFA*P + CFA * PET
    #
    #   Final equation for corrected PET
    #   PET_corr = (1 - CFA) * P + CFA * PET
    #
    # /////////////////////////////////////////////////////////////////////////

    # Reducing potential evaporation for reservior or regulated lake using
    # reduction factor
    openwater_pet = openwater_pot_evap * evapo_redfactor

    # CFA correction approach for open water evaporation
    openwater_evapo_cor = (1 - areal_corr_factor) * precipitation + \
        (areal_corr_factor * openwater_pet)

    openwater_evapo_cor = np.where(openwater_evapo_cor < 0, 0,
                                   openwater_evapo_cor)

    # =========================================================================
    # Calculating groundwater recharge[gwr_reservior (km3/day)] for reservior
    # or regulated lake
    # =========================================================================

    # Point source recharge is calculated for arid regions only. Except in arid
    # inland sinks.
    gwr_reservior = np.where((aridity == 1) & (drainage_direction >= 0),
                             groundwater_recharge_constant * m_to_km *
                             reservior_area[x, y] * evapo_redfactor, 0)

    # =========================================================================
    # Total inflow is the sum of inflow and open water precipitation into the
    # waterbody(km3/day)
    # =========================================================================
    total_inflow = inflow_to_swb + precipitation * reservior_area[x, y]

    # *****************************************
    # If both global lake and reservoir are found in the same outflow cell.
    # The demand is shared equally(50%) between.
    # If the global lake cannot meet the water demand, the reservoir tries to
    # fuffill this demand.
    # *****************************************

    # =========================================================================
    # Combininig  open water PET and point source recharge into petgwr(km3/day)
    # =========================================================================
    # petgwr will change for Global lake if water-use is considerd ******
    petgwr = openwater_evapo_cor * reservior_area[x, y] + gwr_reservior

    # petgwr_max is the maximum amount of openwater_evapo_cor + gwr_reservior
    # to ensure that reservior storage does not fall below 10% of the storage
    # capacity.
    petgwr_max = storage_prevstep + total_inflow

    # Note: Evaporation and  groundwater recharge can occur until storage = 0,
    # but not for abstractions. Abstractions can only occur until the level
    # is 10% of the capacity. So, for reservoirs, evaporation and recharge have
    # priority over abstractions.

    # Reduce point source recharge and open water evaporation when
    # petgwr >  petgwr_max. (check for zero division)
    if (petgwr > 0) and (petgwr > petgwr_max):
        storage_limit = 0
        storage = storage_limit  # same as storage_prevstep + total_inflow - petgwr_max
        gwr_reservior *= (petgwr_max/petgwr)

        openwater_evapo_cor *= (petgwr_max/petgwr)

    else:
        # reservior is solved numerically.
        storage = storage_prevstep + total_inflow - petgwr

    release, k_release_new = hanaski.\
        hanasaki_res_reslease(storage, stor_capacity, res_start_month,
                              simulation_momth_day, k_release, reservoir_type,
                              rout_order, outflow_cell, routflow_looper,
                              reservior_area, allocation_coeff, monthly_demand,
                              mean_annual_demand, mean_annual_inflow,
                              inflow_to_swb)

    # Reservoirs release (outflow) water based on their current level [S(t)]
    # convert release from m3/s to km3/day since temporal resultion is daily
    to_km3_per_day = (86400/1e9)

    if storage >= (stor_capacity * 0.1):

        outflow = release * to_km3_per_day
    else:
        # for environmental flow requirement limit release to only 10%
        outflow = 0.1 * release * to_km3_per_day

    if outflow < 0:
        outflow = 0

    # substract outflow from storage
    storage -= outflow

    # reduce G_gloResStorage to maximum storage capacity
    if storage > max_storage:
        outflow += (storage - max_storage)
        # updating storage
        storage = max_storage

    if storage < 0:
        outflow += storage
        storage = 0

    if x==99 and y==610:
        print(storage,  outflow)

    return storage, outflow, gwr_reservior, k_release_new
