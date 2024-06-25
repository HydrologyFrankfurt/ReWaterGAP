# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 12:53:19 2024

@author: nyenah
"""
import os
import json
import glob

import numpy as np
import pandas as pd
import xarray as xr
from scipy.optimize import minimize
from termcolor import colored
from pathlib import Path

from controller import configuration_module as cm
from controller import staticdata_handler as sd
from core.utility import get_upstream_basin as get_basin
import run_watergap
import misc.cli_args as cli

args = cli.parse_cli()




"""
#Todo

# now run watergap with these. also make sure potcell runoff is computed  .(calibration is true)
#  try for cs1,cs2  and then cs3 and cs4.
"""

class OptimizationState:
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
        self.gamma_limit=[0.1, 5]
        self.compute_cfs=False

    # Make sure mask contain only direct upstream cells 
    def get_direct_upstreamcells(self, arrays, marker=np.nan):
        # Iterate over each array starting from the second one
        for i in range(1, len(arrays)):
            # Iterate over all previous arrays to mark common values
            for j in range(i):
                arrays[i][np.isin(arrays[i], arrays[j])] = marker

        return arrays[-1]

    def get_observed_discharge(self, station_id):
        obs_dis_path = "../test_wateruse/station_observed_discharge/" 
        station_file_path = f"{obs_dis_path}{station_id}_observed_discharge.csv"
        
        # Load observed data from the csv file
        obs_dis = pd.read_csv(station_file_path) # km3_year
        self.obs_dis = obs_dis


    def calib_cs1(self, gamma, calib_station, watergap_basin, calib_unit_gamma):
        self.currrent_gamma =  gamma
        # Load parameter file and update gamma
        param_path = "../test_wateruse/WaterGAP_2.2e_global_parameters.nc"
        with xr.open_dataset(param_path, decode_times=False) as global_params:
                
            # Update gamma in the dataset
            # calib_unit_gamma is mask of arc_ids every where 
            global_params['gamma'].values = \
                np.where(calib_unit_gamma>0, gamma, 
                         global_params['gamma'].values)  
     
            # Save the modified dataset
            temp_param_path = "../test_wateruse/temp_WaterGAP_2.2e_global_parameters.nc"
            global_params.to_netcdf(temp_param_path)
            
        # Replace the original file with the updated file
        os.remove(param_path)
        os.replace(temp_param_path, param_path)
        # print(global_params['gamma'].sel(lat=calib_station["lat"].values, lon=calib_station["lon"].values))
        
        # run WaterGAP and Get simulated data
        simulated_data = run_watergap.run(calib_station, watergap_basin)
        self.annual_pot_cell_runoff = simulated_data["pot_cell_runoff"]
        
        sim_dis = np.array(simulated_data["sim_dis"])  # km3/year
        sim_years = list(range(self.start_year , self.end_year+1))
        sim_df = pd.DataFrame({ "Year": sim_years, "sim_dis": sim_dis})
        
        # Merge the dataframes on 'Year'. Goal is to remove yearly simulated
        # discharge which is not available in observed discharge data.
        merged_df = pd.merge(sim_df, self.obs_dis, on='Year', how='left')
        filtered_sim_obs_df = merged_df.dropna()
        print(filtered_sim_obs_df)
        
        self.mean_sim_dis = filtered_sim_obs_df['sim_dis'].mean()
        self.mean_obs_dis = filtered_sim_obs_df['obs_dis'].mean()

        
        # Calculate error
        error_cs1 = np.abs((self.mean_sim_dis - self.mean_obs_dis) / self.mean_obs_dis)
        
        print('\n' + f'Bias {error_cs1} for Gamma {gamma[0]}')
        
        # Check if the optimization should be terminated
        if error_cs1 < self.threshold_cs1:
            self.calibration_status = 1
            raise Exception('\n'+ f'Calibration status: {self.calibration_status} - sucessful for Gamma = {gamma[0]} and Bias = {error_cs1}')
    
        return error_cs1

    def calib_cs2(self, gamma):
        min_mean_obs_dis_adapted = self.mean_obs_dis * 0.9
        max_mean_obs_dis_adapted = self.mean_obs_dis * 1.1
        
        check_cs2 = min_mean_obs_dis_adapted  <= self.mean_sim_dis <= max_mean_obs_dis_adapted
        # print( min_mean_obs_dis, self.mean_sim_dis, max_mean_obs_dis, self.mean_obs_dis)
        
        if check_cs2 == True: 
            self.calibration_status = 2
            print('\n'+ f'Calibration status: {self.calibration_status} - sucessful for 10% criterion  with Gamma = {gamma[0]}')
        else:
            self.calibration_status = 3
            print("10% criterion cannot be fulfilled, CFA is calculated." + '\n')
    
    def calib_cs3(self, calib_unit_cfa, calib_station):
        # We need to ensure that CFA is adjusted accordingly for a cell 
        # with either positive (precipitation > evapotranspiration) 
        # and negative (evapotranspiration > precipitation) cell water 
        # balance. 
        #  The sign for a positive and negative cell water balance can be 
        # already seen in the varible potential_cell_runoff (We compute CFA with  
        # potcell runoff because it’s the basis for applying the CFA.)
        # Details can be found here on CFA (https://hess.copernicus.org/articles/12/841/2008/hess-12-841-2008.pdf)
        
        if self.calibration_status == 3:
            self.compute_cfs=True
            # Concatenate along a new dimension and then take the mean along that dimension
            combined_annual_pot_cell_runoff = xr.concat(self.annual_pot_cell_runoff, dim='time')
            mean_pot_cell_runoff = combined_annual_pot_cell_runoff.mean(dim='time')
           
            # get sign of for pot cell runoff station 
            
            mean_pot_cell_runoff_cell = mean_pot_cell_runoff.\
                sel(lat=calib_station["lat"].values, lon=calib_station["lon"].values).values[0][0]
            
            # get meean pot runoff for basin only and take mean over calibration unit.
            mean_pot_cell_runoff_calib_unit = np.where(calib_unit_cfa>0, mean_pot_cell_runoff.values, np.nan)
            mean_pot_cell_runoff_calib_unit = np.nansum(np.abs(mean_pot_cell_runoff_calib_unit)) # aboslute sum over calib unit
           
            
           
            if self.currrent_gamma == self.gamma_limit[0]:
                mean_obs_dis_adapted = self.mean_obs_dis * 0.9
            else: 
                mean_obs_dis_adapted = self.mean_obs_dis * 1.1
    
            
            sign = lambda runoff: np.where(runoff > 0, 1, np.where(runoff < 0, -1, 0)) # answer from this is either 1, -1 or 0
            
            cfa = 1 - (sign(mean_pot_cell_runoff_cell) * (self.mean_sim_dis - mean_obs_dis_adapted) / mean_pot_cell_runoff_calib_unit)
            
            # Limiting correction factor to range 0.5 - 1.5.
            cfa = max(0.5, min( cfa, 1.5))
            print(mean_pot_cell_runoff_cell, mean_pot_cell_runoff_calib_unit, cfa)
            # Load parameter file and update CFA
            param_path = "../test_wateruse/WaterGAP_2.2e_global_parameters.nc"
            with xr.open_dataset(param_path, decode_times=False) as global_params:
                    
                # Update gamma in the dataset
                # calib_unit_gamma is mask of arc_ids every where 
                global_params['areal_corr_factor'].values = \
                    np.where(calib_unit_cfa>0, cfa, 
                              global_params['areal_corr_factor'].values)  
         
                # Save the modified dataset
                temp_param_path = "../test_wateruse/temp_WaterGAP_2.2e_global_parameters.nc"
                global_params.to_netcdf(temp_param_path)
                
            # Replace the original file with the updated file
            os.remove(param_path)
            os.replace(temp_param_path, param_path)
        

    def calib_cs4(self, calib_station, watergap_basin):
        if self.compute_cfs:
            # run WaterGAP and Get simulated data
            simulated_data = run_watergap.run(calib_station, watergap_basin)
            
            sim_dis = np.array(simulated_data["sim_dis"])  # km3/year
            sim_years = list(range(self.start_year , self.end_year+1))
            sim_df = pd.DataFrame({ "Year": sim_years, "sim_dis": sim_dis})
            
            # Merge the dataframes on 'Year'. Goal is to remove yearly simulated
            # discharge which is not available in observed discharge data.
            merged_df = pd.merge(sim_df, self.obs_dis, on='Year', how='left')
            filtered_sim_obs_df = merged_df.dropna()
            print(filtered_sim_obs_df)
            
            self.mean_sim_dis = filtered_sim_obs_df['sim_dis'].mean()
            self.mean_obs_dis = filtered_sim_obs_df['obs_dis'].mean()
            
            if self.currrent_gamma == self.gamma_limit[0]:
                mean_obs_dis_adapted = self.mean_obs_dis * 0.9
            else: 
                mean_obs_dis_adapted = self.mean_obs_dis * 1.1
            # Here, we explicitly calculate CFS to correct the discharge at the grid cell
    
            cfs = mean_obs_dis_adapted / self.mean_sim_dis  # Adjust CFS so that sim_dis equals Qobs
            print(cfs)
            if (1.0 < cfs < 1.01) or (0.99 < cfs < 1.0):
                cfs = 1.0
                print(f"cfs is not far away from 1.0: {cfs}")
            
            print(f"CFS is calculated with Gamma = {self.currrent_gamma}  to be {cfs}")
            if (cfs > 1.0) or (cfs < 1.0):
                self.calibration_status  = 4
            
            
            # Load parameter file and update CFA
            if  self.calibration_status == 4:
                param_path = "../test_wateruse/WaterGAP_2.2e_global_parameters.nc"
                with xr.open_dataset(param_path, decode_times=False) as global_params:
                        
                    # Update gamma in the dataset
                    # calib_unit_gamma is mask of arc_ids every where 
                    global_params['stat_corr_fact'].\
                        loc[dict(lat=calib_station["lat"].values, lon=calib_station["lon"].values)] =cfs
                       
             
                    # Save the modified dataset
                    temp_param_path = "../test_wateruse/temp_WaterGAP_2.2e_global_parameters.nc"
                    global_params.to_netcdf(temp_param_path)
                    
                # Replace the original file with the updated file
                os.remove(param_path)
                os.replace(temp_param_path, param_path)


def calibrate_parameters(initial_gamma, bounds):
    state = OptimizationState()
    streamflow_station = state.initialize_static.stations
    streamflow_station.set_index('station_id', inplace=True)
    streamflow_station.index = streamflow_station.index.astype(str)

    # =====================================================================
    # Get current calibration station and upstream basin 
    # =====================================================================
    config_file =  args.name #  i am getting station id from config file
    station_id = config_file.split("-")[-1].split(".")[0]

    print(colored(f'Running calibration for Station ID: {station_id}', 'light_yellow'))  
    
    current_calib_station = streamflow_station.loc[[station_id]]
   
    watergap_basin = get_basin.\
        Select_upstream_basin(cm.run_basin,
                              state.initialize_static.arc_id,
                              current_calib_station,
                              state.initialize_static.lat_lon_arcid,
                              state.initialize_static.upstream_cells)
    
    
    # =========================================================================
    #     # Get direct upstream cell for which gamma should be changed
    # ==========================================================================
    # basin are marked with arcids
    get_basin_arcid = np.where(watergap_basin.upstream_basin==0, 
                               state.initialize_static.arc_id, np.nan )
    
    path = '../test_wateruse/prev_upstream_cells.npz'
    if os.path.exists(path):
        prev_upstreamcells = np.load('../test_wateruse/prev_upstream_cells.npz')
        update_prev_upstreamcells = {key: prev_upstreamcells[key] for key in prev_upstreamcells.files}
        update_prev_upstreamcells["station_id"] = get_basin_arcid
        np.savez_compressed('../test_wateruse/prev_upstream_cells.npz', 
                            **update_prev_upstreamcells)
        
        calib_upstreamcells = [update_prev_upstreamcells[key] for key in update_prev_upstreamcells]
    else:
        calib_upstreamcells=[get_basin_arcid]
        np.savez_compressed('../test_wateruse/prev_upstream_cells.npz', 
                            **{station_id : get_basin_arcid})
        

    # contains basin mask for direct upstreamcells 
    calib_unit_gamma_cfa_cfs = state.get_direct_upstreamcells(calib_upstreamcells)
    # =========================================================================
    
    # Get observed discharge per station
    state.get_observed_discharge(station_id)
    # =========================================================================
    # calibrate Gamma  (CS1 and CS2)
    # =========================================================================
    try:
       # CS1
        minimize(state.calib_cs1, x0=initial_gamma, method="powell", 
                 bounds=bounds, args=(current_calib_station, watergap_basin, 
                                calib_unit_gamma_cfa_cfs), 
                 options={'ftol':0.0001, 'xtol':0.0001, 'maxfev':1})
        
        # CS2
        state.calib_cs2(state.currrent_gamma)

        # CS3
        state.calib_cs3(calib_unit_gamma_cfa_cfs, current_calib_station)
        
        # CS4
        state.calib_cs4(current_calib_station, watergap_basin)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    initial_gamma = 5
    gamma_bounds = [(0.1, 5.0)]
    calibrate_parameters(initial_gamma, gamma_bounds )




