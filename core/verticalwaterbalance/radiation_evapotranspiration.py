# -*- coding: utf-8 -*-

# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================


"""Radiation and Evapotranspiration."""

# =============================================================================
# This module computes radiation components for all cells based on 'Evaluation
# of Radiation Components in a Global Freshwater Model with Station-Based
# Observations'.Müller Schmied et al., 2016b and evapotranspiration for all
# cells based on "the global water resources and use model WaterGAP v2.2d:
# model description and evaluation." Müller Schmied et al 2021.
# Priestly-Taylor potential evapotranspiration is currenlty the default
# evapotranspiration algorithm
# =============================================================================

import numpy as np
from numba import njit


@njit(cache=True)
def compute_radiation(temperature, down_shortwave_radiation,
                      down_longwave_radiation, snow_water_storage,
                      snow_albedo_thresh, openwater_albedo,
                      snow_albedo, albedo, emissivity):
    """
    Compute Radition  according to Müller Schmied et al., 2016.

    (doi:10.3390/w8100450)

    Parameters
    ----------
    temperature : float
        Daily air tempeature, Units : [K]
    down_shortwave_radiation : float
        Downward shortwave radiation  Units: [Wm−2]
    down_longwave_radiation : float
        Downward longwave radiation  Units: [Wm−2]
    snow_water_storage : float
        Daily snow water storage (for shortwave radiation),  Units: [mm]
    snow_albedo_thresh : float
        Threshold to use snow albedo (3mm), Units: [mm]
    openwater_albedo : float
       Open water albedo, Units: [-]
    snow_albedo : float
       Snow albedo,  Units: [-]
    albedo : float
        Albedo per landcover (Müller Schmied et al 2014, Table A2), Units: [-]
    emissivity : float
        Emisivity per landcover (Müller Schmied et al 2014, Table A2),
        Units: [-]

    Returns
    -------
    net_radiation : float
        Net radiation  according to Müller Schmied et al., 2016., Units: [Wm−2]
    openwater_net_radiation : float
       Open water radiation  according to Müller Schmied et al., 2016.,
       Units: [Wm−2]

    """
    # snow_water_storage > 3mm, snow abledo is used for shortwave
    # radiation calulation
    albedo = np.where(snow_water_storage > snow_albedo_thresh, snow_albedo,
                      albedo)

    # Net shortwave radiation is based on Eq. 1 in
    # Müller Schmied et al., 2016b,  Units: Wm−2
    net_shortwave_radiation = down_shortwave_radiation * (1-albedo)

    # Upward shortwave radiation is based on Eq. 2 in
    # Müller Schmied et al., 2016b, Units: Wm−2
    upward_shortwave_radiation = down_shortwave_radiation - \
        net_shortwave_radiation

    # =====================================================================
    #  Net longwave radiation and upward longwave radiation (Wm−2)
    # =====================================================================
    # Stefan_Boltzmann_constant (5.67 × 10−8 (Wm−2·K−4))
    stefan_boltzmann_constant = 5.67e-08  # (Müller Schmied et al., 2016)

    # Upward longwave radiation is based on Eq. 3 in
    # Müller Schmied et al., 2016b, Units: (Wm−2)
    up_longwave_radiation = \
        emissivity * (stefan_boltzmann_constant * np.power(temperature, 4))

    # Net longwave radiation is based on Eq. 4 in
    # Müller Schmied et al., 2016b,  Unit: (Wm−2)
    net_longwave_radiation = down_longwave_radiation - up_longwave_radiation

    # =====================================================================
    # Net radiation (Wm−2) calulation
    # =====================================================================
    # Net radiation is based on Eq. 5 in Müller Schmied et al., 2016b,
    net_radiation = net_shortwave_radiation + net_longwave_radiation

    # =====================================================================
    # open water net radiation (Wm−2) calulation
    # =====================================================================
    openwater_net_shortwave_radiation = down_shortwave_radiation * \
        (1 - openwater_albedo)
    openwater_net_radiation = openwater_net_shortwave_radiation + \
        net_longwave_radiation

    return net_radiation, openwater_net_radiation


