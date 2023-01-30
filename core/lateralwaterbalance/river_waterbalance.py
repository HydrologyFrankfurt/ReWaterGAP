# -*- coding: utf-8 -*-
"""
Created on Sun Jan  1 21:04:26 2023

@author: nyenah
"""
import numpy as np
from numba import njit


@njit(cache=True)
def river_velocity(river_storage, river_length, river_bottom_width,
                   roughness, river_slope):
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
        (((river_bottom_width**2)/16) + (0.5 * cross_sectional_area))**0.5

    # Wetted perimetter and hydraulic radius are calulated assuming a
    # trapezoidal channel with slope of 0.5 at both sides.
    # Both have Units: m
    wetted_perimeter = river_bottom_width + (2.0*river_depth*np.sqrt(5.0))
    hydraulic_radius = cross_sectional_area / wetted_perimeter

    # River velocity (using  Manning–Strickler equation) is based on
    # section 4.7.3 (Eq.32) of (Müller Schmied et al. (2021).
    river_velocity = (1/roughness) * (hydraulic_radius**(2/3)) * \
        np.sqrt(river_slope)

    # River velocity is now converted,  Units: km/day
    m_ps_to_km_ps = 86.4
    river_velocity = river_velocity * m_ps_to_km_ps

    # limit  velocity values below  0.00001(cm/day) to  0.00001 (cm/day)
    river_velocity = np.where(river_velocity < 0.00001, 0.00001, river_velocity)

    # Now river velocity is divided by river length to be consitent with
    # the outflow constant of the other surface waterbodies
    # (Global and local lakes and wetlands)

    outflow_constant = river_velocity / river_length
    return river_velocity, outflow_constant


@njit(cache=True)
def river_water_balance(river_storage, river_inflow, outflow_constant,
                        stat_corr_fact):

    river_storage_prev = river_storage

    # river water balance Eq.30 (section 4.7.1) of Müller Schmied et al. (2021)
    # is solved analytically with a timestep of one day.
    river_storage = river_storage_prev * np.exp(-1*outflow_constant) + \
        (river_inflow / outflow_constant) * (1 - np.exp(-1*outflow_constant))

    streamflow = river_inflow + river_storage_prev - river_storage
    streamflow = np.where(streamflow < 0, 0, streamflow)

    # Apply a staion correction factor which corrects discharge at the grid
    # cell where the gauging station is located
    streamflow *= stat_corr_fact

    return river_storage, streamflow
