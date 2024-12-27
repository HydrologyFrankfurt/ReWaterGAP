# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Merge model parameters into netcdf."""

import glob
import xarray as xr
import numpy as np
import pandas as pd
from calibration import convert_data_csv
from calibration import regionalization as regio


def merge_parameters():
    """
    Merge model parameters into netcdf.

    Returns
    -------
    None.

    """
    calib_out_dir = './calibration/calib_out'
    # Use glob to list all .nc files in the specified directory
    nc_files = glob.glob(f'{calib_out_dir}/**/*.nc', recursive=True)

    # create an output paramater nc file.
    out_params = xr.open_dataset(nc_files[0], decode_times=False)
    out_params['areal_corr_factor'].values = \
        np.where(~np.isnan(out_params['areal_corr_factor']), 1, np.nan)
    out_params['stat_corr_fact'].values = \
        np.where(~np.isnan(out_params['stat_corr_fact']), 1, np.nan)

    # =============================================================================
    # merging various paramaters (CFA and CFS) from different region in to one file
    # =============================================================================
    for i in range(len(nc_files)):
        params_region = xr.open_dataset(nc_files[i], decode_times=False)

        out_params['areal_corr_factor'].values = \
            np.where(params_region['areal_corr_factor'] != 1,
                     params_region['areal_corr_factor'],
                     out_params['areal_corr_factor'])

        out_params['stat_corr_fact'].values = \
            np.where(params_region['stat_corr_fact'] != 1,
                     params_region['stat_corr_fact'], out_params['stat_corr_fact'])

    # =========================================================================
    # read in gamma after regionalisation and add to parameter file
    # =========================================================================
    gamma_df = pd.read_csv('./calibration/Gamma_all_region.csv')
    # Read in arcid xarray
    arcids_paths = "./input_data/static_input/arc_id.nc"
    arcid = xr.open_dataarray(arcids_paths, decode_times=False)

    # Match Arc_IDs in gamma with arcid and set corresponding values in temp_gamma
    arcid_df = arcid.to_dataframe(name="Arc_ID").reset_index()
    gamma_df = gamma_df.set_index("Arc_ID")
    gamma_df["gamma_final"] = gamma_df["gamma_final"].clip(lower=0.1, upper=5)

    # correct North plain china gamma
    gamma_china = pd.read_csv('./calibration/North_plain_china_gamma_correction.csv')
    gamma_china = gamma_china.replace(-99, np.nan).set_index("Arc_ID")

    corrected_gamma = gamma_df.merge(gamma_china, on="Arc_ID", how='left')
    corrected_gamma["gamma_final"] =\
        corrected_gamma["VALUE"].combine_first(corrected_gamma["gamma_final"])
    corrected_gamma = corrected_gamma.drop(columns="VALUE")

    # Join gamma values into arcid DataFrame
    merged = arcid_df.join(corrected_gamma["gamma_final"], on="Arc_ID")

    out_params['gamma'].values = merged["gamma_final"].values.reshape(arcid.shape)

    out_params.to_netcdf("./model/WaterGAP_2.2e_global_parameters.nc")


def run_regionalization_merge_parameters(num_threads_or_nodes):
    """
    Run regionalistion

    Parameters
    ----------
    num_threads_or_nodes : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    num_thread = num_threads_or_nodes
    convert_data_csv.convert_csv()
    regio.regionalize_paramters(num_thread)
    merge_parameters()
    