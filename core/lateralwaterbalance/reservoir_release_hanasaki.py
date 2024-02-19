# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""
Created on Thu Jun 15 06:59:01 2023

@author: nyenah
"""


import numpy as np
from numba import njit


@njit(cache=True)
def hanasaki_res_reslease(storage, stor_capacity, res_start_month,
                          simulation_momth_day, k_release, reservoir_type,
                          rout_order, outflow_cell, routflow_looper,
                          reservior_area, allocation_coeff, monthly_demand,
                          mean_annual_demand, mean_annual_inflow,
                          inflow_to_swb, num_days_in_month,
                          all_reservoir_and_regulated_lake_area):

    # Index to  print out varibales of interest
    # e.g  if x==65 and y==137: print(prev_gw_storage)
    x, y = rout_order[routflow_looper]

    # =========================================================================
    # Reserviors operation algorithm is based on Hanasaki et al 2006.
    # New operations should cited and implemented here.
    # =========================================================================
    # Note!!! Reservoirs release is based on current reservoir storage [S(t)]

    # compute release coefficient at the first day of operational year
    # see equation 3 or 29  of  Hanasaki et al 2006 and
    # Müller Schmied et al. (2021) respectively

    if simulation_momth_day[0] == res_start_month:
        if simulation_momth_day[1] == 1:
            if storage < (stor_capacity * 0.1):
                k_release = 0.1
            else:
                k_release = storage / (stor_capacity * 0.85)

    # Reservoirs are categorized into two classes of purpose thus
    # Irririgation = 1  and non-irrigitaion = 2
    if reservoir_type == 1:
        # for irrigation reservior monthly release is computed using eqn 5 & 6
        # Hanasaki et al 2006.

        # 1st calulate downstream demand considering 5 downstreanm cells for
        # each reservoir if any else calculate demand to the next reserviour
        # for the available downstream cells.

        monthly_downstream_demand = monthly_demand[x, y]  # km3/month
        mean_annual_downstream_demand = mean_annual_demand[x, y]  # m3/yr

        # downstream cell looper (dsc)
        dsc = 0
        # corresponing outflow cell for current cell[x, y]
        m, n = outflow_cell[routflow_looper]

        # *********************************************************************
        stop_mean_annual_calculation = False  # Flag to stop mean annual demand
        # calulation if the next downstream cell has a reservoir
        # *********************************************************************
        while dsc < 5 and reservior_area[m, n] <= 0 and m > 0 and n > 0:

            monthly_downstream_demand += monthly_demand[m, n] * \
                 allocation_coeff[routflow_looper][dsc]

            # Mean annual demand is computed considering all reservior area
            # in simulation
            if not stop_mean_annual_calculation:
                if all_reservoir_and_regulated_lake_area[m, n] <= 0:
                    mean_annual_downstream_demand += mean_annual_demand[m, n] * \
                        allocation_coeff[routflow_looper][dsc]
                else:
                    stop_mean_annual_calculation = True

            prev_ds_cell = np.array([m, n])
            # getting the next downstream cell.
            next_ds_cell = np.where(np.sum(rout_order == prev_ds_cell, axis=1)
                                    == rout_order.shape[1])[0]
            m, n = outflow_cell[next_ds_cell[0]]
            # update downstream cell looper
            dsc += 1

        # =====================================================================
        #         # compute provisional monthly release [m3/s]
        # =====================================================================
        # convert monthly_downstream_demand from km3/month to m3/s
        m3_per_s = 1e9 * 1/(86400 * num_days_in_month)
        monthly_downstream_demand = monthly_downstream_demand * m3_per_s
        # convert mean_annual_downstream_demand from m3/yr to m3/s
        year_to_s = 31536000
        mean_annual_downstream_demand = \
            mean_annual_downstream_demand / year_to_s

        # see eqn 3 of  Hanasaki et al 2006
        if mean_annual_downstream_demand >= (0.5 * mean_annual_inflow):
            prov_rel =\
                mean_annual_inflow / 2 * (1 + monthly_downstream_demand /
                                          mean_annual_downstream_demand)
        else:
            prov_rel = mean_annual_inflow + monthly_downstream_demand - \
                mean_annual_downstream_demand

    elif reservoir_type == 2:
        prov_rel = mean_annual_inflow  # [m3/s]
    else:
        print("unknown reservoir type")

    # =====================================================================
    # calculate monthly release [m3/s]. see eqn 7 of  Hanasaki et al 2006
    # =====================================================================
    #  c_ratio is defined as (reservoir capacity / mean total annual inflow)
    # Reservoir capacity(stor_capacity) = km3  and mean_annual_inflow = m3/s
    # hence mean_annual_inflow should be converted to km3
    to_km3 = (31536000/1e9)  # (31536000 = 365 * 24 * 60 * 60)

    # old code didnt account for division by zero, hence i am imitating the
    # same error for comparison. i will correct it here later.
    # (check gcrc 46162, x=140, y=157)******
    
    if mean_annual_inflow == 0:
        c_ratio = np.inf
    else:
        c_ratio = stor_capacity/(mean_annual_inflow * to_km3)

    if c_ratio >= 0.5:
        release = k_release * prov_rel
    else:
        # to convert inflow from km3 per day to m3/s
        to_m3_per_s = (1e9/86400)
        # release is applied on daily inflow
        release = ((4*(c_ratio)**2) * k_release * prov_rel) + \
            (1 - (4*(c_ratio)**2)) * (inflow_to_swb*to_m3_per_s)

    return release, k_release
