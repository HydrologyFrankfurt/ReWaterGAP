# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Groundwater  Storage."""

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


@njit(cache=True)
def update_netabs_gw():
    """
    Update net groundwater abstraction.

    Returns
    -------
    int
        DESCRIPTION.

    """
    return 0


@njit(cache=True)
def compute_groundwater_storage(aridity_or_inlandsink, groundwater_storage,
                                diffuse_gw_recharge, cell_area, netabs_gw,
                                remaining_use, land_area_frac, gw_dis_coeff,
                                point_source_recharge=None):
    """
    Compute daily groundwater storage and related fluxes.

    Parameters
    ----------
    aridiity : string
        Compute groundwater for "Humid" or "Arid" region
    groundwater_storage : array
        Daily groundwater storage. Units: [km^3]
    diffuse_gw_recharge : array
        Daily difuuse groundwater recharge. Units: [km^3/day]
    cell_area : array
        Area of a grid cell. Units: [km^2]
    netabs_gw : array
        Net abstraction from groundwater. Units: [km^3/day]
    remainingUse : array
        Daily total unsatisfied water use. Units: [km^3/day]
    land_area_frac : array
        Land area fraction. Units: [%]
    point_source_recharge : array
        Sum of all point groundwater recharge from surface waterboides in
        arid regions. Units: [km^3/day]

    Returns
    -------
    groundwater_storage : array
        Updated daily groundwater storage. Units: [km^3]

     groundwater_discharge : array
        Updated daily groundwater discharge. Units: [km^3/day]
    """
    groundwater_storage_prev = groundwater_storage

    # =========================================================================
    # Computing net groundwater recharge (netgw_in [km3])  which is defined as
    # diffuse recharge  + point source recharge - net abstraction.
    # =========================================================================
    # Point_source_recharge is only computed for arid surafce water bodies.
    # Except arid inlank sink
    if aridity_or_inlandsink == "humid" or \
            aridity_or_inlandsink == "inland sink":
        point_source_recharge = 0

    netgw_in = diffuse_gw_recharge + point_source_recharge

    # Update net abstraction from groundwater if there is unsatisfied water use
    # from previous time step.
    netabs_gw = np.where(remaining_use != 0, update_netabs_gw(), netabs_gw)

    # Updating net groundwater recharge (netgw_in [km3])
    netgw_in = netgw_in-netabs_gw

    # =========================================================================
    # Computing  daily groundwater storage (km3) and discharge(km3/day)
    # =========================================================================
    # Groundwater balance dS/dt = netgw_in - NAg - k*S is solved analytically
    #  for each time step of 1 day to prevent numerical inaccuracies.

    groundwater_storage = groundwater_storage_prev * np.exp(-1 * gw_dis_coeff) +\
        (netgw_in/gw_dis_coeff)*(1-np.exp(-1 * gw_dis_coeff))

    groundwater_discharge = \
        groundwater_storage_prev - groundwater_storage + netgw_in

    # Recalculate groundwater storage when groundwater discharge=0
    # dS/dt = netgw_in - NAg (without k*S) -> S(t) = S(t-1) + netgw_in

    groundwater_storage = np.where(groundwater_discharge <= 0,
                                   groundwater_storage_prev + netgw_in,
                                   groundwater_storage)

    groundwater_discharge = np.where(groundwater_discharge <= 0, 0,
                                     groundwater_discharge)

    return groundwater_storage, groundwater_discharge
