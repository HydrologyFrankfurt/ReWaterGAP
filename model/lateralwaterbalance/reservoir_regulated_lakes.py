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
from model.lateralwaterbalance import storage_reduction_factor as rf
from model.lateralwaterbalance import reservoir_release_hanasaki as hanaski
from model.lateralwaterbalance import reservoir_release_tharthar as scaling


@njit(cache=True)
def reservoir_regulated_lake_water_balance(rout_order, routflow_looper, outflow_cell,
                                           storage, stor_capacity, precipitation,
                                           openwater_pot_evap, aridity, drainage_direction,
                                           inflow_to_swb,
                                           groundwater_recharge_constant, reservior_area,
                                           reduction_exponent_res, areal_corr_factor,
                                           res_start_month, simulation_momth_day,
                                           k_release, reservoir_type,
                                           allocation_coeff, monthly_demand,
                                           mean_annual_demand, mean_annual_inflow,
                                           glolake_area,
                                           accumulated_unsatisfied_potential_netabs_sw,
                                           accumulated_unsatisfied_potential_netabs_glolake,
                                           num_days_in_month,
                                           all_reservoir_and_regulated_lake_area,
                                           reg_lake_redfactor_firstday, minstorage_volume,
                                           res_inflow_past_30days, 
                                           counter_for_tharthar_mean_30days):
    """
    Compute water balance for reservoirs and regulated lakes.

    Parameters
    ----------
    rout_order : array
        Routing order for the grid cells.
    routflow_looper : int
        Routing flow looper.
    outflow_cell : array
        Outflow cells (downstream cell) for respective grid cells.
    storage : float
        Current storage in the reservoir, Unit: [km^3].
    stor_capacity : float
        Storage capacity of the reservoir, Unit: [km^3].
    precipitation : float
        Daily precipitation, Unit: [km^3/day].
    openwater_pot_evap : float
        Potential evaporation from open water, Unit: [km^3/day].
    aridity : array
        Integer which differentiates arid(aridity=1) from
        humid(aridity=0) regions taken from  [1]_ , Units: [-]
    drainage_direction : array
        Drainage direction for each grid cell, Units: [-]
    inflow_to_swb : float
        Inflow to surface water bodies, Unit: [km^3/day].
    groundwater_recharge_constant : float
       Groundwater recharge constant below lakes, reserviors & wetlands (=0.01)
       Eqn 26 [1]_, Unit: [m/day]
    reservior_area : array
        Reservoir area for each grid cell, Unit: [km^2].
    reduction_exponent_res : float
        Reduction exponent for reservoirs (= 2.81383) Eqn 25 [1]_, Units: [-]
    areal_corr_factor : float
        Areal correction factor for grid cell.
    res_start_month : int
        Start month for reservoir operations.
    simulation_momth_day : array
        array indicating the current month and day of simulation.
    k_release : float
        Release coefficient for Hanasaki algorithm Eqn 29 [1]_, Units: [-]
    reservoir_type : int
        Type of reservoir (irrigation or non irrigation).
    allocation_coeff : float
        Allocation coefficient for water release Eqn 6 [2]_.
    monthly_demand : array
        Monthly demand for each grid cell, Unit: [km^3/day].
    mean_annual_demand : array
        Mean annual demand for each grid cell, Unit: [km^3/day].
    mean_annual_inflow : array
        Mean annual inflow for each grid cell, Unit: [km^3/day].
    glolake_area : float
        Global lake area, Unit: [km^2].
    accumulated_unsatisfied_potential_netabs_sw : float
        Accumulated unsatisfied potential net abstraction from surface water, Unit: [km^3/day].
    accumulated_unsatisfied_potential_netabs_glolake : float
        Accumulated unsatisfied potential net abstraction from global lake, Unit: [km^3/day].
    num_days_in_month : int
        Number of days in the current month.
    all_reservoir_and_regulated_lake_area : array
        all reservoirs and regulated lakes areas in simulation, Unit: [km^2].
    reg_lake_redfactor_firstday : int
        Indicator for the first day to compute regulated lake reduction factor.
    minstorage_volume : float
        Minimum storage volume for the reservoir, Unit: [km^3].

    References.

    .. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                The global water resources and use model WaterGAP v2.2d:
                model description and evaluation. Geoscientific Model
                Development, 14(2), 1037–1079.
                https://doi.org/10.5194/gmd-14-1037-2021

    .. [2] Naota Hanasaki, Shinjiro Kanae, Taikan Oki, A reservoir operation 
            scheme for global river routing models, Journal of Hydrology,
            Volume 327, Issues 1–2, 2006,
            Pages 22-41, ISSN 0022-1694,
            https://doi.org/10.1016/j.jhydrol.2005.11.011.

    Returns
    -------
    storage : float
        Updated storage in the reservoir after the water balance, Unit: [km^3].
    outflow : float
        Outflow from the reservoir, Unit: [km^3/day].
    gwr_reservior : float
        Groundwater recharge for the reservoir, Unit: [km^3/day].
    k_release_new : float
        Updated release coefficient for Hanasaki algorithm.
    accumulated_unsatisfied_potential_netabs_res : float
        Updated accumulated unsatisfied potential net abstraction from reservoir, Unit: [km^3/day].
    actual_use_sw : float
        Actual netabstraction  from reservoir, Unit: [km^3/day].

    """
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
    if reg_lake_redfactor_firstday == 1:
        evapo_redfactor = 0
    else:
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

    # *************************************************************************
    # If both global lake and reservoir are found in the same outflow cell.
    # The demand is shared equally(50%) between.
    # If the global lake cannot meet the water demand, the reservoir tries to
    # fuffill this demand.
    # *************************************************************************
    if glolake_area > 0:
        accumulated_unsatisfied_potential_netabs_res = \
            accumulated_unsatisfied_potential_netabs_sw * 0.5 + \
            accumulated_unsatisfied_potential_netabs_glolake
    else:
        accumulated_unsatisfied_potential_netabs_res = \
            accumulated_unsatisfied_potential_netabs_sw

    # Needed To compute daily actual use
    acc_unsatisfied_potnetabs_res_start = \
        accumulated_unsatisfied_potential_netabs_res

    # Note: Evaporation and  groundwater recharge can occur until storage = 0,
    # but not for abstractions. Abstractions can only occur until the level
    # is 10% of the capacity. So, for reservoirs, evaporation and recharge have
    # priority over abstractions.

    # =========================================================================
    # Combininig  open water PET and point source recharge into petgwr(km3/day)
    # =========================================================================
    petgwr = openwater_evapo_cor * reservior_area[x, y] + gwr_reservior

    # petgwr_max is the maximum amount of openwater_evapo_cor + gwr_reservior
    # to ensure that reservior storage does not fall below 10% of the storage
    # capacity.
    petgwr_max = storage_prevstep + total_inflow

    # Reduce point source recharge and open water evaporation when
    # petgwr >  petgwr_max. (check for zero division)
    if (petgwr > 0) and (petgwr > petgwr_max):
        storage_limit = 0
        storage = storage_limit  # same as storage_prevstep + total_inflow - petgwr_max
        gwr_reservior *= (petgwr_max/petgwr)

        openwater_evapo_cor *= (petgwr_max/petgwr)

    else:
        # reservior water balance  is solved numerically.
        storage = storage_prevstep + total_inflow - petgwr

    # Water abstraction can now occur after satisfying PET and gwr_reservior
    if accumulated_unsatisfied_potential_netabs_res < 0:
        # Here potential net abstraction from surface water is negative (return
        # flows) and hence used to increase reservoir storage
        storage -= accumulated_unsatisfied_potential_netabs_res
        accumulated_unsatisfied_potential_netabs_res = 0
    else:
        if storage > (0.1 * stor_capacity):
            if accumulated_unsatisfied_potential_netabs_res < \
                    (storage - (0.1 * stor_capacity)):
                storage -= accumulated_unsatisfied_potential_netabs_res
                accumulated_unsatisfied_potential_netabs_res = 0
            else:
                accumulated_unsatisfied_potential_netabs_res -= \
                    (storage - (0.1 * stor_capacity))
                storage = 0.1 * stor_capacity

    if np.abs(storage) <= minstorage_volume:
        storage= 0
    # compute relase from Hanasaki algorithm
    if x == 112 and y == 446:
        
        release, counter_for_tharthar_mean_30days = scaling.scaling_res_reslease(storage, stor_capacity,
                                  simulation_momth_day,
                                  mean_annual_inflow,
                                  inflow_to_swb,
                                  res_inflow_past_30days, 
                                  counter_for_tharthar_mean_30days)
    
    else:
        release, k_release_new = hanaski.\
            hanasaki_res_reslease(storage, stor_capacity, res_start_month,
                                  simulation_momth_day, k_release, reservoir_type,
                                  rout_order, outflow_cell, routflow_looper,
                                  reservior_area, allocation_coeff, monthly_demand,
                                  mean_annual_demand, mean_annual_inflow,
                                  inflow_to_swb, num_days_in_month,
                                  all_reservoir_and_regulated_lake_area)

    # Reservoirs release (outflow) water based on their current level [S(t)]
    # convert release from m3/s to km3/day since temporal resultion is daily
    to_km3_per_day = 86400/1e9

    if storage >= (stor_capacity * 0.1):

        outflow = release * to_km3_per_day
    else:
        # for environmental flow requirement limit release to only 10%
        outflow = 0.1 * release * to_km3_per_day

    if outflow < 0:
        outflow = 0

    # substract outflow from storage
    storage -= outflow

    # reduce reservoir storage to maximum storage capacity is storage > maximum
    # reservoir storage
    if storage > max_storage:
        outflow += (storage - max_storage)
        # updating storage
        storage = max_storage

    if storage < 0:
        outflow += storage
        storage = 0
    
    if x ==112 and y == 446:

        outflow_canal_capacity = 0.06  # km3/day (maximum observed 2003–2019)

        if outflow > outflow_canal_capacity:
            outflow = outflow_canal_capacity


    actual_use_sw = acc_unsatisfied_potnetabs_res_start - \
        accumulated_unsatisfied_potential_netabs_res

    # convert open water evaporation for swb from km/day to km3/day (output purpose)
    openwater_evapo_cor_km3 = openwater_evapo_cor * reservior_area[x, y]

    return storage, outflow, gwr_reservior, k_release_new, \
        accumulated_unsatisfied_potential_netabs_res, actual_use_sw, \
            openwater_evapo_cor_km3, counter_for_tharthar_mean_30days