@njit(cache=True)
def priestley_taylor(temperature, pt_coeff_humid_arid, 
                     net_radiation, openwater_net_radiation,
                     x, y ):
    """
    Compute Priestly-Taylor potential evapotranspiration.

    Parameters
    ----------
    temperature : float
        Daily air tempeature, Units : [K]
    pt_coeff_humid_arid : TYPE
        Priestley-Taylor coefficient  for humid and arid cells (alpha), Units: [-]
    net_radiation : float
        Net radiation  according to Müller Schmied et al., 2016., Units: [Wm−2]
    openwater_net_radiation : float
        Open water radiation  according to Müller Schmied et al., 2016.,
        Units: [Wm−2]

    Returns
    -------
    potential_evap : float
        Potential evapotranspiration, Units: [mm/day]
    openwater_pot_evap : float
        Open water potential evapotranspiration, Units: [mm/day]

    """
    # =====================================================================
    # Slope of the saturation kPa°C-1
    # =====================================================================
    # Converting temperature to degrees celcius
    covert_to_degree = 273.15
    conv_temperature = temperature - covert_to_degree

    # Actual name: Slope of the saturation, Units: kPa°C-1
    slope_of_sat_num = 4098 * (0.6108 * np.exp((17.27 * conv_temperature) /
                                               (conv_temperature + 237.3)))

    slope_of_sat_den = (conv_temperature + 237.3)**2

    slope_of_sat = slope_of_sat_num / slope_of_sat_den

    # =====================================================================
    # Psychrometric constant  kPa°C-1
    # =====================================================================
    # Actual name: Atmospheric pressure,	Units: kPa
    atm_pressure = 101.3

    # Actual name: Latent heat,	Units: MJkg-1
    latent_heat = np.where(conv_temperature > 0,
                           (2.501 - (0.002361 * conv_temperature)), 2.835)

    #  Actual name: Psychrometric constant	Unit kPa°C-1
    psy_const = (0.0016286 * atm_pressure) / latent_heat

    # =====================================================================
    #  Priestley-Taylor Potential evapotranspiration (mm/day)
    #  (Eq. 7 in Müller Schmied et al 2021.)
    # =====================================================================
    # Priestley-Taylor coefficient  for potential evapotranspiration(α)
    # Following Shuttleworth (1993), α is set to 1.26 in humid
    # and to 1.74 in (semi)arid cells
    # Humid-arid calssification based on Müller Schmied et al. 2021

    # Coverting net radiation to mm/day
    # Note!!!, I deliberately did not attach "self"  here so I dont
    # convert the final net radiation output to  mm/day. 
    net_radiation = (net_radiation * 0.0864) / latent_heat

    # Actual name: Potential evapotranspiration,	Units:  mmd-1
    potential_evap = pt_coeff_humid_arid * ((slope_of_sat * net_radiation)
                                             / (slope_of_sat + psy_const))

    # Accounting for negative net radiation and setting them to zero
    potential_evap = np.where(net_radiation <= 0, 0, potential_evap)

    # =====================================================================
    # Priestley-Taylor open water potential evapotranspiration (mm/day)
    # =====================================================================
    # Coverting net radiation to mm/day
    openwater_net_radiation = \
        (openwater_net_radiation * 0.0864) / latent_heat

    # Actual name: Open water potential evapotranspiration,	Units:  mmd-1
    openwater_pot_evap = \
       pt_coeff_humid_arid * ((slope_of_sat * openwater_net_radiation) /
                                (slope_of_sat + psy_const))

    # Accounting for negative net radiation and setting them to zero
    openwater_pot_evap = np.where(openwater_net_radiation <= 0, 0,
                                  openwater_pot_evap)
    return potential_evap, openwater_pot_evap
