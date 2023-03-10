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

    def __init__(self):
        self.state = {}

    def savestate(self, date, current_landarea_frac,
                  previous_landarea_frac, landareafrac_ratio,
                  lai_days_since_start, lai_cum_precipitation,
                  lai_growth_status, canopy_storage, snow_storage,
                  snow_storage_subgrid, soil_water_content,
                  groundwater_storage, loclake_storage, locwet_storage,
                  glolake_storage, glowet_storage, river_storage):
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
                          "landareafrac_ratio": landareafrac_ratio}

        vert_bal_states = {"lai_days_since_start": lai_days_since_start,
                           "cum_precipitation": lai_cum_precipitation,
                           "growth_status": lai_growth_status,

                           # storages before restart date
                           "canopy_storage_prev": canopy_storage,
                           "snow_water_stor_prev": snow_storage,
                           "snow_water_storsubgrid_prev": snow_storage_subgrid,
                           "soil_water_content_prev": soil_water_content}

        lat_bal_states = {"groundwater_storage_prev": groundwater_storage,
                          "loclake_storage_prev": loclake_storage,
                          "locwet_storage_prev": locwet_storage,
                          "glolake_storage_prev": glolake_storage,
                          "glowet_storage_prev": glowet_storage,
                          "river_storage_prev": river_storage}

        self.state.update({"last_date": date,
                          "landfrac_state": landfrac_state,
                           "vert_bal_states": vert_bal_states,
                           "lat_bal_states": lat_bal_states})

        with open('restartwatergap_'+str(date)+'.pickle', 'wb') as file:
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
            path = glob.glob("*"+prev_date+".pickle")
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
