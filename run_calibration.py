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
import json
from termcolor import colored
import pandas as pd


class GetActualAbstraction:
    """Run WaterGAP to get actual abstraction."""

    def __init__(self):
        self.config_path = './Config_ReWaterGAP.json'

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
                elif  "ant" in key  or "subtract_use" in key or "res_opt" in key\
                    or "delayed_use" in key  or 'actual_net_abstr_' in key:
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
        os.system(f"python3 run_watergap.py {self.config_path}")


def calibrate_watergap():
    """
    Run calibration steps A and B.

    Returns
    -------
    None.

    """
    # =========================================================================
    #                       Calibration step A
    # =========================================================================
    # Run WaterGAP globally to get the actual net abstraction from groundwater
    # and  surface water. This will be the water use data for calibration)
    print('\n' + colored("Running Calibration step A...","magenta"))
    get_actual_net_abstr = GetActualAbstraction()
    get_actual_net_abstr.modify_config_file()
    # get_actual_net_abstr.run_watergap()

    # =========================================================================
    #    Set up files for calibration (generate config file for each station)
    # =========================================================================
    print('\n'+ colored("Generating station specific configuration files"
                        " for Calibration step B...", "magenta"))
    os.system(f"python3 calibration_setup.py {get_actual_net_abstr.config_path}")

    # =========================================================================
    #                       Calibration step B
    # =========================================================================

    # Optimise WaterGAP parameters
    print('\n'+ colored("Running Calibration step B...", "magenta"))

    # Loop through stations superbasins and stations.
    all_odered_stations = pd.read_csv("input_data/static_input/stations.csv")

    for i in range(len(all_odered_stations)):
        station_id_ordered = all_odered_stations['station_id'][i]
        station_config_path = \
            f"../test_wateruse/station_config_files/Config_ReWaterGAP-{station_id_ordered}.json"
        os.system(f"python3 find_gamma_cfa_cfs.py {station_config_path}")


if __name__ == "__main__":
    calibrate_watergap()
