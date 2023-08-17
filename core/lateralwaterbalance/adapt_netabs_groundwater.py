# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Update Ground Water Abstraction."""

from numba import njit
import sys

# This module adapts potential net ground water abstraction due to the ff:
# 1. Less water is available in surface water for irrigation and
# 2. Due to delayed use more water is abstarcted from surface water for
# irrigation than demanded.

# =============================================================================
# In the computation of potential_net_abstraction_gw in GWSWUSE(model for
# computing net abstraction for ground and surface water), it is assumed that,
# total demand for irrigation by surface water can be fulfilled by the water
# available in surface water bodies including the river. As net abstractions
# from groundwater are a function of the return flows of irrigation with
# surface water, the potential net abstraction from groundwater
# (potential_net_abstraction_gw) needs to be adapted.

# potential_net_abstraction_gw is adapted if, for each cell and time step:
# 1. there is less water for irrigation in surface water (i.e., not all demand for net
# abstractions from surface water can be fulfilled even after spatial
# redistribution) or
# 2. if, due to the delayed water use option, more surface water is abstracted
# for irrigation than demanded on this day.

# ***Note !!!: It is assumed in WGHM that the satisfaction of irrigation
# demands is given the lowest priority and is fulfilled after all
# non-irrigation demands have been met.
# =============================================================================

# To adapt potential_net_abstraction_gw for the current time step(t), the daily
# unsatisfied net abstraction from surface water (daily_unsatisfied_pot_nas)
# from the  previous  time step(t-1) is used.

# This daily_unsatisfied_pot_nas(t-1) is calculated as the difference between
# AccUnNApot,s(t-1) and AccUnNApot,s(t-2). This results in unsatisfied use of
# the time step(t-1)

# If daily_unsatisfied_pot_nas(t-1) is positive, it indicates that less water
# than demanded can be taken from surface water on day t-1
# [potential_net_abstraction_sw(t-1) > actual_net_abstraction_sw(t-1)].
# potential_net_abstraction_gw(t) is adapted. Here, return flow change(t-1)
# from surafce  water for irrigation to ground water is subtsracted from
# potential_net_abstraction_gw(t) to get actual_net_abstraction_gw(t).
# This also means return flow(t) to ground water is decreased.
# [potential_net_abstraction_gw(t) < actual_net_abstraction_gw(t)]

# If daily_unsatisfied_pot_nas(t-1) is zero, then potential_net_abstraction_sw
# (t-1) equals actual_net_abstraction_sw(t-1). potential_net_abstraction_gw(t)
# is not adapted [potential_net_abstraction_gw(t)=actual_net_abstraction_gw(t)]

# If daily_unsatisfied_pot_nas(t-1) is negative, it means that due to delayed
# satisfaction, more surface water is net abstracted on day t-1 than demanded.
# [potential_net_abstraction_sw(t-1) < actual_net_abstraction_sw(t-1)].
# potential_net_abstraction_gw(t) is adapted. Return flow (t) is increased).
# [potential_net_abstraction_gw(t) > actual_net_abstraction_gw(t)]

# The accumulated unsatisfied potential net abstraction from surface water
# (AccUnNApot,s) represents the portion of potential net abstraction that could
# not be satisfied over time. It takes into account not only the unsatisfied
# use of the current time step, but also that of previous time steps.
# (range: AccUnNApot is  >=0 ).
# =============================================================================

