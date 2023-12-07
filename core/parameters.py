# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Model parameter values."""

# =============================================================================
# This module contains all paameter values to run  WaterGAP
# =============================================================================

import numpy as np


class Parameters:
    """WaterGAP parameters."""

    def __init__(self):
        # Define Array size for parameters
        longitude_size = 720
        latitude_size = 360
        parameter_size = (latitude_size, longitude_size)

        # =====================================================================
        # Radiation and Evapotranspiration
        # =====================================================================
        # open water albedo (-)
        self.openwater_albedo = 0.08 + np.zeros(parameter_size)

        # snow albedo threhold (mm)
        self.snow_albedo_thresh = 3.0 + np.zeros(parameter_size)

        # Priestley-Taylor coefficient  for potential evapotranspiration(α)
        # Following Shuttleworth (1993), α is set to 1.26 in humid
        # and to 1.74 in (semi)arid cells
        # Priestley-Taylor coefficient  for humid cells
        self.pt_coeff_humid = 1.26 + np.zeros(parameter_size)

        # Priestley-Taylor coefficient  for arid cells
        self.pt_coeff_arid = 1.74 + np.zeros(parameter_size)

        # =====================================================================
        # Canopy
        # =====================================================================
        # maximum storage coefficient (mm)
        self.max_storage_coefficient = 0.30 + np.zeros(parameter_size)

        # =====================================================================
        # Snow
        # =====================================================================
        self.snow_freeze_temp = 273.15 + np.zeros(parameter_size)  # K
        self.snow_melt_temp = 273.15 + np.zeros(parameter_size)  # K
        self.adiabatic_lapse_rate = 0.006 + np.zeros(parameter_size)  # K/m or °C/m

        # =====================================================================
        # Soil
        # =====================================================================
        # Fraction of effective_precipitation that directly becomes runoff (-)
        self.runoff_frac_builtup = 0.50

        # Runoff coefficient (-)
        self.gamma = 2 + np.zeros(parameter_size)

        # Areal correction factor (-)
        self.areal_corr_factor = 1.0 + np.zeros(parameter_size)

        # Maximum daily potential evapotransipration (mm/day)
        self.max_daily_pet = 15.0 + np.zeros(parameter_size)

        # critical precipitation threshold for ground water recharge in
        # (semi)arid areas (mm/day)
        self.critcal_gw_precipitation = 12.5 + np.zeros(parameter_size)

        # =====================================================================
        # Groundwater
        # =====================================================================
        # Globally constant groundwater discharge coefficient(Döll et al.,2014)
        self.gw_dis_coeff = 0.01 + np.zeros(parameter_size)

        # *********************************************************************
        #                       Surface water bodies
        # *********************************************************************
        # ==================
        # lake and wetlands
        # ==================
        # Reduction exponent (-) taken from Eqn 24 in (Müller Schmied et al.
        # (2021)) for local and global lakes and wetlands.
        self.reduction_exponent_lakewet = 3.32193 + np.zeros(parameter_size)

        # Groundwater recharge constant below lakes, reserviors & wetlands
        # (0.01 md−1)
        self.gw_recharge_constant = 0.01 + np.zeros(parameter_size)

        # Surface water outflow coefficient (0.01 d−1)
        self.swb_outflow_coeff = 0.01 + np.zeros(parameter_size)

        # Lake outflow exponent (a[-])
        self.lake_out_exp = 1.5 + np.zeros(parameter_size)

        # Maximum lake active depth (m)
        self.activelake_depth = 5.0 + np.zeros(parameter_size)

        # Wetland outflow exponent (a[-])
        self.wetland_out_exp = 2.5 + np.zeros(parameter_size)

        # Maximum wetland active depth (m)
        self.activewetland_depth = 2.0 + np.zeros(parameter_size)

        # Surface water bodies (local lakes and global and local wetlands)
        # drainage area factor.

        self.swb_drainage_area_factor = 20 + np.zeros(parameter_size)

        # ============================
        # Reservior and regulated lake
        # ============================
        # Reduction exponent (-) taken from Eqn 25 in (Müller Schmied et al.
        # (2021)) for reservior and regulated lake.
        self.reduction_exponent_res = 2.81383 + np.zeros(parameter_size)

        # ==================
        # river
        # ==================
        # Station correction factor (-)
        self.stat_corr_fact = 1.0 + np.zeros(parameter_size)
