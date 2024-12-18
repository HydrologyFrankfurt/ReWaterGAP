# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Run Calibration"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import json
from termcolor import colored
import pandas as pd
import sys
from calibration import merge_parameters

class CalibrateStations:
    """Calibrate WaterGAP using all stations available."""

    def __init__(self):
        self.config_path = './Config_ReWaterGAP.json'
        self.calib_out_dir = "./calibration/calib_out/"

    def update_config_values(self, obj):
        """
        Update configuration file.

        Parameters
        ----------
        obj : dictionary
            contains configuration options to update.

        Returns
        -------
        None.

        """
        for key, value in obj.items():
            if isinstance(value, dict):
                self.update_config_values(value)
            else:
                # dont modify these
                if "save_and_read_states_dir" in key or "start" in key or 'end' in key\
                    or "reservoir_start_year" in key or "reservoir_end_year"in key\
                    or "spinup_years" in key or "daily" in key \
                    or "path_to_stations_file" in key or "path_to_observed_discharge" in key:

                    pass
                elif "ant" in key or "subtract_use" in key or "res_opt" in key\
                        or "delayed_use" in key or 'actual_net_abstr_' in key\
                        or "maximum_soil_moisture" in key:
                    obj[key] = True
                # handle "get_neighbouring_cells_map" first before
                # "neighbouring cell" in demand satisfaction option to prevent
                # setting the former option to true.
                elif "get_neighbouring_cells_map" in key:
                    obj[key] = False
                elif "neighbouring_cell" in key:
                    obj[key] = True
                else:
                    obj[key] = False

    def modify_config_file(self):
        """
        Modify configuration file to run WaterGAP  for actual abstractions.

        Returns
        -------
        None.

        """
        with open(self.config_path,  encoding='utf-8') as file:
            config_file = json.load(file)

        # Apply the function to each dictionary in the list
        if 'OutputVariable' in config_file:
            for item in config_file['OutputVariable']:
                self.update_config_values(item)

        if 'RuntimeOptions' in config_file:
            for item in config_file['RuntimeOptions']:
                self.update_config_values(item)

        # Save the modified JSON data
        with open('Config_ReWaterGAP.json', 'w',  encoding='utf-8') as file:
            json.dump(config_file, file, indent=2)

    def run_watergap(self):
        """
        Run WaterGAP.

        Returns
        -------
        None.

        """
        subprocess.run(["python3", "run_watergap.py", self.config_path],
                       check=True)

    def process_basin(self, basin_id):
        """
        Run calibration for per station in each basin.

        Parameters
        ----------
        basin_id : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        station_basin_path = f"{self.calib_out_dir}{basin_id}/stations_basin_{basin_id}.csv"
        ordered_stations = pd.read_csv(station_basin_path)

        for i in range(len(ordered_stations)):

            station_id_ordered = ordered_stations['station_id'][i]
            station_config_path = (
                f"{self.calib_out_dir}{basin_id}/station_config_files/Config_ReWaterGAP-"
                f"{station_id_ordered}-{basin_id}.json")

            log_file = open(f"{self.calib_out_dir}{basin_id}/stdout_{station_id_ordered}.log", "w")
            subprocess.run(["python3", "-m", "calibration.find_gamma_cfa_cfs", station_config_path],
                           stdout=log_file)
            log_file.close()

    def run_on_local_server(self, basin_ids, num_threads):
        """
        Run on local server.

        Parameters
        ----------
        basin_ids : TYPE
            DESCRIPTION.
        num_threads : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            executor.map(self.process_basin, basin_ids)

    def run_on_cluster(basin_ids, num_nodes):
        """
        Run on local cluster.

        Parameters
        ----------
        basin_ids : TYPE
            DESCRIPTION.
        num_nodes : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        for basin_id in basin_ids:
            subprocess.run(["sbatch", "--nodes", str(num_nodes), "run_basins.slurm", str(basin_id)])

    def get_number_of_basins(self):
        """
        Get number of basins for parallel computation.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return len([name for name in os.listdir(self.calib_out_dir)
                    if os.path.isdir(os.path.join(self.calib_out_dir, name))])

def main():
    """
    Run calibration steps A and B.

    Returns
    -------
    None.

    """
    try:
        # initialize class
        calib_watergap = CalibrateStations()
        mode = sys.argv[1]  # 'local' or 'cluster'
        num_threads_or_nodes = int(sys.argv[2])  # Number of threads for local or nodes for cluster
        # =====================================================================
        #                       Calibration step A
        # =====================================================================
        # Run WaterGAP globally to get the actual net abstraction from groundwater
        # and  surface water. This will be the water use data for calibration)
        print('\n' + colored("Running Calibration step A...","magenta"))
        calib_watergap.modify_config_file()
        calib_watergap.run_watergap()

        # =====================================================================
        #  Set up files for calibration (generate config file for each station)
        # =====================================================================
        print('\n' + colored("Generating station specific configuration files"
                             " for Calibration step B...", "magenta"))

        subprocess.run(["python3", "-m", "calibration.calibration_setup",
                        calib_watergap.config_path], check=True)

        # =====================================================================
        #                       Calibration step B
        # =====================================================================

        # Optimise WaterGAP parameters
        print('\n' + colored("Running Calibration step B...", "magenta"))
        n = calib_watergap.get_number_of_basins()

        basin_ids = list(range(1, n+1))

        print('\n' + colored("Calibrating " + str(len(basin_ids))+" calibration region(s)...", "blue"))
        if mode == 'local':
            calib_watergap.run_on_local_server(basin_ids, num_threads_or_nodes)
            print('\n' + colored("Calibration complete", "green"))
        elif mode == 'cluster':
            calib_watergap.run_on_cluster(basin_ids, num_threads_or_nodes)
        else:
            print("Invalid mode. Use 'local' or 'cluster'.")

        # =====================================================================
        #                       Calibration step c
        # =====================================================================
        # Here paramater regionlisation is computed for basins with no or
        # limited observations. After, parameters are merged into a single
        # netcdf.
        print('\n' + colored("Running Regionlisation step C...", "magenta"))
        merge_parameters.run_regionalization_merge_parameters(num_threads_or_nodes)
        absolute_param_path = os.path.abspath("./model/WaterGAP_2.2e_global_parameters.nc")
        print('\n' + colored(f"Model parameters merged and saved to {absolute_param_path}", "green"))

    except KeyboardInterrupt:
        os.system("pkill -u $USER python3")


if __name__ == "__main__":
    main()
