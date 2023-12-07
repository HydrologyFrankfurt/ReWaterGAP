# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Vertical water balance coordinator."""

# =============================================================================
# This module brings all vertical water balance functions together to run
# =============================================================================

import numpy as np
from core.utility import units_conveter_check_neg_precip as check_or_convert
from core.verticalwaterbalance import waterbalance_vertical as vb_numba
from core.verticalwaterbalance import lai_init


class VerticalWaterBalance:
    """Computes vertical waterbalance."""

    # Get all storages and fluxes in this dictionary container
    fluxes = {}
    storages = {}

    def __init__(self, forcings_static, parameters):
        self.forcings_static = forcings_static
        self.cont_frac = self.forcings_static.static_data.\
            land_surface_water_fraction.contfrac.values.astype(np.float64)/100
        self.parameters = parameters

        # Initialise routing order
        rout_order = self.forcings_static.static_data.rout_order
        self.rout_order = rout_order[['Lat_index_routorder',
                                      'Lon_index_routorder']].to_numpy()

        # Volumes at which storage is set to zero, units: [km3]
        self.minstorage_volume = 1e-15

        # =====================================================================
        #                   Radiation
        # =====================================================================
        # Model paramters for radiation (Müller Schmied et al 2014,Table A2)
        radiation_parameters = \
            self.forcings_static.static_data.canopy_snow_soil_parameters
        # Land cover based on Müller Schmied et al. 2021 , Units: (-)
        self.land_cover = self.forcings_static.static_data.land_cover
        # Humid-arid calssification based on Müller Schmied et al. 2021
        self.humid_arid = self.forcings_static.static_data.humid_arid

        # Albedo based on landcover type (Müller Schmied et al 2014,Table A2)
        self.albedo = np.zeros((self.forcings_static.lat_length,
                                self.forcings_static.lon_length))
        self.albedo.fill(np.nan)
        for i in range(len(radiation_parameters)):
            self.albedo[self.land_cover[:, :] == radiation_parameters.loc[i, 'Number']] = \
               radiation_parameters.loc[i, 'albedo']

        # Snow albedo based on landcover type(Müller Schmied et al 2014,
        # Table A2)
        self.snow_albedo = np.zeros(self.albedo.shape)
        self.snow_albedo.fill(np.nan)
        for i in range(len(radiation_parameters)):
            self.snow_albedo[self.land_cover[:, :] == radiation_parameters.loc[i, 'Number']] = \
               radiation_parameters.loc[i, 'snow_albedo']

        # Emissivity based on landcover type(Müller Schmied et al 2014,
        # Table A2)
        self.emissivity = np.zeros(self.albedo.shape)
        self.emissivity.fill(np.nan)
        for i in range(len(radiation_parameters)):
            self.emissivity[self.land_cover[:, :] == radiation_parameters.loc[i, 'Number']] = \
               radiation_parameters.loc[i, 'emissivity']

        # =====================================================================
        #           Leaf area index
        # =====================================================================
        # Days since start of leaf area index profile(counter for days with
        # growing conditions), units: day
        self.lai_days = np.zeros((self.forcings_static.lat_length,
                                  self.forcings_static.lon_length))

        # cumulative precipitation,  units: mm/day
        self.cum_precipitation = np.zeros((self.forcings_static.lat_length,
                                           self.forcings_static.lon_length))

        # Growth status per grid cell shows whether a specific land cover
        # is (not) growing (value=0) or fully grown (value=1).
        # Initially all landcovers are not growing
        self.growth_status = np.zeros((self.forcings_static.lat_length,
                                       self.forcings_static.lon_length))

        # self.lai_param contains parameter such as maximum and minimum Leaf
        # area index, and inital days per landcover to start or end growing
        # season
        parameters_lai = \
            self.forcings_static.static_data.canopy_snow_soil_parameters
        self.lai_param = \
            lai_init.LeafAreaIndex(self.land_cover, parameters_lai)

        # =====================================================================
        #                   Canopy
        # =====================================================================
        self.canopy_storage = \
            np.zeros((self.forcings_static.lat_length,
                      self.forcings_static.lon_length))

        # =====================================================================
        #                   Snow
        # =====================================================================
        self.snow_water_storage = np.zeros((self.forcings_static.lat_length,
                                            self.forcings_static.lon_length))

        # Land cover specific degreeday values(Müller Schmied et al. 2021)
        self.degreeday = np.zeros(self.snow_water_storage.shape) * np.nan

        # Get degree day parameter (Müller Schmied et al 2014,Table A2)
        parameters_snow = \
            self.forcings_static.static_data.canopy_snow_soil_parameters
        for i in range(len(parameters_snow)):
           self.degreeday[self.land_cover[:, :] == parameters_snow.loc[i, 'Number']] = \
               parameters_snow.loc[i, 'degree-day']

        self.elevation = self.forcings_static.static_data.gtopo30_elevation

        # Snow water storage divided into 100 subgrids based on GTOPO30 (U.S.
        # Geological Survey, 1996) land surface elevation map, Units: mm
        elev_size = \
            self.forcings_static.static_data.gtopo30_elevation[1:].shape
        self.snow_water_storage_subgrid = np.zeros(elev_size)

        # =====================================================================
        #                   Soil
        # =====================================================================
        self.soil_water_content = np.zeros((self.forcings_static.lat_length,
                                            self.forcings_static.lon_length))

        # Get parameters for soil water balance
        soil_static_data = self.forcings_static.static_data.soil_static_data()
        self.builtup_area = soil_static_data[0]
        total_avail_water_content = soil_static_data[1]
        self.drainage_direction = soil_static_data[2]
        self.max_groundwater_recharge = soil_static_data[3]
        self.soil_texture = soil_static_data[4]
        self.groundwater_recharge_factor = soil_static_data[5]

        # Calulate maximum soil water content
        soil_parameters = \
            self.forcings_static.static_data.canopy_snow_soil_parameters

        rooting_depth = np.zeros(self.land_cover.shape) * np.nan
        for i in range(len(soil_parameters)):
            rooting_depth[self.land_cover[:, :] == soil_parameters.loc[i, 'Number']] = \
                soil_parameters.loc[i, 'rooting_depth']
        self.max_soil_water_content = \
            np.where(total_avail_water_content > 0,
                     total_avail_water_content * rooting_depth, np.nan)

        # =====================================================================
        #   Storage to be transfered to runoff when land area fraction is zero
        # =====================================================================
        self.daily_storage_transfer = \
            np.zeros((self.forcings_static.lat_length,
                      self.forcings_static.lon_length))

    def calculate(self, date, current_landarea_frac, landareafrac_ratio):
        """
        Calculate vertical waterbalance.

        Parameters
        ----------
        time_step : int
            Daily timestep.
        date : numpy.datetime64
            Timestamp or date of a daily simulation.

        Returns
        -------
        None.

        """
        # =====================================================================
        # Select daily climate forcing and convert units (only precipitation
        #  and tempearture)
        # =====================================================================
        #                  ==================================
        #                  ||     Precipitation (mm/day)   ||
        #                  ==================================
        precipitation = self.forcings_static.climate_forcing.precipitation.sel(
            time=str(date))

        #  Checking negative precipittaion
        check_or_convert.check_neg_precipitation(precipitation.pr)

        # Covert precipitation units to mm/day
        precipitation = check_or_convert.to_mm_per_day(precipitation.pr)

        #                  =============================
        #                  ||     Air tempeature (K)  ||
        #                  =============================
        temperature = self.forcings_static.climate_forcing.temperature.sel(
            time=str(date))

        # Covert air tempeature from degree celcius to Kelvin
        temperature = check_or_convert.to_kelvin(temperature.tas)

        #                  =========================================
        #                  || Downward shortwave radiation (Wm−2) ||
        #                  =========================================
        down_shortwave_radiation = \
            self.forcings_static.climate_forcing.down_shortwave_radiation.sel(
                time=str(date))
        down_shortwave_radiation = \
            down_shortwave_radiation.rsds.values.astype(np.float64)

        #                  =========================================
        #                  ||  Downward longwave radiation (Wm−2) ||
        #                  =========================================
        down_longwave_radiation = \
            self.forcings_static.climate_forcing.down_longwave_radiation.sel(
                time=str(date))
        down_longwave_radiation = \
            down_longwave_radiation.rlds.values.astype(np.float64)

        # =====================================================================
        # compute vertical waterbalance
        # =====================================================================
        output = vb_numba.\
            vert_water_balance(self.rout_order, temperature,
                               down_shortwave_radiation,
                               down_longwave_radiation,
                               self.snow_water_storage,
                               self.parameters.snow_albedo_thresh,
                               self.parameters.openwater_albedo,
                               self.snow_albedo, self.albedo, self.emissivity,
                               self.humid_arid, self.parameters.pt_coeff_arid,
                               self.parameters.pt_coeff_humid,
                               self.growth_status, self.lai_days,
                               self.lai_param.initial_days,
                               self.cum_precipitation, precipitation,
                               self.lai_param.min_leaf_area_index,
                               self.lai_param.max_leaf_area_index,
                               self.land_cover, self.canopy_storage,
                               current_landarea_frac, landareafrac_ratio,
                               self.parameters.max_storage_coefficient,
                               self.minstorage_volume,
                               self.daily_storage_transfer,
                               self.snow_water_storage_subgrid,
                               self.degreeday, self.elevation,
                               self.parameters.adiabatic_lapse_rate,
                               self.parameters.snow_freeze_temp,
                               self.parameters.snow_melt_temp,
                               self.parameters.runoff_frac_builtup,
                               self.builtup_area, self.soil_water_content,
                               self.parameters.gamma,
                               self.parameters.max_daily_pet,
                               self.soil_texture, self.drainage_direction,
                               self.max_groundwater_recharge,
                               self.groundwater_recharge_factor,
                               self.parameters.critcal_gw_precipitation,
                               self.max_soil_water_content,
                               self.parameters.areal_corr_factor)

        # Radiation and PET output
        net_radiation = output[0]
        daily_potential_evap = output[2]
        openwater_potential_evap = output[3]

        # Leaf area index ouput
        leaf_area_index = output[4]
        self.lai_days = output[5]
        self.cum_precipitation = output[6]
        self.growth_status = output[7]

        # Canopy output
        self.canopy_storage = output[8]
        throughfall = output[9]
        canopy_evap = output[10]

        # Snow ouput
        self.snow_water_storage = output[12]
        self.snow_water_storage_subgrid = output[13]
        snow_fall = output[14]
        sublimation = output[15]
        snow_melt = output[16]

        # Soil output
        self.soil_water_content = output[17]
        groundwater_recharge_from_soil_mm = output[18]
        surface_runoff = output[19]

        # update daily storage transfer
        self.daily_storage_transfer = output[21]

        # print(throughfall[17, 192], output[11][17, 192], self.snow_water_storage[17, 192])
        # =====================================================================
        # Getting all storages
        # =====================================================================
        # write out data per continental fraction
        per_contfrac = current_landarea_frac / self.cont_frac

        VerticalWaterBalance.storages.\
            update({'canopystor': self.canopy_storage * per_contfrac,
                    'swe': self.snow_water_storage * per_contfrac,
                    'soilmoist':  self.soil_water_content * per_contfrac})

        # =====================================================================
        # Getting all fluxes
        # =====================================================================

        VerticalWaterBalance.fluxes.\
            update({'netrad': net_radiation,
                    'potevap':  daily_potential_evap,
                    'lai-total':  leaf_area_index,
                    'canopy_evap':  canopy_evap * per_contfrac,
                    'throughfall':  throughfall * per_contfrac,
                    'snow_fall':  snow_fall * per_contfrac,
                    'snow_melt':  snow_melt * per_contfrac,
                    'snow_evap':  sublimation * per_contfrac,

                    # Groundwater recharge (qr) and surface runoff(qs)
                    # are writtem out as netcdf and not used for lateral water
                    # balance calculation.
                    'qr':  groundwater_recharge_from_soil_mm * per_contfrac,
                    'qs':  surface_runoff * per_contfrac,

                    # Variables here are used for lateral water balance
                    # calculation. Note: 'groundwater_recharge' and
                    # 'surface_runoff' are not wriiten out.
                    'groundwater_recharge': groundwater_recharge_from_soil_mm,
                    'surface_runoff': surface_runoff,
                    'openwater_PET': openwater_potential_evap,
                    'daily_storage_transfer': self.daily_storage_transfer,
                    'daily_precipitation': precipitation})

    def get_storages_and_fluxes(self):
        """
        Get daily storages and fluxes for vertical waterbalance.

        Returns
        -------
        dict
            Dictionary of all storages.
        dict
           Dictionary of all fluxes.

        """
        return VerticalWaterBalance.storages, VerticalWaterBalance.fluxes

    def update_vertbal_for_restart(self, vertbalance_states):
        """
        Update vertical balance parameters for model restart.

        Parameters
        ----------
        vertbalance_states : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.lai_days = vertbalance_states["lai_days_since_start"]
        self.cum_precipitation = vertbalance_states["cum_precipitation"]
        self.growth_status = vertbalance_states["growth_status"]

        self.canopy_storage = vertbalance_states["canopy_storage_prev"]
        self.snow_water_storage = vertbalance_states["snow_water_stor_prev"]
        self.snow_water_storage_subgrid = \
            vertbalance_states["snow_water_storsubgrid_prev"]
        self.soil_water_content = vertbalance_states["soil_water_content_prev"]
