# -*- coding: utf-8 -*-
"""
Created on Sun Jan  1 21:04:26 2023

@author: nyenah
"""
import numpy as np
from numba import njit


@njit(cache=True)
def river_velocity(rout_order, routflow_looper,
                   river_storage, river_length, river_bottom_width,
                   roughness, roughness_multiplier, river_slope, ):
    """
    Compute river velocity for grid cells.

    Parameters
    ----------
    rout_order : array
        Routing order of cells
    routflow_looper : int
        looper that goes through the routing order.
    river_storage : array
        DESCRIPTION.
    river_length : TYPE
        DESCRIPTION.
    river_bottom_width : TYPE
        DESCRIPTION.
    roughness : TYPE
        DESCRIPTION.
    roughness_multiplier : TYPE
        DESCRIPTION.
    river_slope : TYPE
        DESCRIPTION.
     : TYPE
        DESCRIPTION.

    Returns
    -------
    river_velocity : TYPE
        DESCRIPTION.
    outflow_constant : TYPE
        DESCRIPTION.

    """
    # Index to  print out varibales of interest
    # e.g  if x==65 and y==137: print(prev_gw_storage)
    x, y = rout_order[routflow_looper]

    # =========================================================================
    # Compute river velocity.
    # =========================================================================
    # Note!!! River velocity is computed in m3/s and later converted to
    # km3/day

    # River cross sectional area is assumed to be a  trapezoidal channel
    # with slope of 0.5 at both sides. Units: m2
    km2_to_m2 = 1e+6
    cross_sectional_area = (river_storage / river_length) * km2_to_m2

    # River depth dependence on river storage is based on section 4.7.3
    # (Eq.34) of (Müller Schmied et al. (2021). Units: m
    km_to_m = 1000
    river_bottom_width = river_bottom_width * km_to_m

    river_depth = (-1/4) * river_bottom_width + \
        np.sqrt(((river_bottom_width**2)/16) + (0.5 * cross_sectional_area))

    # Wetted perimetter and hydraulic radius are calulated assuming a
    # trapezoidal channel with slope of 0.5 at both sides.
    # Both have Units: m
    wetted_perimeter = river_bottom_width + (2.0*river_depth*np.sqrt(5.0))
    hydraulic_radius = cross_sectional_area / wetted_perimeter

    # River velocity (using  Manning–Strickler equation) is based on
    # section 4.7.3 (Eq.32) of (Müller Schmied et al. (2021). Units: m/s
    river_velocity = (1/(roughness_multiplier * roughness)) * np.power(hydraulic_radius, (2/3)) * \
        np.sqrt(river_slope)

    # River velocity is now converted,  Units: km/day
    m_ps_to_km_ps = 86.4
    river_velocity = river_velocity * m_ps_to_km_ps

    # limit  velocity values below  0.00001 to  0.00001
    river_velocity = np.where(river_velocity < 0.00001, 0.00001, river_velocity)

    # Now river velocity is divided by river length to be consitent with
    # the outflow constant of the other surface waterbodies
    # (Global and local lakes and wetlands)

    outflow_constant = river_velocity / river_length
    return river_velocity, outflow_constant


@njit(cache=True)
def river_water_balance(rout_order, routflow_looper,
                        river_storage, river_inflow, outflow_constant,
                        stat_corr_fact,
                        accumulated_unsatisfied_potential_netabs_sw):
    """
    Compute River water balance including storages and fluxes.

    Parameters
    ----------
    rout_order : TYPE
        DESCRIPTION.
    routflow_looper : TYPE
        DESCRIPTION.
    river_storage : TYPE
        DESCRIPTION.
    river_inflow : TYPE
        DESCRIPTION.
    outflow_constant : TYPE
        DESCRIPTION.
    stat_corr_fact : TYPE
        DESCRIPTION.

    Returns
    -------
    river_storage : TYPE
        DESCRIPTION.
    streamflow : TYPE
        DESCRIPTION.

    """
    # Index to  print out varibales of interest
    # e.g  if x==65 and y==137: print(prev_gw_storage)
    x, y = rout_order[routflow_looper]

    #                  ======================================
    #                  ||            River balance         ||
    #                  ======================================
    # Note components of the waterbalance in Equation 30 of Müller Schmied et
    # al. (2021) is calulated as follows. River area is not considered hence
    # river precipitation and evaporation are not considered.
    river_storage_prev = river_storage

    # Note!!! even though river evaporation is not considered, variables are
    # named such that they allow for future consideration of evaporation.

    riverevap_netabs = accumulated_unsatisfied_potential_netabs_sw

    # To get *riverevap_netabs_max*, defined as the maximum value for
    # netabstraction,  the river water balance Eq.30  (section 4.7.1) of Müller
    # Schmied et al. (2021) is differentiated analytically with a timestep of
    # one day. After set this differential to 0 and solve of netabs to get
    # maximum net abstraaction.

    riverevap_netabs_max = river_inflow + \
        ((outflow_constant * river_storage_prev *
         np.exp(-1*outflow_constant))/(1 - np.exp(-1*outflow_constant)))

    if riverevap_netabs > riverevap_netabs_max:
        river_storage = 0

        streamflow = river_inflow + river_storage_prev - riverevap_netabs_max
        if streamflow < 0:
            streamflow = 0

        # There is not enough  storage to satisfy potential net asbraction from
        # suracface water
        if accumulated_unsatisfied_potential_netabs_sw > 0:
            accumulated_unsatisfied_potential_netabs_sw -= accumulated_unsatisfied_potential_netabs_sw * \
                (riverevap_netabs_max / riverevap_netabs)
        else:
            accumulated_unsatisfied_potential_netabs_sw = 0

    else:

        # river water balance Eq.30 (section 4.7.1) of Müller Schmied et al.
        # (2021) is solved analytically with a timestep of one day.
        river_storage = river_storage_prev * np.exp(-1*outflow_constant) + \
            (((river_inflow - riverevap_netabs)
             / outflow_constant) * (1 - np.exp(-1*outflow_constant)))

        streamflow = river_inflow + river_storage_prev - river_storage - \
            riverevap_netabs

        if streamflow < 0:
            streamflow = 0

        # potential net asbraction from suracface water is satified due to
        # available storage
        accumulated_unsatisfied_potential_netabs_sw = 0

    # Apply a staion correction factor which corrects discharge at the grid
    # cell where the gauging station is located
    streamflow *= stat_corr_fact

    return river_storage, streamflow, \
        accumulated_unsatisfied_potential_netabs_sw
