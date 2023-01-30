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

# Define Array size for parameters
longitude_size = 720
latitude_size = 360
parameter_size = (latitude_size, longitude_size)


# =============================================================================
# Radiation and Evapotranspiration
# =============================================================================
# open water albedo (-)
openwater_albedo = 0.08

# snow albedo threhold (mm)
snow_albedo_thresh = 3

# Priestley-Taylor coefficient  for humid cells
pt_coeff_humid = 1.26 + np.zeros(parameter_size)

# Priestley-Taylor coefficient  for arid cells
pt_coeff_arid = 1.74 + np.zeros(parameter_size)

# =============================================================================
# Canopy
# =============================================================================
# maximum storage coefficient (mm)
max_storage_coefficient = 0.3 + np.zeros(parameter_size)

# =============================================================================
# Soil
# =============================================================================
# Fraction of effective_precipitation that directly becomes runoff (-)
runoff_frac_builtup = 0.5

# Runoff coefficient (-)
gamma = 2 + np.zeros(parameter_size)

# Areal correction factor (-)
areal_corr_factor = 1 + np.zeros(parameter_size)

# Maximum daily potential evapotransipration (mm/day)
max_daily_pet = 15.0 + np.zeros(parameter_size)

# critical precipitation threshold for ground water recharge in
# (semi)arid areas (mm/day)
critcal_gw_precipitation = 12.5 + np.zeros(parameter_size)

# =============================================================================
# Groundwater
# =============================================================================
# Globally constant groundwater discharge coefficient (Döll et al., 2014)
gw_dis_coeff = 0.01 + np.zeros(parameter_size)

# *****************************************************************************
#                       Surface water bodies
# *****************************************************************************
# ==================
# lake and wetlands
# ==================
# Reduction exponent (-) taken from Eqn 24 in (Müller Schmied et al. (2021)).
# for local and global lakes and wetlands.
reduction_exponent_lakewet = 3.32193

# Groundwater recharge constant below lakes, reserviors & wetlands (0.01 md−1)
groundwater_recharge_constant = 0.01

# Surface water outflow coefficient (0.01 d−1)
swb_outflow_coeff = 0.01

# Lake outflow exponent (a[-])
lake_out_exp = 1.5

# Maximum lake active depth (m)
activelake_depth = 5 + np.zeros(parameter_size)

# Wetland outflow exponent (a[-])
wet_out_exp = 2.5

# Maximum wetland active depth (m)
activewetland_depth = 2 + np.zeros(parameter_size)

# Surface water bodies (local lakes and global and local wetlands) drainage
# area factor.

swb_drainage_area_factor = 20 + np.zeros(parameter_size)