@njit(cache=True)
def update_netabs_gw(potential_net_abstraction_gw,
                     potential_water_withdrawal_sw_irri,
                     potential_consumptive_use_sw_irri,
                     daily_unsatisfied_pot_nas,
                     frac_irri_returnflow_to_gw,
                     rout_order, routflow_looper):
    """
    Update net groundwater abstraction.

    Returns
    -------
    int
        DESCRIPTION.

    """
    # Index to  print out varibales of interest
    # e.g  if x==65 and y==137: print(prev_gw_storage)
    x, y = rout_order[routflow_looper]

    if daily_unsatisfied_pot_nas > 0:
        if potential_water_withdrawal_sw_irri > 0:
            # In this case surface water abstraction for irrigation on the previous
            # day was lower than that assumed when computing potential_net_abstraction_sw
            # Return flow to groundwater are decreased and actual_net_abstraction_gw
            # becomes larger than potential_net_abstraction_gw.
            # see documenttion (Delayed use and update potential net ground water
            #  abstraction for derivation of  the following terms. )

            wateruse_eff_irri = potential_consumptive_use_sw_irri / potential_water_withdrawal_sw_irri 
    
            factor = 1 - ((1 - frac_irri_returnflow_to_gw) * (1 - wateruse_eff_irri))
    
            actual_water_withdrawal_irri_sw = \
                (1 / factor)*(potential_water_withdrawal_sw_irri * factor -
                              daily_unsatisfied_pot_nas)
    
            if actual_water_withdrawal_irri_sw <= 0:
                # Abstraction from  surface water for irrigation does  not
                # contribuite to the daily unsatisfied potential net abstraction
                # from surface water
                actual_water_withdrawal_irri_sw = 0
    
                acc_unsat_netabstraction_othersectors = \
                    daily_unsatisfied_pot_nas - (potential_water_withdrawal_sw_irri *
                                                 factor)   # i need to accumulate this 
            else:
                # Abstraction from surface water for irrigation contribuites to all
                # the daily unsatisfied potential net abstraction from surface
                # water since non-irrigation water demand are met first before
                # irigation demand
    
                acc_unsat_netabstraction_sw_irri = daily_unsatisfied_pot_nas   # i need to accumulate this 
    
            # Compute return flow change to adapt actual_net_abstraction_gw
            returnflow_change = (frac_irri_returnflow_to_gw) * (1 - wateruse_eff_irri) *\
                (actual_water_withdrawal_irri_sw - potential_water_withdrawal_sw_irri )
    
            actual_net_abstraction_gw = potential_net_abstraction_gw - returnflow_change
           
        else:
            acc_unsat_netabstraction_othersectors = daily_unsatisfied_pot_nas  # i need to accumulate this 
            actual_net_abstraction_gw = potential_net_abstraction_gw
    
    elif daily_unsatisfied_pot_nas < 0:
        if potential_water_withdrawal_sw_irri > 0: 
            # Redrawal from the surface water for irrigation  means there is contribution from
            # this sector to daily unsatisfied use.
            # Due to delayed satisfaction the actual net abstraction from surface
            # water of the previous day was larger than potential net abstraction
            # from surface water. Return flow to ground water should be increased.
            wateruse_eff_irri = potential_consumptive_use_sw_irri / potential_water_withdrawal_sw_irri 
    
            factor = 1 - (1 - frac_irri_returnflow_to_gw) * (1 - wateruse_eff_irri)
    
            actual_water_abstraction_irri_sw = \
                (1 / factor)*(potential_water_withdrawal_sw_irri * factor -
                              daily_unsatisfied_pot_nas)
            
            
            # Abstraction from surface water for irrigation contribuites to all
            # the daily unsatisfied potential net abstraction from surface
            # water since non-irrigation water demand are met first before
            # irigation demand***
            acc_unsat_netabstraction_sw_irri = daily_unsatisfied_pot_nas  # i need to accumulate this 
    
            # Compute return flow change to adapt actual_net_abstraction_gw
            returnflow_change = (frac_irri_returnflow_to_gw) * (1 - wateruse_eff_irri) *\
                (actual_water_abstraction_irri_sw - potential_water_withdrawal_sw_irri)
    
            actual_net_abstraction_gw = potential_net_abstraction_gw - returnflow_change
            
        else: 
            # No Redrawal from the surface water for irrigation  means all contribution are to daily unsatisfied use 
            # the other sectors. hence no return flow to the ground.
            acc_unsat_netabstraction_othersectors = daily_unsatisfied_pot_nas  # i need to accumulate this 
            actual_net_abstraction_gw = potential_net_abstraction_gw
    else:
        actual_net_abstraction_gw = potential_net_abstraction_gw

    return actual_net_abstraction_gw
