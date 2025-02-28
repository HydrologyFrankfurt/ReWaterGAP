# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Calibration Routine."""

import os

import numpy as np
import pandas as pd
import xarray as xr
from scipy.optimize import minimize
from termcolor import colored


from controller import configuration_module as cm
from controller import staticdata_handler as sd
from model.utility import get_upstream_basin as get_basin
import run_watergap
import misc.cli_args as cli

args = cli.parse_cli()


class OptimizationState:
    """Compute calibration CS1-CS4 sect. 4.9 (Müller Schmied et al. 2021)."""

    def __init__(self):
        self.threshold_cs1 = 0.01
        self.threshold_cs2 = 0.1
        self.calibration_status = 0
        self.initialize_static = sd.StaticData(cm.run_calib)
        self.start_year = int(cm.start.split("-")[0])
        self.end_year = int(cm.end.split("-")[0])
        self.obs_dis = 0
        self.mean_sim_dis = 0
        self.mean_obs_dis = 0
        self.annual_pot_cell_runoff = 0
        self.currrent_gamma = 0
        self.gamma_limit = [0.1, 5]
        self.compute_cfs = False
        self.calib_out_dir = "./calibration/calib_out/"
        self.basin_id = None

    def get_direct_upstreamcells(self, arrays, marker=np.nan):
        """
        Get direct upstream cell for calibration station.

        Parameters
        ----------
        arrays : array
            station upstream cells.
        marker : float, optional
            Marks cells which are not direct upstream with NAN values.

        Returns
        -------
        arrays
            direct upstream cell for calibration station

        """
        # Make sure mask contain only direct upstream cells
        for i in range(1, len(arrays)):
            # Iterate over all previous arrays to mark common values
            for j in range(i):
                arrays[i][np.isin(arrays[i], arrays[j])] = marker

        return arrays[-1]

    def get_observed_discharge(self, station_id, basin_id):
        """
        Get observed discharge per station.

        Parameters
        ----------
        station_id : str
            ID for calibration station.

        Returns
        -------
        None.

        """
        self.basin_id = basin_id
        obs_dis_path = f"{self.calib_out_dir}{self.basin_id}/station_observed_discharge/"
        station_file_path = f"{obs_dis_path}{station_id}_observed_discharge.csv"

        # Load observed data from the csv file
        obs_dis = pd.read_csv(station_file_path)  # km3_year
        self.obs_dis = obs_dis

    def calib_cs1(self, gamma, calib_station, watergap_basin, calib_unit_gamma,
                  check_bounds=False):
        """
        Perform calibrartion status 1, sect. 4.9 (Müller Schmied et al. 2021).

        Parameters
        ----------
        gamma : float
            Runoff coefficient
        calib_station : str
            contains station id , lat and lon
        watergap_basin : array
            contains all upstream cells for calibration station .
        calib_unit_gamma : array
            contains only direct upstream cell where runoff coefficient (gamma)
            should be changed.
        check_bounds : boolean, optional
            If true check_gamma_bounds function is run. This function
            sets gamma to bounds after the 1st iteration so that if
            the error or bias is still not +/-1% in the 2nd iteration.
            we already skip to CS2-CS4.

        Raises
        ------
        Exception
            End calibration if successful.

        Returns
        -------
        error_cs1 : float
            Long term Bias.

        """
        self.currrent_gamma = gamma

        # Load parameter file and update gamma
        base_param_path = f"{self.calib_out_dir}{self.basin_id}"
        param_path = f"{base_param_path}/WaterGAP_2.2e_global_parameters_basin_{self.basin_id}.nc"

        with xr.open_dataset(param_path, decode_times=False) as global_params:

            # Update gamma in the dataset
            global_params['gamma'].values = \
                np.where(calib_unit_gamma > 0, self.currrent_gamma,
                         global_params['gamma'].values)

            # Save the modified dataset
            temp_param_path = f"{base_param_path}/temp_WaterGAP_2.2e_global_parameters.nc"
            global_params.to_netcdf(temp_param_path)

        # Replace the original file with the updated file
        os.remove(param_path)
        os.replace(temp_param_path, param_path)

        # =====================================================================
        # Run WaterGAP and get simulated data
        # =====================================================================
        simulated_data = run_watergap.run(calib_station, watergap_basin, self.basin_id)
        self.annual_pot_cell_runoff = simulated_data["pot_cell_runoff"]

        sim_dis = np.array(simulated_data["sim_dis"])  # km3/year
        sim_years = list(range(self.start_year, self.end_year+1))
        sim_df = pd.DataFrame({"Year": sim_years, "sim_dis": sim_dis})

        # Merge the dataframes on 'Year'. Goal is to remove yearly simulated
        # discharge which is not available in observed discharge data.
        merged_df = pd.merge(sim_df, self.obs_dis, on='Year', how='left')
        filtered_sim_obs_df = merged_df.dropna()
        print(filtered_sim_obs_df)

        self.mean_sim_dis = filtered_sim_obs_df['sim_dis'].mean()
        self.mean_obs_dis = filtered_sim_obs_df['obs_dis'].mean()

        # =====================================================================
        # Calculate error
        # =====================================================================
        error_cs1 = np.abs((self.mean_sim_dis - self.mean_obs_dis) / self.mean_obs_dis)
        print('\n' + f'Bias {error_cs1} for Gamma = {self.currrent_gamma}')
        # =====================================================================

        # Check if the optimization should be terminated
        if error_cs1 < self.threshold_cs1:
            self.calibration_status = 1
            if check_bounds is False:
                print('\n' + ' Calibration sucessful for Gamma ' +
                      f'= {self.currrent_gamma} and Bias = {error_cs1}')
                raise Exception('\n' + f'Calibration status: {self.calibration_status}')

        return error_cs1

    def check_gamma_bounds(self, initial_gamma, calib_station, watergap_basin,
                           calib_unit_gamma):
        """
        Set gamma to bounds after the 1st iteration.

        Method: We run the WaterGAP model with an initial guess.
        Afterward, we compare the mean simulated discharge to the observed
        discharge. If the simulated discharge is greater, we reduce it by
        setting gamma to the maximum value (5). If the simulated discharge is
        still greater, we keep gamma at 5 and proceed to CS2-CS4.
        Otherwise, we run an optimization algorithm to find the optimal gamma
        within the bounds (initial bounds, maxbounds).

        The same approach applies when we want to increase the simulated
        discharge. If the discharge remains smaller even after decreasing it to
        the minimum (0.1), we set gamma to 0.1 m and proceed to CS2-CS4.
        Otherwise, we run the optimization algorithm with gamma bounds
        (minbounds, initial bounds) to find the appropriate value.


        Parameters
        ----------
        initial_gamma : float
            Initial guess for runoff coefficient(defualt = 2)
        calib_station :str
            contains station id , lat and lon
        watergap_basin : array
            contains all upstream cells for calibration station .
        calib_unit_gamma : array
            contains only direct upstream cell where runoff coefficient (gamma) 
            should be changed.

        Returns
        -------
        gamma_bounds : list of tuple
            set gamma to bounds where error is in +/-1% threshold

        """
        # Capping gamma to bounds after the 1st iteration so that if
        # the error or bias is still not +/-1% in the 2nd iteration.
        # we already skip to CS2-CS4

        gamma_bounds = 0
        check_bounds = True

        self.calib_cs1(initial_gamma, calib_station, watergap_basin,
                       calib_unit_gamma, check_bounds)

        if self.mean_sim_dis - self.mean_obs_dis > 0:
            self.calib_cs1(self.gamma_limit[1], calib_station, watergap_basin,
                           calib_unit_gamma, check_bounds)

            if self.mean_sim_dis - self.mean_obs_dis > 0:
                self.calibration_status = 2
                gamma_bounds = self.gamma_limit[1]
            else:
                gamma_bounds = [(initial_gamma, self.gamma_limit[1])]
                print('\n' + f'Gamma {self.gamma_limit[1]} is too great.' +
                      f' Actual gamma lies in bounds {gamma_bounds}')
        else:
            # here we ....
            self.calib_cs1(self.gamma_limit[0], calib_station, watergap_basin,
                           calib_unit_gamma, check_bounds)
            if self.mean_sim_dis - self.mean_obs_dis < 0:
                self.calibration_status = 2
                gamma_bounds = self.gamma_limit[0]
            else:
                gamma_bounds = [(self.gamma_limit[0], initial_gamma)]
                print('\n' + f'Gamma {self.gamma_limit[0]} is too small.' +
                      f' Actual gamma lies in bounds {gamma_bounds}')
        return gamma_bounds

    def calib_cs2(self, gamma):
        """
        Perform calibrartion status 2, sect. 4.9 (Müller Schmied et al. 2021).

        Parameters
        ----------
        gamma : float
            Runoff coefficient

        Returns
        -------
        None.

        """
        if self.calibration_status == 2:
            min_mean_obs_dis_adapted = self.mean_obs_dis * 0.9
            max_mean_obs_dis_adapted = self.mean_obs_dis * 1.1

            check_cs2 = min_mean_obs_dis_adapted <= self.mean_sim_dis <= max_mean_obs_dis_adapted

            if check_cs2:
                print(f'Calibration sucessful for 10% criterion  with Gamma = {gamma}' )
            else:
                self.calibration_status = 3
                print("10% criterion cannot be fulfilled, CFA is calculated." + '\n')

    def calib_cs3(self, calib_unit_cfa):
        """
        Perform calibrartion status 3, sect. 4.9 (Müller Schmied et al. 2021).

        Parameters
        ----------
        calib_unit_cfa : array
            contains only direct upstream cell where areal correction factor (CFA)
            should be changed.

        Returns
        -------
        None.

        """
        # We need to ensure that CFA is adjusted accordingly for a cell
        # with either positive (precipitation > evapotranspiration)
        # and negative (evapotranspiration > precipitation) cell water
        # balance.
        #  The sign for a positive and negative cell water balance can be
        # already seen in the varible potential_cell_runoff (We compute CFA with
        # potcell runoff because it’s the basis for applying the CFA.)
        # Details can be found here on CFA:
        # (https://hess.copernicus.org/articles/12/841/2008/hess-12-841-2008.pdf)

        if self.calibration_status == 3:
            self.compute_cfs=True
            # Concatenate along a time and then take the mean
            combined_annual_pot_cell_runoff = xr.concat(self.annual_pot_cell_runoff, dim='time')
            mean_pot_cell_runoff = combined_annual_pot_cell_runoff.mean(dim='time') #km3/year

            # potential cell runoff for the entire calibration unit.
            mean_pot_cell_runoff_calib_unit = \
                np.where(calib_unit_cfa>0, mean_pot_cell_runoff.values, np.nan)
            abs_sum_pot_cell_runoff_calib_unit = np.nansum(np.abs(mean_pot_cell_runoff_calib_unit))

            if self.currrent_gamma == self.gamma_limit[0]:
                mean_obs_dis_adapted = self.mean_obs_dis * 0.9
            else:
                mean_obs_dis_adapted = self.mean_obs_dis * 1.1

            sign = lambda runoff: np.where(runoff > 0, 1, np.where(runoff < 0, -1, 0))
            # sign_runof is either 1, -1 or 0
            sign_runoff = sign(mean_pot_cell_runoff_calib_unit)

            compute_cfa = 1 - (sign_runoff *(self.mean_sim_dis - mean_obs_dis_adapted)
                               / abs_sum_pot_cell_runoff_calib_unit)

            cfa = np.where(calib_unit_cfa > 0, compute_cfa , np.nan)

            # Limiting correction factor to range 0.5 - 1.5.
            cfa = np.where(cfa > 1.5, 1.5,  np.where(cfa < 0.5, 0.5, cfa))

            print("Potential runoff in basin: ", abs_sum_pot_cell_runoff_calib_unit, "km3/year")
            print("Max CFA in basin: ", np.nanmax(cfa))
            print("Min CFA in basin: ",  np.nanmin(cfa))

            # Load parameter file and update CFA
            base_param_path = f"{self.calib_out_dir}{self.basin_id}"
            param_path = \
                f"{base_param_path}/WaterGAP_2.2e_global_parameters_basin_{self.basin_id}.nc"
            with xr.open_dataset(param_path, decode_times=False) as global_params:

                # Update areal corection factor  in the dataset
                global_params['areal_corr_factor'].values = \
                    np.where(calib_unit_cfa>0, cfa,
                              global_params['areal_corr_factor'].values)

                # Save the modified dataset
                temp_param_path = f"{base_param_path}/temp_WaterGAP_2.2e_global_parameters.nc"
                global_params.to_netcdf(temp_param_path)

            # Replace the original file with the updated file
            os.remove(param_path)
            os.replace(temp_param_path, param_path)

    def calib_cs4(self, calib_station, watergap_basin):
        """
        Perform calibrartion status 4, sect. 4.9 (Müller Schmied et al. 2021).

        Parameters
        ----------
        calib_station : TYPE
            DESCRIPTION.
        watergap_basin : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.compute_cfs:
            # =================================================================
            # Run WaterGAP and get simulated data
            # =================================================================
            simulated_data = run_watergap.run(calib_station, watergap_basin, self.basin_id)

            sim_dis = np.array(simulated_data["sim_dis"])  # km3/year
            sim_years = list(range(self.start_year, self.end_year+1))
            sim_df = pd.DataFrame({"Year": sim_years, "sim_dis": sim_dis})

            # Merge the dataframes on 'Year'. Goal is to remove yearly simulated
            # discharge which is not available in observed discharge data.
            merged_df = pd.merge(sim_df, self.obs_dis, on='Year', how='left')
            filtered_sim_obs_df = merged_df.dropna()
            print(filtered_sim_obs_df)

            self.mean_sim_dis = filtered_sim_obs_df['sim_dis'].mean()
            self.mean_obs_dis = filtered_sim_obs_df['obs_dis'].mean()
            # =================================================================

            if self.currrent_gamma == self.gamma_limit[0]:
                mean_obs_dis_adapted = self.mean_obs_dis * 0.9
            else:
                mean_obs_dis_adapted = self.mean_obs_dis * 1.1

            # Here, we explicitly calculate CFS to correct the discharge at
            # the grid cell
            cfs = mean_obs_dis_adapted / self.mean_sim_dis

            if (1.0 < cfs < 1.01) or (0.99 < cfs < 1.0):
                cfs = 1.0
                print(f"cfs is not far away from 1.0: {cfs}")

            print(f"CFS is calculated with Gamma = {self.currrent_gamma}  to be {cfs}" + '\n' )

            if (cfs > 1.0) or (cfs < 1.0):
                self.calibration_status = 4

            # Load parameter file and update CFA
            if self.calibration_status == 4:
                base_param_path = f"{self.calib_out_dir}{self.basin_id}"
                param_path = \
                    f"{base_param_path}/WaterGAP_2.2e_global_parameters_basin_{self.basin_id}.nc"
                with xr.open_dataset(param_path, decode_times=False) as global_params:

                    # Update gamma in the dataset
                    global_params['stat_corr_fact'].\
                        loc[{"lat": calib_station["lat"].values,
                             "lon":calib_station["lon"].values}] = cfs

                    # Save the modified dataset
                    temp_param_path = f"{base_param_path}/temp_WaterGAP_2.2e_global_parameters.nc"
                    global_params.to_netcdf(temp_param_path)

                # Replace the original file with the updated file
                os.remove(param_path)
                os.replace(temp_param_path, param_path)


def calibrate_parameters(initial_gamma):
    """
    Calibrate Gamma,CFA and CFS (Müller Schmied et al 2021, sect. 4.9).

    Parameters
    ----------
    initial_gamma : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Initialize calibration routine
    state = OptimizationState()
    # =====================================================================
    # Get current calibration station and upstream basin (from super basin X)
    # =====================================================================
    config_file = args.name.split("-")  # Getting station id from config file
    station_id, basin_id = config_file[1], config_file[-1].split(".")[0]
    station_csv_path = f"{state.calib_out_dir}{basin_id}/stations_basin_{basin_id}.csv"

    streamflow_station = pd.read_csv(station_csv_path)

    streamflow_station.set_index('station_id', inplace=True)
    streamflow_station.index = streamflow_station.index.astype(str)

    current_calib_station = streamflow_station.loc[[station_id]]

    watergap_basin = get_basin.\
        SelectUpstreamBasin(cm.run_basin,
                            state.initialize_static.arc_id,
                            current_calib_station,
                            state.initialize_static.lat_lon_arcid,
                            state.initialize_static.upstream_cells)

    # =========================================================================
    #     # Get direct upstream cell for which gamma should be changed
    # ==========================================================================
    get_basin_arcid = np.where(watergap_basin.upstream_basin == 0,
                               state.initialize_static.arc_id, np.nan)

    path = f"{state.calib_out_dir}{basin_id}/prev_upstream_cells.npz"
    if os.path.exists(path):
        prev_upstreamcells = np.load(path)
        update_prev_upstreamcells = \
            {key: prev_upstreamcells[key] for key in prev_upstreamcells.files}

        update_prev_upstreamcells[station_id] = get_basin_arcid

        np.savez_compressed(path,  **update_prev_upstreamcells)

        calib_upstreamcells = [update_prev_upstreamcells[key] for key in update_prev_upstreamcells]
    else:
        calib_upstreamcells = [get_basin_arcid]
        np.savez_compressed(path, **{station_id: get_basin_arcid})

    # contains mask for direct upstreamcells
    calib_unit_gamma_cfa = state.get_direct_upstreamcells(calib_upstreamcells)

    # =========================================================================
    # Get observed discharge per station
    # =========================================================================
    state.get_observed_discharge(station_id, basin_id)

    # =========================================================================
    # Now run calibration CS1-CS4
    # =========================================================================
    try:

        # Capping gamma to bounds after the 1st iteration so that if
        # the error or bias is still not +-1% in the 2nd iteration.
        # we already skip to CS2-CS4
        print(colored(f"Running initial check for gamma bounds for Station ID: {station_id}",
                      'light_yellow'))

        gamma_bounds = state.check_gamma_bounds(initial_gamma, current_calib_station,
                                                watergap_basin, calib_unit_gamma_cfa)

        print(colored('\n' + f"Running calibration for station Station ID: {station_id} " +
                      f"with gamma in range (or at) {gamma_bounds}", 'light_yellow'))
        if state.calibration_status != 2:
            # CS1
            new_init_gamma = np.mean(gamma_bounds)
            minimize(state.calib_cs1, x0=new_init_gamma, method="powell",
                     bounds=gamma_bounds, args=(current_calib_station, watergap_basin,
                                                calib_unit_gamma_cfa),
                     options={'maxfev':10})

        else:
            # CS2
            state.calib_cs2(state.currrent_gamma)

            # CS3
            state.calib_cs3(calib_unit_gamma_cfa)

            # CS4
            state.calib_cs4(current_calib_station, watergap_basin)

            print('\n' + f'Calibration status: {state.calibration_status}')
    except Exception as e:
        print(e)


if __name__ == "__main__":
    GAMMA_GUESS = 2
    calibrate_parameters(GAMMA_GUESS)
