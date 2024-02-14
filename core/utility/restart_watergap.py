# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Restart."""
# =============================================================================
# This module saves restart information to file
# =============================================================================

import pickle
import logging
import os
import sys
import glob
import watergap_logger as log
import misc.cli_args as cli
import pandas as pd
from pathlib import Path

# ===============================================================
# Get module name and remove the .py extension
# Module name is passed to logger
# ===============================================================
modname = (os.path.basename(__file__))
modname = modname.split('.')[0]

# ++++++++++++++++++++++++++++++++++++++++++++++++
# Parsing  Argguments for CLI from cli_args module
# +++++++++++++++++++++++++++++++++++++++++++++++++
args = cli.parse_cli()


class RestartState:
    """Collect the restart states at the end of the simulation."""

    def __init__(self, save_and_read_states_path):
        self.state = {}
        self.save_and_read_states_path = str(Path(save_and_read_states_path))

    def savestate(self, date,
                  current_landarea_frac, previous_landarea_frac,
                  landareafrac_ratio, previous_swb_frac, glores_frac_prevyear,
                  gloresfrac_change, init_landfrac_res_flag, 
                  lai_days_since_start, lai_cum_precipitation, 
                  lai_growth_status, canopy_storage,
                  snow_storage, snow_storage_subgrid, soil_water_content,
                  daily_storage_transfer, groundwater_storage, loclake_storage,
                  locwet_storage,  glolake_storage, glowet_storage,
                  river_storage, glores_storage, k_release,
                  unsatisfied_potential_netabs_riparian,
                  unsat_potnetabs_sw_from_demandcell,
                  unsat_potnetabs_sw_to_supplycell,
                  neighbouring_cells_map,
                  accumulated_unsatisfied_potential_netabs_sw,
                  daily_unsatisfied_pot_nas,
                  prev_accumulated_unsatisfied_potential_netabs_sw,
                  prev_potential_water_withdrawal_sw_irri,
                  prev_potential_consumptive_use_sw_irri,
                  set_res_storage_flag):
        """
        Write variable to file for only a day before the restart date.

        Parameters
        ----------
        date : TYPE
            DESCRIPTION.
        current_landarea_frac : TYPE
            DESCRIPTION.
        previous_landarea_frac : TYPE
            DESCRIPTION.
        landareafrac_ratio : TYPE
            DESCRIPTION.
        lai_days_since_start : TYPE
            DESCRIPTION.
        lai_cum_precipitation : TYPE
            DESCRIPTION.
        lai_growth_status : TYPE
            DESCRIPTION.
        canopy_storage : TYPE
            DESCRIPTION.
        snow_storage : TYPE
            DESCRIPTION.
        snow_storage_subgrid : TYPE
            DESCRIPTION.
        soil_water_content : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        date = pd.to_datetime(str(date))
        date = date.strftime('%Y-%m-%d')

        landfrac_state = {"current_landareafrac": current_landarea_frac,
                          "previous_landareafrac": previous_landarea_frac,
                          "landareafrac_ratio": landareafrac_ratio,
                          "previous_swb_frac": previous_swb_frac,
                          "glores_frac_prevyear": glores_frac_prevyear,
                          "gloresfrac_change": gloresfrac_change,
                          "init_landfrac_res_flag": init_landfrac_res_flag
                          }

        vert_bal_states = {"lai_days_since_start": lai_days_since_start,
                           "cum_precipitation": lai_cum_precipitation,
                           "growth_status": lai_growth_status,

                           # storages before restart date
                           "canopy_storage": canopy_storage,
                           "snow_water_stor": snow_storage,
                           "snow_water_storsubgrid": snow_storage_subgrid,
                           "soil_water_content": soil_water_content,
                           "daily_storage_transfer": daily_storage_transfer}

        lat_bal_states = {"groundwater_storage": groundwater_storage,
                          "loclake_storage": loclake_storage,
                          "locwet_storage": locwet_storage,
                          "glolake_storage": glolake_storage,
                          "glowet_storage": glowet_storage,
                          "river_storage": river_storage,
                          "glores_storage": glores_storage,
                          "k_release": k_release,
                          "unsatisfied_potential_netabs_riparian":
                              unsatisfied_potential_netabs_riparian,
                          "unsat_potnetabs_sw_from_demandcell":
                              unsat_potnetabs_sw_from_demandcell,
                          "unsat_potnetabs_sw_to_supplycell":
                              unsat_potnetabs_sw_to_supplycell,
                          "neighbouring_cells_map" : neighbouring_cells_map, 
                          "accumulated_unsatisfied_potential_netabs_sw":
                              accumulated_unsatisfied_potential_netabs_sw,
                          "daily_unsatisfied_pot_nas":
                              daily_unsatisfied_pot_nas,
                          "prev_accumulated_unsatisfied_potential_netabs_sw":
                              prev_accumulated_unsatisfied_potential_netabs_sw,
                          "prev_potential_water_withdrawal_sw_irri":
                              prev_potential_water_withdrawal_sw_irri,
                          "prev_potential_consumptive_use_sw_irri":
                              prev_potential_consumptive_use_sw_irri, 
                          "set_res_storage_flag": set_res_storage_flag }

        self.state.update({"last_date": date,
                          "landfrac_state": landfrac_state,
                           "vert_bal_states": vert_bal_states,
                           "lat_bal_states": lat_bal_states})

        file_path = os.path.join(self.save_and_read_states_path,
                                 'restartwatergap_' + str(date) + '.pickle')

        with open(file_path, 'wb') as file:
            pickle.dump(self.state, file)

    def load_restart_info(self, prev_date):
        """
        Load restart information.

        Returns
        -------
        restart_data : TYPE
            DESCRIPTION.

        """
        try:
            read_path = os.path.join(self.save_and_read_states_path,
                                     "*"+prev_date+".pickle")
            path = glob.glob(read_path)
            with open(path[0], 'rb') as rf:
                restart_data = pickle.load(rf)
        except IndexError:
            log.config_logger(logging.ERROR, modname, 'Restart data file'
                              ' (restartwatergap_'+prev_date+'.pickle) '
                              'not found. ' + '\n' +
                              'Restart date may also be later or further than '
                              'date of saved states --> Check '
                              '*SimilationPeriod* in configuration file',
                              args.debug)
            sys.exit()  # dont run code if Restart information does not exist
        else:
            print('Restart data loaded successfully')
        return restart_data
