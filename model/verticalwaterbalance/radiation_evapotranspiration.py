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
#
# Potential evapotranspiration can be computed with the following
# methods, selected for the run via 'pet_method' in the .json Setup file:
# 0 = Priestley-Taylor   (Müller Schmied et al. 2021, default)
# 1 = Penman-Monteith FAO56    ( Allen et al. 1998)
# 2 = Hargreaves-Samani  (Hargreaves & Samani 1985)
# 3 = Jensen-Haise       (Jensen & Haise 1963)
# 4 = Koeppen subdivision (method chosen per climate zone after Pimentel et al. 2023)
# 5 = Priestley-Taylor parameterized (locally parameterized PT alpha values after Aschonitis et al. 2017)
# 6 = Penman-Monteith complete (land-cover-specific aerodynamic resistance and
#     LAI-based dynamic surface resistance in the full Monteith form,
#     Allen et al. 1998 Eqs. 3-4)
# =============================================================================

import numpy as np
from numba import njit


@njit(cache=True)
def calculate_net_radiation(temperature, down_shortwave_radiation,
                            down_longwave_radiation, snow_water_storage,
                            snow_albedo_thresh, openwater_albedo,
                            snow_albedo, albedo, emissivity, x, y):
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
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    net_radiation : float
        Net radiation  according to Müller Schmied et al., 2016., Units: [Wm−2]
    openwater_net_radiation : float
       Open water radiation  according to Müller Schmied et al., 2016.,
       Units: [Wm−2]

    """

    # Index (x, y) to  print out varibales of interest
    # e.g.  if x==65 and y==137: print(albedo)

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
def priestley_taylor_pet(temperature, pt_coeff_humid_arid,
                         net_radiation, openwater_net_radiation,
                         x, y):
    """
    Potential evapotranspiration based on Priestly-Taylor algorithm

    Parameters
    ----------
    temperature : float
        Daily air tempeature, Units : [K]
    pt_coeff_humid_arid : flaot
        Priestley-Taylor coefficient  for humid and arid cells (alpha), Units: [-]
    net_radiation : float
        Net radiation  according to Müller Schmied et al., 2016., Units: [Wm−2]
    openwater_net_radiation : float
        Open water radiation  according to Müller Schmied et al., 2016.,
        Units: [Wm−2]
     x : int
         Latitude index of cell
     y : int
         Longitude index of cell

    Returns
    -------
    potential_evap : float
        Potential evapotranspiration, Units: [mm/day]
    openwater_pot_evap : float
        Open water potential evapotranspiration, Units: [mm/day]

    """
    # Index (x, y) to  print out varibales of interest
    # e.g.  if x==65 and y==137: print(net_radiation)
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


@njit(cache=True)
def penman_monteith_fao56(temperature,
                        net_radiation, openwater_net_radiation,
                        windspeed, relative_humidity,
                        x, y):
    """
    Potential evapotranspiration based on Penman-Monteith equation
    following FAO-56 reference evapotranspiration standard.

    Reference: Allen et al. (1998), FAO Irrigation and Drainage Paper No. 56.
    Aerodynamic and surface resistance terms are standardized to a reference
    grass surface (height 0.12 m, surface resistance 70 s m-1), following
    Allen et al. (1998). Net radiation is computed using land-cover-specific
    albedo and emissivity values from WaterGAP (Müller Schmied et al. 2021),
    consistent with the existing radiation calculation.

    Parameters
    ----------
    temperature : float
        Daily mean air temperature, Units: [K]
    net_radiation : float
        Net radiation according to Müller Schmied et al., 2016.,
        Units: [W m-2]
    openwater_net_radiation : float
        Open water net radiation according to Müller Schmied et al., 2016.,
        Units: [W m-2]
    windspeed : float
        Near-surface wind speed at 10 m height (sfcWind), Units: [m s-1]
    relative_humidity : float
        Near-surface relative humidity, Units: [%]
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    potential_evap : float
        Potential evapotranspiration, Units: [mm/day]
    openwater_pot_evap : float
        Open water potential evapotranspiration, Units: [mm/day]

    """
    # Index (x, y) to print out variables of interest
    # e.g. if x==65 and y==137: print(net_radiation)

    # =====================================================================
    # Convert temperatures to degrees Celsius
    # =====================================================================
    covert_to_degree = 273.15
    conv_temperature = temperature - covert_to_degree

    # =====================================================================
    # Slope of the saturation vapour pressure curve, Units: kPa °C-1
    # Eq. 13 in Allen et al. (1998), consistent with Müller Schmied et al.
    # (2021) and the existing Priestley-Taylor implementation
    # =====================================================================
    slope_of_sat_num = 4098 * (0.6108 * np.exp((17.27 * conv_temperature) /
                                                (conv_temperature + 237.3)))
    slope_of_sat_den = (conv_temperature + 237.3) ** 2
    slope_of_sat = slope_of_sat_num / slope_of_sat_den

    # =====================================================================
    # Psychrometric constant, Units: kPa °C-1
    # Consistent with Müller Schmied et al. (2021) and the existing
    # Priestley-Taylor implementation
    # =====================================================================
    # Atmospheric pressure, Units: kPa
    atm_pressure = 101.3

    # Latent heat of vaporization, Units: MJ kg-1
    latent_heat = np.where(conv_temperature > 0,
                           (2.501 - (0.002361 * conv_temperature)), 2.835)

    # Psychrometric constant, Units: kPa °C-1
    psy_const = (0.0016286 * atm_pressure) / latent_heat

    # =====================================================================
    # Wind speed at 2 m height, Units: m s-1
    # Convert 10 m wind to 2 m for the reference crop, via log. wind-profile
    # Allen et al. (1998) Eq. 47 for z = 10 m:
    # u2 = u10 * 4.87 / ln(67.8*10 - 5.42) = u10 * 0.748
    # =====================================================================
    u2 = windspeed * 0.748

    # =====================================================================
    # Saturation vapour pressure, Units: kPa
    # =====================================================================
    es = 0.6108 * np.exp((17.27 * conv_temperature) /
                              (conv_temperature + 237.3))

    # =====================================================================
    # Actual vapour pressure from relative humidity, Units: kPa
    # Following Allen et al. (1998), Eq. 17
    # =====================================================================
    ea = (relative_humidity / 100.0) * es

    # Vapour pressure deficit, Units: kPa
    vpd = es - ea
    # Ensure VPD is not-negative
    vpd = np.where(vpd < 0, 0, vpd)

    # =====================================================================
    # Penman-Monteith Potential evapotranspiration (mm/day)
    # FAO-56 reference evapotranspiration following Allen et al. (1998), Eq. 6
    # Soil heat flux G is assumed negligible at daily timestep
    # =====================================================================
    # Convert net radiation from W m-2 to mm/day
    net_radiation_mmday = (net_radiation * 0.0864) / latent_heat

    # Numerator: radiation term + aerodynamic term for grass (FAO-56 ETo)
    # numerator = (slope_of_sat * net_radiation_mmday +
    #            psy_const * (900.0 / (conv_temperature + 273.0)) * u2 * vpd)

    # Numerator: radiation term + aerodynamic term tall ref crop (ASCE ETr)
    numerator = (slope_of_sat * net_radiation_mmday +
                 psy_const * (1600.0 / (conv_temperature + 273.0)) * u2 * vpd)

    # Denominator grass (FAO-56 ETo)
    # denominator = slope_of_sat + psy_const * (1.0 + 0.34 * u2)

    # Denominator tall ref (ASCE ETr)
    denominator = slope_of_sat + psy_const * (1.0 + 0.38 * u2)

    # Potential evapotranspiration, Units: mm/day
    potential_evap = numerator / denominator

    # Accounting for negative net radiation and setting PET to zero
    potential_evap = np.where(net_radiation <= 0, 0, potential_evap)

    # =====================================================================
    # Penman-Monteith open water potential evapotranspiration (mm/day)
    # =====================================================================
    openwater_net_radiation_mmday = (openwater_net_radiation * 0.0864) / \
        latent_heat

    openwater_numerator = (slope_of_sat * openwater_net_radiation_mmday +
                           psy_const * (900.0 / (conv_temperature + 273.0)) *
                           u2 * vpd)

    openwater_pot_evap = openwater_numerator / denominator

    # Accounting for negative net radiation and setting PET to zero
    openwater_pot_evap = np.where(openwater_net_radiation <= 0, 0,
                                  openwater_pot_evap)

    return potential_evap, openwater_pot_evap


@njit(cache=True)
def hargreaves_samani_pet(temperature, min_temperature, max_temperature,
                          day_of_year, x, y):
    """
    Potential evapotranspiration based on the Hargreaves-Samani from
    Hargreaves & Samani (1985)

    Extraterrestrial radiation Ra is computed geometrically from latitude
    (derived from the grid cell row index x) and day of year, following
    Equations 21-27 in Allen et al. (1998).

    Parameters
    ----------
    temperature : float
        Daily mean air temperature, Units: [K]
    min_temperature : float
        Daily minimum air temperature, Units: [K]
    max_temperature : float
        Daily maximum air temperature, Units: [K]
    day_of_year : int
        Julian day of the year (1 = 1 January, 365 = 31 December),
        Units: [days]
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    potential_evap : float
        Potential evapotranspiration, Units: [mm/day]
    openwater_pot_evap : float
        Open water potential evapotranspiration, Units: [mm/day]

    """
    # Index (x, y) to print out variables of interest
    # e.g. if x==65 and y==137: print(temperature)

    # =====================================================================
    # Convert temperatures to degrees Celsius
    # =====================================================================
    covert_to_degree = 273.15
    conv_temperature = temperature - covert_to_degree
    conv_min_temperature = min_temperature - covert_to_degree
    conv_max_temperature = max_temperature - covert_to_degree

    # =====================================================================
    # Latent heat of vaporization, Units: MJ kg-1
    # Consistent with Müller Schmied et al. (2021) and the existing
    # Priestley-Taylor implementation
    # =====================================================================
    latent_heat = np.where(conv_temperature > 0,
                           (2.501 - (0.002361 * conv_temperature)), 2.835)

    # =====================================================================
    # Latitude derived from row index x
    # WaterGAP uses a 0.5 global grid, where row x=0 is equivalent to the
    # northernmost cell centred at 89.75 N, x=359 to 89.75 S.
    # Latitude in degrees: 90 - (x + 0.5) * 0.5
    # =====================================================================
    latitude_deg = 90.0 - (x + 0.5) * 0.5

    # Converted to radians following Eq. 22 in Allen et al. (1998)
    phi = (np.pi / 180.0) * latitude_deg

    # =====================================================================
    # Extraterrestrial radiation Ra, Units: MJ m-2 day-1
    # Following Equations 21-27 in Allen et al. (1998)
    # =====================================================================

    # Solar constant, Units: MJ m-2 min-1 (Allen et al. 1998)
    gsc = 0.0820

    # Inverse relative distance Earth-Sun, (Eq. 23 in Allen et al. (1998))
    dr = 1.0 + 0.033 * np.cos((2.0 * np.pi / 365.0) * day_of_year)

    # Solar declination, Units: rad, (Eq. 24 in Allen et al. (1998))
    delta = 0.409 * np.sin((2.0 * np.pi / 365.0) * day_of_year - 1.39)

    # Sunset hour angle, Units: rad, (Eq. 25 in Allen et al. (1998))
    # Argument clipped to [-1, 1] to avoid arccos domain errors at polar
    # latitudes (above 55 degrees N/S) where Ra equations have limited
    # validity (Allen et al. 1998)
    arccos_arg = -np.tan(phi) * np.tan(delta)
    arccos_arg = min(max(arccos_arg, -1.0), 1.0)
    omega_s = np.arccos(arccos_arg)

    # Extraterrestrial radiation Units: MJ m-2 day-1, Eq. 21 in Allen et al. (1998)
    ra = ((24.0 * 60.0) / np.pi) * gsc * dr * (
        omega_s * np.sin(phi) * np.sin(delta)
        + np.cos(phi) * np.cos(delta) * np.sin(omega_s)
    )

    # Ra must be non-negative
    ra = max(ra, 0.0)

    # Convert Ra from MJ m-2 day-1 to mm day-1 equivalent
    ra_mm = ra / latent_heat

    # =====================================================================
    # Temperature range, Units: K,
    # clipped to zero to avoid sqrt of negative values
    # =====================================================================
    temp_range = conv_max_temperature - conv_min_temperature
    temp_range = max(temp_range, 0.0)

    # =====================================================================
    # Hargreaves-Samani potential evapotranspiration (mm/day)
    # ETpot = 0.0023 * Ra * (Tmean + 17.8) * sqrt(Tmax - Tmin)
    # Hargreaves & Samani (1985)
    # =====================================================================
    potential_evap = (0.0023 * ra_mm
                      * (conv_temperature + 17.8)
                      * np.sqrt(temp_range))

    # Avoid negative evapotranspiration values
    potential_evap = np.where(potential_evap <= 0, 0,
                                  potential_evap)

    # =====================================================================
    # Open water potential evapotranspiration (mm/day)
    # HS has no representation of surface radiation dynamics,
    # therefore, Open water PET is set to land surface PET
    # =====================================================================
    openwater_pot_evap = potential_evap

    return potential_evap, openwater_pot_evap


@njit(cache=True)
def jensen_haise_pet(temperature, down_shortwave_radiation, x, y):
    """
    Potential evapotranspiration based on the Jensen-Haise algorithm from
    Jensen & Haise (1963)

    Driven by incoming shortwave radiation and mean air temperature, without
    any representation of surface radiation dynamics (albedo, longwave).

    Parameters
    ----------
    temperature : float
        Daily mean air temperature, Units: [K]
    down_shortwave_radiation : float
        Downward shortwave radiation, Units: [W m-2]
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    potential_evap : float
        Potential evapotranspiration, Units: [mm/day]
    openwater_pot_evap : float
        Open water potential evapotranspiration, Units: [mm/day]

    """
    # Index (x, y) to print out variables of interest
    # e.g. if x==65 and y==137: print(temperature)

    # =====================================================================
    # Convert temperature to degrees Celsius
    # =====================================================================
    covert_to_degree = 273.15
    conv_temperature = temperature - covert_to_degree

    # =====================================================================
    # Latent heat of vaporization, Units: MJ kg-1
    # Consistent with Müller Schmied et al. (2021) and the existing
    # Priestley-Taylor implementation
    # =====================================================================
    latent_heat = np.where(conv_temperature > 0,
                           (2.501 - (0.002361 * conv_temperature)), 2.835)

    # =====================================================================
    # Convert shortwave radiation from W m-2 to mm/day equivalent
    # (R_s / l_h), consistent with the existing radiation conversion
    # =====================================================================
    shortwave_radiation_mmday = \
        (down_shortwave_radiation * 0.0864) / latent_heat

    # =====================================================================
    # Jensen-Haise potential evapotranspiration (mm/day)
    # ETpot = (0.025 * Tmean + 0.08) * R_s / l_h
    # Jensen & Haise (1963)
    # =====================================================================
    potential_evap = ((0.025 * conv_temperature + 0.08)
                      * shortwave_radiation_mmday)

    # Avoid negative evapotranspiration values
    potential_evap = np.where(potential_evap <= 0, 0,
                                  potential_evap)

    # =====================================================================
    # Open water potential evapotranspiration (mm/day)
    # Jensen-Haise has no representation of surface radiation dynamics,
    # therefore, Open water PET is set to land surface PET
    # =====================================================================
    openwater_pot_evap = potential_evap

    return potential_evap, openwater_pot_evap


@njit(cache=True)
def penman_monteith_complete(temperature,
                             net_radiation, openwater_net_radiation,
                             windspeed, relative_humidity, land_cover,
                             leaf_area_index,
                             z0m_lut, d0_lut, z0h_lut, rs_lut,
                             x, y):
    """
    Potential evapotranspiration based on the complete (land-cover-specific)
    Penman-Monteith equation in its full Monteith form.

    In contrast to penman_monteith_pet (FAO-56 grass/tall reference with the
    lumped 900/0.34 coefficients), this method uses explicit aerodynamic and
    surface resistances per IGBP land cover class. Aerodynamic resistance is
    derived from land-cover-specific roughness lengths (z0m, z0h) and
    zero-plane displacement height (d0) following Allen et al. (1998), Eq. 4.
    To keep the aerodynamic formulation valid over tall canopies (displacement
    heights exceeding the 10 m forcing height), the 10 m wind speed is
    extrapolated to a 50 m blending height with a neutral logarithmic wind
    profile before the resistance is evaluated. Surface resistance is derived
    dynamically from the current leaf area index following FAO-56
    (rs = r_l / (0.5 * LAI), single-leaf stomatal resistance r_l = 100 s m-1);
    for sparsely vegetated or dormant cells (LAI -> 0) it falls back to the
    fixed land-cover-specific bulk resistance from the look-up table. Open
    water evaporation uses open-water roughness (look-up index 0) and zero
    surface resistance (free water surface), so that the Penman-Monteith
    reduces to the Penman equation.

    Reference: Allen et al. (1998), FAO Irrigation and Drainage Paper No. 56,
    Eqs. 3 and 4 (Monteith form). Net radiation is computed using
    land-cover-specific albedo and emissivity from WaterGAP
    (Müller Schmied et al. 2021), consistent with the existing radiation
    calculation.

    Parameters
    ----------
    temperature : float
        Daily mean air temperature, Units: [K]
    net_radiation : float
        Net radiation according to Müller Schmied et al., 2016.,
        Units: [W m-2]
    openwater_net_radiation : float
        Open water net radiation according to Müller Schmied et al., 2016.,
        Units: [W m-2]
    windspeed : float
        Near-surface wind speed at 10 m height (sfcWind), Units: [m s-1]
    relative_humidity : float
        Near-surface relative humidity, Units: [%]
    land_cover : float
        IGBP land cover class of the cell (WaterGAP code), Units: [-]
    leaf_area_index : float
        Current daily leaf area index of the cell, used to derive the dynamic
        surface resistance, Units: [-]
    z0m_lut : array
        Look-up table of roughness length for momentum per land cover class
        (index = land cover code, index 0 = open water), Units: [m]
    d0_lut : array
        Look-up table of zero-plane displacement height per land cover class,
        Units: [m]
    z0h_lut : array
        Look-up table of roughness length for heat/vapour per land cover
        class, Units: [m]
    rs_lut : array
        Look-up table of bulk surface resistance per land cover class,
        Units: [s m-1]
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    potential_evap : float
        Potential evapotranspiration, Units: [mm/day]
    openwater_pot_evap : float
        Open water potential evapotranspiration, Units: [mm/day]

    """
    # Index (x, y) to print out variables of interest
    # e.g. if x==65 and y==137: print(net_radiation)

    # =====================================================================
    # Convert temperature to degrees Celsius
    # =====================================================================
    covert_to_degree = 273.15
    conv_temperature = temperature - covert_to_degree

    # =====================================================================
    # Slope of the saturation vapour pressure curve, Units: kPa °C-1
    # Eq. 13 in Allen et al. (1998), consistent with the existing PET methods
    # =====================================================================
    slope_of_sat_num = 4098 * (0.6108 * np.exp((17.27 * conv_temperature) /
                                                (conv_temperature + 237.3)))
    slope_of_sat_den = (conv_temperature + 237.3) ** 2
    slope_of_sat = slope_of_sat_num / slope_of_sat_den

    # =====================================================================
    # Psychrometric constant, Units: kPa °C-1
    # Consistent with the existing Priestley-Taylor implementation
    # =====================================================================
    # Atmospheric pressure, Units: kPa
    atm_pressure = 101.3

    # Latent heat of vaporization, Units: MJ kg-1
    latent_heat = np.where(conv_temperature > 0,
                           (2.501 - (0.002361 * conv_temperature)), 2.835)

    # Psychrometric constant, Units: kPa °C-1
    psy_const = (0.0016286 * atm_pressure) / latent_heat

    # =====================================================================
    # Saturation and actual vapour pressure and deficit, Units: kPa
    # Allen et al. (1998), Eqs. 11 and 17
    # =====================================================================
    es = 0.6108 * np.exp((17.27 * conv_temperature) /
                         (conv_temperature + 237.3))
    ea = (relative_humidity / 100.0) * es
    vpd = es - ea
    # Ensure VPD is non-negative
    vpd = np.where(vpd < 0, 0, vpd)

    # =====================================================================
    # Mean atmospheric density at constant pressure, Units: kg m-3
    # Allen et al. (1998), Annex 3, using the virtual temperature
    # approximation Tkv ~ 1.01 * T and specific gas constant
    # R = 0.287 kJ kg-1 K-1
    # =====================================================================
    air_density = atm_pressure / (1.01 * temperature * 0.287)

    # Specific heat of moist air at constant pressure, Units: MJ kg-1 °C-1
    spec_heat = 1.013e-3

    # =====================================================================
    # Wind speed at the blending height, Units: m s-1
    # The 10 m forcing wind is extrapolated to a 50 m blending height above
    # all canopies with a neutral logarithmic profile (reference roughness
    # 0.03 m). This keeps (blending_height - d0) positive for tall canopies
    # (displacement heights up to ~21 m), where the 10 m level lies inside
    # the canopy and the aerodynamic resistance would otherwise be undefined.
    # =====================================================================
    blending_height = 50.0
    reference_roughness = 0.03
    wind_blend = windspeed * (np.log(blending_height / reference_roughness) /
                              np.log(10.0 / reference_roughness))
    # Avoid division by zero in the aerodynamic resistance under calm winds
    wind_blend = np.where(wind_blend < 0.01, 0.01, wind_blend)

    # von Karman constant squared, Units: [-]
    von_karman_sq = 0.41 ** 2

    # =====================================================================
    # Land surface potential evapotranspiration (mm/day)
    # Full Penman-Monteith (Monteith form), Allen et al. (1998), Eq. 3, with
    # land-cover-specific aerodynamic (Eq. 4) and surface resistance.
    # =====================================================================
    # Look up land-cover-specific aerodynamic parameters (index = land cover
    # code)
    landcover_index = int(land_cover)
    z0m = z0m_lut[landcover_index]
    d0 = d0_lut[landcover_index]
    z0h = z0h_lut[landcover_index]

    # Dynamic bulk surface resistance from the current leaf area index,
    # FAO-56 (Allen et al. 1998): rs = r_l / (0.5 * LAI), with a single-leaf
    # stomatal resistance r_l = 100 s m-1. For sparsely vegetated or dormant
    # cells (LAI -> 0, e.g. barren, snow, open water, leaf-off deciduous) the
    # dynamic term is unbounded, so the fixed land-cover-specific bulk
    # resistance from the look-up table is used instead.
    leaf_resistance = 100.0
    active_leaf_area_index = 0.5 * leaf_area_index
    if active_leaf_area_index > 0.1:
        surface_resistance = leaf_resistance / active_leaf_area_index
    else:
        surface_resistance = rs_lut[landcover_index]

    # Aerodynamic resistance at the blending height, Units: s m-1
    # Allen et al. (1998), Eq. 4
    aero_resistance = (np.log((blending_height - d0) / z0m) *
                       np.log((blending_height - d0) / z0h)) / \
                      (von_karman_sq * wind_blend)

    # Convert net radiation from W m-2 to MJ m-2 day-1
    net_radiation_mjday = net_radiation * 0.0864

    # Radiation and aerodynamic terms of the numerator, Units: MJ m-2 day-1
    # The aerodynamic term is scaled by 86400 s day-1 to convert the
    # per-second resistance term to a daily flux, consistent with the
    # per-day radiation term.
    radiation_term = slope_of_sat * net_radiation_mjday
    aerodynamic_term = (86400.0 * air_density * spec_heat * vpd /
                        aero_resistance)

    denominator = slope_of_sat + psy_const * \
        (1.0 + surface_resistance / aero_resistance)

    # Latent heat flux, Units: MJ m-2 day-1
    latent_heat_flux = (radiation_term + aerodynamic_term) / denominator

    # Potential evapotranspiration, Units: mm/day
    potential_evap = latent_heat_flux / latent_heat

    # Accounting for negative net radiation and setting PET to zero
    potential_evap = np.where(net_radiation <= 0, 0, potential_evap)

    # =====================================================================
    # Open water potential evapotranspiration (mm/day)
    # Open water roughness (look-up index 0) and zero surface resistance,
    # so the Penman-Monteith reduces to the Penman open water equation.
    # =====================================================================
    ow_z0m = z0m_lut[0]
    ow_d0 = d0_lut[0]
    ow_z0h = z0h_lut[0]
    ow_surface_resistance = rs_lut[0]

    ow_aero_resistance = (np.log((blending_height - ow_d0) / ow_z0m) *
                          np.log((blending_height - ow_d0) / ow_z0h)) / \
                         (von_karman_sq * wind_blend)

    openwater_net_radiation_mjday = openwater_net_radiation * 0.0864

    ow_radiation_term = slope_of_sat * openwater_net_radiation_mjday
    ow_aerodynamic_term = (86400.0 * air_density * spec_heat * vpd /
                           ow_aero_resistance)

    ow_denominator = slope_of_sat + psy_const * \
        (1.0 + ow_surface_resistance / ow_aero_resistance)

    ow_latent_heat_flux = (ow_radiation_term + ow_aerodynamic_term) / \
        ow_denominator

    openwater_pot_evap = ow_latent_heat_flux / latent_heat

    # Accounting for negative net radiation and setting PET to zero
    openwater_pot_evap = np.where(openwater_net_radiation <= 0, 0,
                                  openwater_pot_evap)

    return potential_evap, openwater_pot_evap