# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""compute Bankfull flow."""


import xarray as xr
import numpy as np
import pandas as pd

# Note!!!
# To compute the bankfull flow, we use a return flow period of 1.5 years
# (approach 6 in Schneider et al., 2011 Table 4).
# We extract the annual maxima series from 40 years of daily river discharge
# (1961-2000). We compute the Pearson III distribution properties for both
# arithmetic and logarithmic values (mean, standard deviation,
#  variation coefficient, and skewness coefficient).
# For a particular skewness coefficient and a return period of 1.5 years,
# we get the K value (shape parameter) from a Pearson III distribution table.
# The bankfull flow is then estimated for the skewness coefficient and this
# return period (1.5 years) using the schematic described in figure 4.11
# (page 138) of * Maniak, U., 2005. Hydrologie und Wasserwirtschaft – eine
# Einführung für Ingenieure. Springer, Berlin.* for Pearson III distribution.


# simulated discharge path
SIM_DIS_PATH = "watergap2-2e_gswp3-w5e5_sim_histsoc_dis_down_global_daily_1961_2000.nc4"

# Constants
YEAR_START = 1961
YEAR_END = 2000
NODATA  = -9999

# =============================================================================
# Load simulated discharge (streamflow) dataset and select period
# =============================================================================
sim_dis_full = xr.open_mfdataset(SIM_DIS_PATH, chunks={'time': 365})
sim_dis = sim_dis_full.sel(time=slice(f"{YEAR_START}-01-01", f"{YEAR_END}-12-31"))

# =============================================================================
# Get annual maxima series (AMS) for simulated discharge (km3/day)
# =============================================================================
# Arithmetic
annual_maxima_dis = sim_dis.dis_down.resample(time='1Y').max().values

# Logarithmic
# Ensure no zero values for logarithmic calculation
annual_maxima_no_zero_dis = np.where(annual_maxima_dis == 0, np.nan,
                                     annual_maxima_dis)
log_annual_maxima_dis = np.log(annual_maxima_no_zero_dis)

# =============================================================================
# Compute  Pearson III distribution properties
# =============================================================================
# Arithmetic (mean, standard deviation, variation coefficient)
mean_maxima_dis = np.mean(annual_maxima_dis, axis=0)
std_maxima_dis = np.std(annual_maxima_dis, axis=0)
varcoeff_maxima_dis = np.divide(std_maxima_dis, mean_maxima_dis,
                                out=np.zeros_like(std_maxima_dis),
                                where=mean_maxima_dis != 0)


# Logarithmic (mean, standard deviation, variation coefficient)
log_mean_maxima_dis = np.mean(log_annual_maxima_dis, axis=0)
log_std_maxima_dis = np.std(log_annual_maxima_dis, axis=0)
log_varcoeff_maxima_dis = np.divide(log_std_maxima_dis, log_mean_maxima_dis,
                                    out=np.zeros_like(log_std_maxima_dis),
                                    where=log_mean_maxima_dis != 0)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Skewness coefficient (fisher-pearson standardized moment coefficien)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def compute_skewness(ams, mean_ams, std_ams, sample_size):
    """
    Compute skewness coefficient.

    Parameters
    ----------
    ams : array
        Annual maximaum discharge series
    mean_ams : array
       (Log) Mean of annual maximaum discharge series
    std_ams : array
        (Log) Standard deviation of annual maximaum discharge series
    sample_size : int
        sample size per grid cell

    Returns
    -------
    skewness_coefficient : float
        (Log) Skewness coefficient

    """
    skew_p1 = sample_size / ((sample_size - 1) * (sample_size - 2))
    skew_p2 = np.nansum((ams - mean_ams)**3, axis=0)

    skew_numerator = skew_p1 * skew_p2
    skew_denominator = std_ams**3
    skewness_coefficient = np.divide(skew_numerator, skew_denominator,
                                     out=np.zeros_like(skew_denominator),
                                     where=skew_denominator != 0)
    return skewness_coefficient


sample_size = annual_maxima_dis.shape[0]
# Arithmetic
skew_maxima_dis = compute_skewness(annual_maxima_dis, mean_maxima_dis,
                                   std_maxima_dis, sample_size)
# Logarithmic
log_skew_maxima_dis = compute_skewness(log_annual_maxima_dis, log_mean_maxima_dis,
                                       log_std_maxima_dis, sample_size)

lat, lon =  243, 638

# =============================================================================
# Load Pearson III distribution k-values and interpolate and compute
# bankfull flow
# =============================================================================
pearson_k3 = pd.read_csv("K_PEARSON_3.csv")
pearson3_skewness_values = pearson_k3.iloc[:, 0][3:].values.astype(np.float32)
# select only k-values for return period 1.5
pearson3_k_values = pearson_k3.iloc[:, 5][3:].values.astype(np.float32)


