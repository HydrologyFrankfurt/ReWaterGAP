# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 08:16:29 2024

@author: nyenah
"""
from controller import configuration_module as cm
from controller import staticdata_handler as sd
from pathlib import Path
import glob
import os
import json
import shutil
import numpy as np
import xarray as xr
import pandas as pd
import create_discharge_data as create_dis

class SetupCalibration:
    def __init__(self):
        self.initialize_static = sd.StaticData(cm.run_calib)
        self.start_year = int(cm.start.split("-")[0])
        self.end_year = int(cm.end.split("-")[0])
        self.config_path ='./Config_ReWaterGAP.json'

    def cleanup_simulation_files(self,):
        water_use_path =  str(Path(cm.water_use_data_path + r'/*'))
        file_patterns = [fpath for fpath in 
                            glob.glob(water_use_path) 
                             if 'atotuse' in 
                             os.path.basename(fpath)]
        for file in file_patterns:
                if os.path.exists(file):
                    os.remove(file)
    
    def copy_actual_net_abstraction(self):
    
        self.cleanup_simulation_files()
        
        actual_nag = xr.open_mfdataset("output_data/atotusegw_*.nc")
        actual_nas = xr.open_mfdataset("output_data/atotusesw_*.nc")
    
        continental_frac = self.initialize_static.land_surface_water_fraction.contfrac.values
        mm_m3 = self.initialize_static.cell_area * 1e6 * (continental_frac / 100) / 1e3
        s_to_day = 86400
    
        actual_nag = actual_nag.atotusegw * mm_m3 * s_to_day
        actual_nag = actual_nag.resample(time="M").sum() * (continental_frac / continental_frac)
    
        actual_nas = actual_nas.atotusesw * mm_m3 * s_to_day
        actual_nas = actual_nas.resample(time="M").sum() * (continental_frac / continental_frac)
    
    
        wateruse_path = "input_data/water_use/"
        # Iterate over each 10-year period
        for start_year in range(self.start_year, self.end_year + 1, 10):
            end_year = min(start_year + 9, self.end_year)
        
            # Filter data for the current 10-year period
            period_nag = actual_nag.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
            period_nas = actual_nas.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
        
            # Create file paths
            period_nag_path = os.path.join(wateruse_path, f"atotusegw_{start_year}_{end_year}.nc")
            period_nas_path = os.path.join(wateruse_path, f"atotusesw_{start_year}_{end_year}.nc")
        
            # Write out the data for the current 10-year period
            period_nag.to_netcdf(period_nag_path)
            period_nas.to_netcdf(period_nas_path)
    
    def reorder_calib_stations(self):
        # =====================================================================
        # Initialise static data for calibrations and order stations to match 
        # routing order
        # ======================================================================
        streamflow_station = self.initialize_static.stations
        streamflow_station.set_index(['lon', 'lat'], inplace=True)
        routing_order=  self.initialize_static.rout_order
        
    
        arcids_for_reordering = self.initialize_static.lat_lon_arcid.drop(columns=['GCRC'])
        arcids_for_reordering = arcids_for_reordering.round(2) # round data to 2 decimal place (eg. -46.7499999999999 = -46.75)
        arcids_for_reordering = arcids_for_reordering.set_index('ArcID').T.to_dict('list')
        
        # Get station id 
        all_station_ids = pd.read_csv('../test_wateruse/StationsID_ArcID.csv')
        all_station_ids.set_index('WLM_AID', inplace=True)


        ordered_stations_list = []
    
        for index, row in routing_order.iterrows():
            routing_id = row['rout_order_arcid']
           
            if routing_id in arcids_for_reordering:
               lon, lat = arcids_for_reordering[routing_id]

               # Directly access the row you need using the index
               if (lon, lat) in streamflow_station.index: 
                   #print(lon, lat)
                   station_row = streamflow_station.loc[(lon, lat)]
                   current_station_id = all_station_ids.loc[routing_id].values[0]
                   ordered_stations_list.append({'station_id': current_station_id, 
                                                 'lon': station_row.name[0], 
                                                 'lat': station_row.name[1]})
                   
                   self.generate_config_and_discharge_for_station(current_station_id)

        reordered_stations = pd.DataFrame(ordered_stations_list)     
        path_to_save = str(Path(cm.path_to_stations_file + r'/stations.csv'))   
        reordered_stations.to_csv(path_to_save, index=False)

    # Generate observed discharge and configuration file for all stations 
    def generate_config_and_discharge_for_station(self, station_id):
        # load opbsered discharge and check max and min time. 
        station_file_path = (cm.observed_discharge_filepath +  "/" + 
                             station_id + "_annual.json")
        
        load_obs_dis = create_dis.load_data(station_file_path)
        discharge_data = create_dis.generate_river_dis(load_obs_dis)
        
        # convert to km3/year
        km3_year = (365 * 24 * 60 * 60) / 1000000000.0
        discharge_data = discharge_data * km3_year
        
        out_dis_path ='../test_wateruse/station_observed_discharge/' + station_id + "_observed_discharge.csv"
        discharge_data.to_csv(out_dis_path)
      
        station_start_year = str(discharge_data.index[0]) + "-01-01"
        station_end_year = str(discharge_data.index[-1]) + "-12-31"
         
        with open(self.config_path) as file:
            config_file = json.load(file)
        
        config_file['RuntimeOptions'][2]["SimulationPeriod"]["start"] =  station_start_year
        config_file['RuntimeOptions'][2]["SimulationPeriod"]["end"] = station_end_year
        config_file['RuntimeOptions'][4]["SimulationExtent"]["run_basin"] = True
        config_file['RuntimeOptions'][5]["Calibrate WaterGAP"]["run_calib"] = True
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]["streamflow"] = True
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]["pot_cell_runoff"] = True
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]["actual_net_abstr_groundwater"] = False
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]["actual_net_abstr_surfacewater"] = False
        config_file['RuntimeOptions'][0]['SimulationOption']['Demand_satisfaction_opts']['neighbouring_cell'] = False
        
        
        out_config_path = "../test_wateruse/station_config_files/Config_ReWaterGAP-"+ station_id + ".json" 
        with open(out_config_path, 'w') as file:
            json.dump(config_file, file, indent=2)
    
    def copy_parameter_remove_temp_files(self): 
        path = '../test_wateruse/prev_upstream_cells.npz'
        if os.path.exists(path):
            os.remove(path)
        
        src_file_path='core/WaterGAP_2.2e_global_parameters.nc'
        dest_file_path='../test_wateruse/WaterGAP_2.2e_global_parameters.nc'
        shutil.copy2(src_file_path, dest_file_path)   


def run_calib_setup():
    calib_setup = SetupCalibration()
    calib_setup.copy_actual_net_abstraction()
    calib_setup.reorder_calib_stations()
    calib_setup.copy_parameter_remove_temp_files()
    
if __name__ == "__main__":
    run_calib_setup()   