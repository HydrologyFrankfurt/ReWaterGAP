# -*- coding: utf-8 -*-

# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================


"""Radiation and Evapotranspiration Class."""

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


class RadiationPotentialEvap:
    """
    Compute radiation and Priestly-Taylor potential evapotranspiration.

    Input Parameters
    ----------------
    climate_forcing : array
        Input forcing to caluclate radiation components and
        Priestly-Taylor potential evapotranspiration
    static_data : array and csv
        Land_cover  class (array)  based on [1]_.
        Humid-arid calssification(array) based on [1]_.
        CSV formatted table that contains parameters for radiation components
        based on [2]_.
    date : datetime64
        Date to select specific days
    snow_water_storage : array
        if daily snow water storage is greater than 3mm, snow albedo is used
        for shortwave radiation calulation, Units: mm.
    parameters: : array
        The following parameters are obtained from the parameters array:
        snow_albedo_thresh (mm), openwater_albedo (-), pt_coeff_arid (-),
        pt_coeff_humid (-).


        References.

        .. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                    Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                    Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                    Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                    The global water resources and use model WaterGAP v2.2d:
                    model description and evaluation. Geoscientific Model
                    Development, 14(2), 1037–1079.
                    https://doi.org/10.5194/gmd-14-1037-2021

        .. [2] Müller Schmied, H., Müller, R., Sanchez-Lorenzo, A., Ahrens, B.,
                    and Wild, M.: Evaluation of radiation components in a
                    global freshwater model with station-based observations,
                    Water, 8, 450, https://doi.org/10.3390/w8100450,2016b


    Methods
    -------
    priestley_taylor:
        Priestly-Taylor potential evapotranspiration.
    """

    def __init__(self, climate_forcing, static_data, date, snow_water_storage,
                 parameters):
        self.climate_forcing = climate_forcing
        self.static_data = static_data
        self.date = date
        self.upwards_rad_components = []
        # Global model parameters(e.g. snow aldedo threhold, openwater_albedo,
        # Shuttleworth alpha coeffecient  (arid and humid cells) for  potential
        # evapotranspiiration calulation. etc.) can be found here.
        self.pm = parameters
        # =====================================================================
        # # Loading in climate forcing
        # =====================================================================

        #  Actual name: Air tempeature, Units: K
        temperature = self.climate_forcing.temperature.sel(time=str(self.date))
        temperature = temperature.tas.values

        #  Actual name: Downward shortwave radiation  Units: Wm−2
        down_shortwave_radiation = \
            self.climate_forcing.down_shortwave_radiation.sel(
                time=str(self.date))
        down_shortwave_radiation = down_shortwave_radiation.rsds.values

        #  Actual name: Downward longwave radiation  Units: Wm−2
        down_longwave_radiation = \
            self.climate_forcing.down_longwave_radiation.sel(
                time=str(self.date))
        down_longwave_radiation = down_longwave_radiation.rlds.values

        # =====================================================================
        # # Loading in static variables
        # =====================================================================
        # Actual name: Land cover , Units: (-)
        land_cover = self.static_data.land_cover

        # Actual name: canopy model paramters (Table)
        radiation_parameters = self.static_data.canopy_snow_soil_parameters

        # =====================================================================
        # Net shortwave and upward shortwave radiation (Wm−2)
        # =====================================================================
        # Albedo based on landcover type (Müller Schmied et al 2014,Table A2)
        albedo = np.zeros(temperature.shape)
        albedo.fill(np.nan)
        for i in range(len(radiation_parameters)):
            albedo[land_cover[:, :] == radiation_parameters.loc[i, 'Number']] = \
               radiation_parameters.loc[i, 'albedo']

        snow_albedo = np.zeros(temperature.shape)
        snow_albedo.fill(np.nan)
        for i in range(len(radiation_parameters)):
            snow_albedo[land_cover[:, :] == radiation_parameters.loc[i, 'Number']] = \
               radiation_parameters.loc[i, 'snow_albedo']

        #  snow_water_storage > 3mm, snow abledo is used for shortwave
        # radiation calulation
        snow_albedo_thresh = self.pm.snow_albedo_thresh
        albedo = np.where(snow_water_storage > snow_albedo_thresh, snow_albedo,
                          albedo)

        # Actual name: Net shortwave radiation, Units: Wm−2
        # net_shortwave_radiation is based on Eq. 1 in
        # Müller Schmied et al., 2016b
        self.net_shortwave_radiation = down_shortwave_radiation * (1-albedo)

        # Actual name: upward shortwave radiation, Units: Wm−2
        # upward_shortwave_radiation is based on Eq. 2 in
        # Müller Schmied et al., 2016b
        upward_shortwave_radiation = down_shortwave_radiation - \
            self.net_shortwave_radiation

        self.upwards_rad_components.append(upward_shortwave_radiation)
        # =====================================================================
        #  Net longwave radiation and upward longwave radiation (Wm−2)
        # =====================================================================
        # Emissivity by landcover type (Müller Schmied et al 2014,Table A2)
        emissivity = np.zeros(temperature.shape)
        emissivity.fill(np.nan)
        for i in range(len(radiation_parameters)):
            emissivity[land_cover[:, :] == radiation_parameters.loc[i, 'Number']] = \
               radiation_parameters.loc[i, 'emissivity']

        # Stefan_Boltzmann_constant (5.67 × 10−8 (Wm−2·K−4))
        stefan_boltzmann_constant = 5.67e-08  # (Müller Schmied et al., 2016)

        # Actual name: Upward longwave radiation, Units:  Wm−2
        # upward_longwave_radiation is based on Eq. 3 in
        # Müller Schmied et al., 2016b
        up_longwave_radiation = emissivity * \
            (stefan_boltzmann_constant * np.power(temperature, 4))

        #  Actual name: Net longwave radiation Unit: (Wm−2)
        # net_longwave_radiation is based on Eq. 4 in
        # Müller Schmied et al., 2016b
        self.net_longwave_radiation = down_longwave_radiation -\
            up_longwave_radiation

        self.upwards_rad_components.append(up_longwave_radiation)
        # =====================================================================
        # Net radiation (Wm−2) calulation
        # =====================================================================

        #  Actual name: Net radiation, Units: Wm−2
        # net_radiation is based on Eq. 5 in Müller Schmied et al., 2016b
        self.net_radiation = self.net_shortwave_radiation + \
            self.net_longwave_radiation

        # =====================================================================
        # open water net radiation (Wm−2) calulation
        # =====================================================================
        openwater_net_shortwave_radiation = down_shortwave_radiation * \
            (1 - self.pm.openwater_albedo)
        self.openwater_net_radiation = openwater_net_shortwave_radiation + \
            self.net_longwave_radiation

    def priestley_taylor(self):
        """Compute Priestly-Taylor potential evapotranspiration.

        Returns
        -------
        Potential evapotranspiration per time step, Units: mm/d.
        """
        # =====================================================================
        # Slope of the saturation kPa°C-1
        # =====================================================================
        # Converting temperature to degrees celcius
        covert_to_degree = 273.15
        temperature = self.climate_forcing.temperature.sel(time=str(self.date))
        temperature = temperature.tas.values - covert_to_degree

        # Actual name: Slope of the saturation, Units: kPa°C-1
        slope_of_sat_num = 4098 * (0.6108 * np.exp((17.27 * temperature) /
                                                   (temperature + 237.3)))

        slope_of_sat_den = (temperature + 237.3)**2

        slope_of_sat = slope_of_sat_num / slope_of_sat_den

        # =====================================================================
        # Psychrometric constant  kPa°C-1
        # =====================================================================
        # Actual name: Atmospheric pressure,	Units: kPa
        atm_pressure = 101.3

        # Actual name: Latent heat,	Units: MJkg-1
        latent_heat = np.where(temperature > 0,
                               (2.501 - (0.002361 * temperature)), 2.835)

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
        humid_arid = self.static_data.humid_arid
        alpha_pt_coefficient = np.where(humid_arid == 1, self.pm.pt_coeff_arid,
                                        self.pm.pt_coeff_humid)

        # Coverting net radiation to mm/day
        # Note!!!, I deliberately did not attach "self"  here so I dont
        # convert the final net radiation ouput to  mm/day. please take note.
        net_radiation = (self.net_radiation * 0.0864) / latent_heat

        # Actual name: Potential evapotranspiration,	Units:  mmd-1
        potential_evap = alpha_pt_coefficient * ((slope_of_sat * net_radiation)
                                                 / (slope_of_sat + psy_const))

        # Accounting for negative net radiation and setting them to zero
        potential_evap = np.where(net_radiation <= 0, 0, potential_evap)

        # =====================================================================
        # Priestley-Taylor open water potential evapotranspiration (mm/day)
        # =====================================================================
        # Coverting net radiation to mm/day
        openwater_net_radiation = \
            (self.openwater_net_radiation * 0.0864) / latent_heat

        # Actual name: Open water potential evapotranspiration,	Units:  mmd-1
        openwater_pot_evap = \
            alpha_pt_coefficient * ((slope_of_sat * openwater_net_radiation) /
                                    (slope_of_sat + psy_const))

        # Accounting for negative net radiation and setting them to zero
        openwater_pot_evap = np.where(openwater_net_radiation <= 0, 0,
                                      openwater_pot_evap)

        return potential_evap, openwater_pot_evap
