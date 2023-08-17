# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Groundwater balance."""

# =============================================================================
# This module computes groundwater balance, including groundwater storage
# and related fluxes for all grid cells based on section 4.5 of
# (Müller Schmied et al. (2021)).
# The groundwater balance equation is solved analytically for each timestep
# of one day to prevent numerical inaccuracies. This avoids the use of very
# small timesteps which will be computationally expensive and hence lead
# to numerical problems.
# =============================================================================

import numpy as np
from numba import njit
from core.lateralwaterbalance import adapt_netabs_groundwater as adapt_gw_abs


@njit(cache=True)
def compute_groundwater_balance(rout_order, routflow_looper,
                                aridity_or_inlandsink, groundwater_storage,
                                diffuse_gw_recharge,
                                potential_net_abstraction_gw,
                                daily_unsatisfied_pot_nas, gw_dis_coeff,
                                prev_potential_water_withdrawal_sw_irri,
                                prev_potential_consumptive_use_sw_irri,
                                frac_irri_returnflow_to_gw,
                                point_source_recharge=None):
    """
    Compute daily groundwater balance including storages and related fluxes.

    Parameters
    ----------
    rout_order : array
        Routing order of cells
    routflow_looper : int
        looper that goes through the routing order.
    aridiity : string
        Compute groundwater for "Humid" or "Arid" region
    groundwater_storage : array
        Daily groundwater storage, Unit: [km^3]
    diffuse_gw_recharge : array
        Daily difuuse groundwater recharge, Unit: [km^3/day]
    potential_net_abstraction_gw : array
        Potential net abstraction from groundwater, Unit: [km^3/day]
    daily_unsatisfied_pot_nas : array
        Daily unsatisfied water use, Unit: [km^3/day]
    gw_dis_coeff : array
        Groundwater discharge coefficient (Döll et al., 2014)
    point_source_recharge : array
        Sum of all point groundwater recharge from surface waterboides in
        arid regions, Unit: [km^3/day]

    Returns
    -------
    groundwater_storage : array
        Updated daily groundwater storage, Unit: [km^3]

     groundwater_discharge : array
        Updated daily groundwater discharge, Unit: [km^3/day]
    """
    # Index to  print out varibales of interest
    # e.g  if x==65 and y==137: print(prev_gw_storage)
    x, y = rout_order[routflow_looper]

    #                  ======================================
    #                  ||  groundwaterwater balance    ||
    #                  ======================================
    # Note components of the waterbalance in Equation 20 of Müller Schmied et
    # al. (2021) is calulated as follows.

    prev_gw_storage = groundwater_storage

    # =========================================================================
    # Computing net groundwater recharge (netgw_in [km3])  which is defined as
    # diffuse recharge  + point source recharge - net abstraction.
    # =========================================================================
    # Point_source_recharge is only computed for (semi)arid surafce water
    #  bodies but not for  inlank sink or humid regions
    if aridity_or_inlandsink == "humid" or \
            aridity_or_inlandsink == "inland sink":
        point_source_recharge = 0

    netgw_in = diffuse_gw_recharge + point_source_recharge

    # Update net abstraction from groundwater if there is unsatisfied water use
    # from previous time step.
    actual_net_abstraction_gw = \
        np.where(daily_unsatisfied_pot_nas != 0,
                 adapt_gw_abs.
                 update_netabs_gw(potential_net_abstraction_gw,
                                  prev_potential_water_withdrawal_sw_irri,
                                  prev_potential_consumptive_use_sw_irri,
                                  daily_unsatisfied_pot_nas,
                                  frac_irri_returnflow_to_gw,
                                  rout_order, routflow_looper),
                 potential_net_abstraction_gw)

    # Updating net groundwater recharge (netgw_in [km3])
    netgw_in = netgw_in - actual_net_abstraction_gw

    # =========================================================================
    # Computing  daily groundwater storage (km3) and discharge(km3/day)
    # =========================================================================
    # Groundwater balance dS/dt = netgw_in - NAg - k*S is solved analytically
    # for each time step of 1 day to prevent numerical inaccuracies.
    # See in Equation 20 of Müller Schmied et al. (2021)

    current_gw_storage = prev_gw_storage * np.exp(-1 * gw_dis_coeff) +\
        (netgw_in/gw_dis_coeff)*(1-np.exp(-1 * gw_dis_coeff))

    groundwater_discharge = prev_gw_storage - current_gw_storage + netgw_in

    # Recalculate groundwater storage when groundwater discharge=0
    # dS/dt = netgw_in - NAg (without k*S) -> S(t) = S(t-1) + netgw_in

    current_gw_storage = np.where(groundwater_discharge <= 0,
                                  prev_gw_storage + netgw_in,
                                  current_gw_storage)

    groundwater_discharge = np.where(groundwater_discharge <= 0, 0,
                                     groundwater_discharge)
    # if x==119 and y ==424:
    #       print(daily_unsatisfied_pot_nas , potential_net_abstraction_gw, actual_net_abstraction_gw)
    return current_gw_storage, groundwater_discharge