def get_k_value(skewness_coefficient, skewness_values, k_values):
    """
    Get k-values for skewness coefficient for return period 1.5 years.

    Parameters
    ----------
    skewness_coefficient : float
        (Log) Skewness coefficient for annual maximaum discharge series
    skewness_values : array
        Skewness values from Pearson III distribution table
    k_values : array
        k-value from Pearson III distribution table

    Returns
    -------
    k-value, float
        return actual or interpolated k-values for a specific skewness
        coefficient using a return period of 1.5

    """
    return np.interp(skewness_coefficient, skewness_values, k_values)


def compute_bankfull_flow(log_skew_ams, skew_ams,
                          sample_size, std_ams, log_mean_ams,
                          log_varcoeff_ams, mean_ams, varcoeff_ams):
    """
    Compute bankfull flow (km3/day).

    Bankfull flow estimated for the skewness coefficient and  return period
      of (1.5 years) using the schematic described in figure 4.11
    (page 138) of * Maniak, U., 2005. Hydrologie und Wasserwirtschaft – eine
    Einführung für Ingenieure. Springer, Berlin.* for Pearson III distribution.

    Parameters
    ----------
    log_skew_ams : float
        Logarithimic skewness coefficient for annual maximaum discharge series
    skew_ams : float
        Arithmetic skewness coefficient for annual maximaum discharge series
    sample_size : float
        sample size per grid cell
    std_ams : float
        Arithmetic Standard deviation of annual maximaum discharge series
    log_mean_ams : float
        Logarithimic mean of annual maximaum discharge series
    log_varcoeff_ams : float
        Logarithimic variation coefficient of annual maximaum discharge series
    mean_ams : float
        Arithmetic mean of annual maximaum discharge series
    varcoeff_ams : float
        Arithmetic variation coefficient of annual maximaum discharge series

    Returns
    -------
    bankfull_flow (km3/day)
        DESCRIPTION.
    """
    if not np.isnan(std_ams):  # Donot consider nan values
        if sample_size > 0 and std_ams > 0:  # std = positive or zero
            if log_skew_ams >= 0:  # Logarithmic
                k_value = get_k_value(log_skew_ams, pearson3_skewness_values, pearson3_k_values)
                log_bankfull_flow = log_mean_ams * (1 + (log_varcoeff_ams * k_value))
                bankfull_flow = np.exp(log_bankfull_flow)
            else:  # Arithmetic

                d_limit = mean_ams * (1.0 - (2.0 * varcoeff_ams / skew_ams))

                if skew_ams < 0 or d_limit < 0:
                    skew_ams = 2.0 * varcoeff_ams

                k_value = get_k_value(skew_ams, pearson3_skewness_values, pearson3_k_values)
                bankfull_flow = mean_ams * (1 + (varcoeff_ams * k_value))
        else:
            bankfull_flow = NODATA
    else:
        bankfull_flow = np.nan  # oceans

    return bankfull_flow


# Vectorize the function for array operations
vectorized_compute_bankfull_flow = np.vectorize(compute_bankfull_flow)

# Compute bankfull flow
bankfull_flow = vectorized_compute_bankfull_flow(
    log_skew_maxima_dis, skew_maxima_dis, sample_size,
    std_maxima_dis, log_mean_maxima_dis,
    log_varcoeff_maxima_dis, mean_maxima_dis, varcoeff_maxima_dis)


# =============================================================================
# Convert to m3/s and fix negative bankfull flow value
# =============================================================================
# Since Pearson III distribution k-values can be negtaive,
# estimated bankfull_flow values can negative. if bankfull values are negative
# set to nan values or  -9999 as in that of old code

# Convert from k3/day to m3/s
M3_S_CONVERSION = 1e9 / (24 * 60 * 60)
bankfull_flow_m3_per_s = bankfull_flow * M3_S_CONVERSION
bankfull_flow_m3_per_s[bankfull_flow_m3_per_s < 0] = NODATA

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# write out data
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Extract latitude and longitude coordinates
lat = sim_dis['lat']
lon = sim_dis['lon']

# Create your numpy array data (example with random values)
# Create a new DataArray from the numpy array data
save_bankfull_flow = xr.DataArray(bankfull_flow_m3_per_s,
                                  coords=[lat, lon],
                                  dims=['lat', 'lon'])

# Update data name and attribute
save_bankfull_flow.name = 'bankfull_flow'
save_bankfull_flow.attrs['units'] = 'm3/s'
save_bankfull_flow.attrs['legend'] = '-9999 are no data value'

# Save the updated Dataset to a new file (if needed)
save_bankfull_flow.to_netcdf('bankfull_flow_test.nc')


# =============================================================================
# There is no need for a chi-squared test as it is only needed to accept or
# reject the Pearson III distribution.
# =============================================================================
