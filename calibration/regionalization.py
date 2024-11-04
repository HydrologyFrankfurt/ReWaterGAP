import pandas as pd
import glob
import os
import numpy as np
import xarray as xr
from sklearn.linear_model import LinearRegression
import concurrent.futures


def read_input_files(folder_path):
    """Read all descriptors as txt files and return a combined DataFrame."""
    all_files = glob.glob(f"{folder_path}/*.csv")
    df_list = []

    for file in all_files:
        df = pd.read_csv(file, sep=",")
        df_list.append(df)

    combined_df = df_list[0]
    for df in df_list[1:]:
        combined_df = pd.merge(combined_df, df, on="Arc_ID", how="outer")

    # Temperatue has unit  as deg C hence we divide by 100 to deg C
    combined_df['GTEMP_1971_2000'] /= 100
    combined_df['basin_identifier'] = np.nan

    combined_df.drop(columns=['outlet'], inplace=True)
    combined_df["area_max_soil"] = np.where(combined_df['max_soil_water_content'] > 0, combined_df['cell_area'], 0)
    combined_df["gamma"] = np.nan
    return combined_df


def get_direct_upstreamcells(arrays, marker=np.nan):
    """Get direct upstream cells for a calibration station."""
    for i in range(1, len(arrays)):
        for j in range(i):
            arrays[i][np.isin(arrays[i], arrays[j])] = marker
    return arrays[-1]


def get_arcid_gamma(region_folders, combined_df):
    """Get Arc_ID and gamma values for direct upstream cells."""
    upstreamcells_per_station = np.load(f"{region_folders}/prev_upstream_cells.npz")
    params_path = glob.glob(f"{region_folders}/*.nc")
    out_params = xr.open_dataset(params_path[0], decode_times=False)

    for i in range(len(upstreamcells_per_station.files)):
        station = upstreamcells_per_station.files[i]
        if i == 0:
            direct_upstreamcells = upstreamcells_per_station[station]
        else:
            upstream_stations = upstreamcells_per_station.files[:i + 1]
            temp_data = [upstreamcells_per_station[j] for j in upstream_stations]
            direct_upstreamcells = get_direct_upstreamcells(temp_data)

        direct_upstreamcells_arcid = direct_upstreamcells[~np.isnan(direct_upstreamcells)]
        gamma_values = out_params['gamma'].values
        gamma = np.nanmean(np.where(direct_upstreamcells > 0, gamma_values, np.nan))

        combined_df.loc[combined_df['Arc_ID'].isin(direct_upstreamcells_arcid), 'basin_identifier'] = station
        combined_df.loc[combined_df['Arc_ID'].isin(direct_upstreamcells_arcid), 'gamma'] = gamma

    return combined_df


def regionalize_paramters():
    # =========================================================================
    # Path settings
    # =========================================================================
    folder_path = './calibration/regionalization_input'
    calib_out_dir = './calibration/calib_out'

    # =========================================================================
    #     Get descriptors
    # =========================================================================
    combined_df = read_input_files(folder_path)

    # =========================================================================
    # Get Arc_ID and gamma values of direct upstream cells per station
    # for all regions
    # =========================================================================

    subfolders = glob.glob(calib_out_dir + "/*/")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(get_arcid_gamma, subfolders, [combined_df]*len(subfolders))

    # Combine results
    combined_df_all_region = combined_df.copy()
    for result in results:
        combined_df_all_region['gamma'] = combined_df_all_region['gamma'].fillna(result['gamma'])
        combined_df_all_region['basin_identifier'] = \
            combined_df_all_region['basin_identifier'].fillna(result['basin_identifier'])

    # =============================================================================
    # Get identifier for all uncalibrated basins and hence gidcells
    # =============================================================================
    combined_df_all_region['basin_identifier'].fillna(combined_df_all_region['super_basin_id'], inplace=True)

    # =========================================================================
    #  Aggregate areas and compute weights for multilinear regrssion
    # =========================================================================
    cont_reg = combined_df_all_region.groupby(['basin_identifier'], as_index=False)[['cell_area', 'area_max_soil']].sum()
    cont_reg.rename(columns={'cell_area': 'upstream_cell_area', 'area_max_soil': 'upstream_cell_area_max_soil'}, inplace=True)

    combined_df_all_region = pd.merge(combined_df_all_region, cont_reg, on="basin_identifier", how="outer")
    columns = ['max_soil_water_content', 'aquifer_groundwater_recharge_fator', 'GTEMP_1971_2000', 
               'max_groundwater_recharge', 'mean_basin_slope_class', 'open_water_fraction', 
               'permanent_snow_ice_fraction']

    for column in columns:
        if column == 'max_soil_water_content':
            combined_df_all_region[f'{column}_weight'] = \
                np.where(combined_df_all_region[column] > 0,
                         combined_df_all_region[column] * combined_df_all_region['cell_area'] /
                         combined_df_all_region['upstream_cell_area_max_soil'], 0)
        else:
            combined_df_all_region[f'{column}_weight'] = combined_df_all_region[column] * \
                combined_df_all_region['cell_area'] / combined_df_all_region['upstream_cell_area']

    # Prepare for regression analysis
    weight_columns = [col for col in combined_df_all_region.columns if col.endswith('_weight')]
    calib_regression = combined_df_all_region.groupby(['basin_identifier'], as_index=False)[weight_columns].sum()

    gamma = combined_df_all_region.groupby(['basin_identifier'], as_index=False)['gamma'].mean()
    calib_regression = pd.merge(calib_regression, gamma, on="basin_identifier", how="outer")
    calib_regression['ln_gamma'] = np.where(calib_regression['gamma'] > 0, np.log(calib_regression['gamma']), np.nan)

    # Data contains both calib and uncalibrated cells
    calib_uncalib_regression = calib_regression.copy()

    # Get only calibrated cells
    calib_regression = calib_regression.dropna()

    # Create and fit the regression model
    model = LinearRegression()
    regression_descriptor = calib_regression.iloc[:, 1:-2]

    regression_gamma = calib_regression['ln_gamma']
    model.fit(regression_descriptor, regression_gamma)

    # Get the coefficients
    coefficients = model.coef_
    intercept = model.intercept_
    # Print the coefficients
    print("Coefficients:", coefficients)
    print("Intercept:", intercept)

    # get estimated gamma
    ln_gamma_estimated = model.predict(calib_uncalib_regression.iloc[:, 1:-2])

    # set gamma limit
    calib_uncalib_regression['gamma_estimated'] = np.exp(ln_gamma_estimated)
    calib_uncalib_regression['gamma_estimated'] = \
        calib_uncalib_regression['gamma_estimated'].clip(lower=0.1, upper=5)

    # only use gamma estimated for where there are uncalibrated cells.
    calib_uncalib_regression['gamma_final'] = calib_uncalib_regression['gamma']
    calib_uncalib_regression['gamma_final'].fillna(calib_uncalib_regression['gamma_estimated'], inplace=True)

    calib_uncalib_regression = calib_uncalib_regression.drop(columns=['gamma'])

    combined_df_all_region = pd.merge(combined_df_all_region, calib_uncalib_regression, on="basin_identifier", how="outer")
    combined_df_all_region.to_csv('regionlisation_all_region.csv', index=False)

    gamma_out = combined_df_all_region[['Arc_ID', 'gamma', 'gamma_final']]
    gamma_out.to_csv('./calibration/Gamma_all_region.csv', index=False)


