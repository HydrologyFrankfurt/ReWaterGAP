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
def scaling_res_reslease(storage, stor_capacity,
                          simulation_momth_day,
                          mean_annual_inflow,
                          inflow_to_swb,
                          res_inflow_past_30days, 
                          counter_for_tharthar_mean_30days):
    """
    Compute reservoir release based on 

    Parameters
    ----------
    storage : float
        Current storage in the reservoir, Unit: [km^3].
    stor_capacity : float
        Storage capacity of the reservoir, Unit: [km^3].
    routflow_looper : int
        Routing flow looper.
    mean_annual_inflow : array
        Mean annual inflow for each grid cell, Unit: [km^3/day].
    inflow_to_swb : float
        Inflow to surface water bodies, Unit: [km^3/day].
  
    Returns
    -------
    release : float
        Reservoir relase [m^3/s]
    counter_for_tharthar_mean_30days : int
        , Units: [-]

    """
    
   # See Hosseini-Moghari et al. (2025) for more detailes https://doi.org/10.5194/hess-29-4073-202
    
    k_release = storage / stor_capacity

    prov_rel = mean_annual_inflow #m3/sec
    
    # Calculated the mean of the last 30 days of inflow
    
    if counter_for_tharthar_mean_30days <= 29: # 30 days 0-29
        
        res_inflow_past_30days [counter_for_tharthar_mean_30days] = inflow_to_swb
        mean_res_inflow_past_30days = np.mean(res_inflow_past_30days)
        
    else:
        # shift left (drop oldest)
        res_inflow_past_30days[:-1] = res_inflow_past_30days[1:]

        # insert newest value
        res_inflow_past_30days[-1] = inflow_to_swb
        mean_res_inflow_past_30days = np.mean(res_inflow_past_30days)
    
    to_km3_per_day = 86400/1e9
    if mean_res_inflow_past_30days == 0:
        mean_res_inflow_past_30days = mean_annual_inflow * to_km3_per_day # m3/sec > km3/routing time step

    term1 = k_release #[-]
    term2 = mean_annual_inflow / mean_res_inflow_past_30days # [m3/sec / km3/day]

    release = (term1 * prov_rel) + (term2 * inflow_to_swb)  # m3/s See Eq. 7 in Hosseini-Moghari et al. (2025) 
    
    # One parameter for each two-month period, obtained through calibration

    P1 = 0.096652913
    P2 = 0.131673572
    P3 = 1.251222394
    P4 = 1.202061108
    P5 = 1.202061108
    P6 = 1.202061108

        
    month = simulation_momth_day[0]   # 1 = Jan ... 12 = Dec
    
    if month in (1, 2):
        release *= P1
    elif month in (3, 4):
        release *= P2
    elif month in (5, 6):
        release *= P3
    elif month in (7, 8):
        release *= P4
    elif month in (9, 10):
        release *= P5
    elif month in (11, 12):
        release *= P6
        

    counter_for_tharthar_mean_30days +=1;
    return release, counter_for_tharthar_mean_30days
