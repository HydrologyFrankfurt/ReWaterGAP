# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Setup files and folders for calibration."""


import os
from pathlib import Path
import glob
import json
import shutil
import xarray as xr
import pandas as pd
import numpy as np
from calibration import create_discharge_data as create_dis
from controller import configuration_module as cm
from controller import staticdata_handler as sd


class SetupCalibration:
    """Set up WaterGAP calibration."""

    def __init__(self):
        self.initialize_static = sd.StaticData(cm.run_calib)
        self.start_year = int(cm.start.split("-")[0])
        self.end_year = int(cm.end.split("-")[0])
        self.config_path = './Config_ReWaterGAP.json'
        self.station_per_superbasin_path = './calibration/stations_per_superbasin.nc'
        self.calib_out_dir = "./calibration/calib_out/"
        self.super_basin = None
        self.unique_basin_values = None

    def cleanup_simulation_files(self):
        """
        Remove old wateruse data if any.

        Returns
        -------
        None.

        """
        water_use_path = str(Path(cm.water_use_data_path + r'/*'))
        file_patterns = [fpath for fpath in
                         glob.glob(water_use_path)
                         if 'atotuse' in
                         os.path.basename(fpath)]
        for file in file_patterns:
            if os.path.exists(file):
                os.remove(file)

    def copy_actual_net_abstraction(self):
        """
        Copy actaual abrstaction from surfaace and ground water.

        This data are copied into wateruse directory which will then
        be used for calibration.

        Returns
        -------
        None.

        """
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

    def generate_calib_structure(self):
        """
        Generate folders based on super basin for paralellization.

        Returns
        -------
        None.

        """
        self.super_basin = xr.open_dataarray(self.station_per_superbasin_path)
        unique_values_nan = np.unique(self.super_basin)
        self.unique_basin_values = unique_values_nan[~np.isnan(unique_values_nan)].astype(np.int32)

        for value in self.unique_basin_values:
            folder_name = os.path.join(self.calib_out_dir, str(value))

            os.makedirs(folder_name, exist_ok=True)

            # Create subfolders within each unique value folder
            os.makedirs(os.path.join(folder_name, 'station_config_files'), exist_ok=True)
            os.makedirs(os.path.join(folder_name, 'station_observed_discharge'), exist_ok=True)



    def reorder_calib_stations(self):
        """
        Order stations to match routing order.

        create respective observed discharge per station with complete years
        usable for caibration (csv).

        Returns
        -------
        None.

        """
        # =====================================================================
        # Initialise static data for calibrations and order stations to match
        # routing order
        # =====================================================================
        # create a copy of the stations file
        streamflow_station = self.initialize_static.stations.copy()
        streamflow_station.set_index(['lon', 'lat'], inplace=True)
        routing_order = self.initialize_static.rout_order

        arcids_for_reordering = self.initialize_static.lat_lon_arcid.drop(columns=['GCRC'])
        # round data to 2 decimal place (eg. -46.7499999999999 = -46.75)
        arcids_for_reordering = arcids_for_reordering.round(2)
        arcids_for_reordering = arcids_for_reordering.set_index('ArcID').T.to_dict('list')

        # Get station id
        all_station_ids = pd.read_csv("./calibration/StationsID_ArcID.csv")
        all_station_ids.set_index('WLM_AID', inplace=True)

        ordered_stations_list = []

        for _, row in routing_order.iterrows():
            routing_id = row['rout_order_arcid']

            if routing_id in arcids_for_reordering:
                lon, lat = arcids_for_reordering[routing_id]

                # Directly access the row you need using the index
                if (lon, lat) in streamflow_station.index:

                    station_row = streamflow_station.loc[(lon, lat)]
                    basin_station_id = int(self.super_basin.sel(lat=lat, lon=lon).values)
                    current_station_id = all_station_ids.loc[routing_id].values[0]
                    ordered_stations_list.append({'station_id': current_station_id,
                                                  'lon': station_row.name[0],
                                                  'lat': station_row.name[1],
                                                 'basin_id': basin_station_id})

                    self.generate_config_and_discharge_for_station(current_station_id,
                                                                   basin_station_id)

        reordered_stations = pd.DataFrame(ordered_stations_list)
        # Group by 'basin_id'
        grouped = reordered_stations.groupby('basin_id')

        # Split DataFrame based on unique basin_id values and save each group
        # as a separate CSV file
        for basin_id, group in grouped:
            group = group.drop(columns=['basin_id'])
            out_csv_path = f"{self.calib_out_dir}{basin_id}/stations_basin_{basin_id}.csv"
            if os.path.exists(out_csv_path):
                os.remove(out_csv_path)
            group.to_csv(out_csv_path, index=False)

    # Generate observed discharge and configuration file for all stations
    def generate_config_and_discharge_for_station(self, station_id, basin_id):
        """
        Generate configuration json file per station.

        create station specific observed discharge as csv.

        Parameters
        ----------
        station_id : str
            Station identifier.

        Returns
        -------
        None.

        """
        # load obsered discharge and check max and min time.
        station_file_path = (cm.observed_discharge_filepath + "/" +
                             station_id + "_annual.json")

        load_obs_dis = create_dis.load_data(station_file_path)
        discharge_data = create_dis.generate_river_dis_calib(load_obs_dis)

        # convert to km3/year
        km3_year = (365 * 24 * 60 * 60) / 1000000000.0
        discharge_data = discharge_data * km3_year

        out_dis_path = (
           f"{self.calib_out_dir}{basin_id}/station_observed_discharge/"
           f"{station_id}_observed_discharge.csv")

        discharge_data.to_csv(out_dis_path)

        station_start_year = str(discharge_data.index[0]) + "-01-01"
        station_end_year = str(discharge_data.index[-1]) + "-12-31"

        with open(self.config_path, encoding='utf-8') as file:
            config_file = json.load(file)

        config_file['RuntimeOptions'][2]["SimulationPeriod"]["start"] = station_start_year
        config_file['RuntimeOptions'][2]["SimulationPeriod"]["end"] = station_end_year
        config_file['RuntimeOptions'][4]["SimulationExtent"]["run_basin"] = True
        config_file['RuntimeOptions'][5]["Calibrate WaterGAP"]["run_calib"] = True
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]["streamflow"] = True
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]["pot_cell_runoff"] = True
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]\
            ["actual_net_abstr_groundwater"] = False
        config_file['OutputVariable'][2]["LateralWaterBalanceFluxes"]\
            ["actual_net_abstr_surfacewater"] = False
        config_file['RuntimeOptions'][0]['SimulationOption']\
            ['Demand_satisfaction_opts']['neighbouring_cell'] = False

        config_file['OutputVariable'][1]["VerticalWaterBalanceStorages"]\
            ["maximum_soil_moisture"] = False

        out_config_path = (
            f"{self.calib_out_dir}{basin_id}/station_config_files/"
            f"Config_ReWaterGAP-{station_id}-{basin_id}.json" )

        with open(out_config_path, 'w', encoding='utf-8') as file:
            json.dump(config_file, file, indent=2)

    def copy_parameter_remove_temp_files(self):
        """
        Copy parameter files and remove old upstream cells mask.

        Returns
        -------
        None.

        """
        for i in self.unique_basin_values:
            path = f"{self.calib_out_dir}{i}/prev_upstream_cells.npz"
            if os.path.exists(path):
                os.remove(path)
            
            
            src_file_pattern ='model/WaterGAP*.nc'
            matching_files = glob.glob(src_file_pattern)
            src_file_path = matching_files[0]

            dest_file_path = f"{self.calib_out_dir}{i}/{src_file_path.split('/')[-1].replace('.nc', f'_{i}.nc')}"
            shutil.copy2(src_file_path, dest_file_path)


def run_calib_setup():
    """
    Run calibration setup function that does the following.

    1. Copy actual abstractions to calibration folder.
    2. Create configuration file per station and read in station specific
    observed discharge.

    Returns
    -------
    None.

    """
    calib_setup = SetupCalibration()
    calib_setup.copy_actual_net_abstraction()
    calib_setup.generate_calib_structure()
    calib_setup.reorder_calib_stations()
    calib_setup.copy_parameter_remove_temp_files()


if __name__ == "__main__":
    run_calib_setup()
