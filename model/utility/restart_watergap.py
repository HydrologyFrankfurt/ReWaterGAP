# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Restart from saved state."""
# =============================================================================
# This module saves restart information to file
# =============================================================================

import pickle
import logging
import os
import sys
import glob
from pathlib import Path
import watergap_logger as log
import misc.cli_args as cli
import pandas as pd


# ===============================================================
# Get module name and remove the .py extension
# Module name is passed to logger
# ===============================================================
modname = os.path.basename(__file__)
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
                  landwaterfrac_excl_glolake_res, land_and_water_freq_flag,
                  water_freq, land_freq, updated_loclake_frac,
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
        date : datetime
            The date for which the model state is being saved.
        current_landarea_frac : array
            The current fraction of land area, Unit: [-] 
        previous_landarea_frac : array
            The fraction of land area in the previous day,  Unit: [-] 
        landareafrac_ratio : array
            The ratio of land area fractions (prev/current),  Unit: [-] 
        previous_swb_frac: array
            Previous sum of surafce water bodies fracion (local lake and local 
            and global  wetland), Unit: [-] 
        glores_frac_prevyear: array
            Global reservoirs/regulated lakes fraction of previous year,  Unit: [-] 
        gloresfrac_change:  array
            Change in global reservoirs/regulated lakes fraction,  Unit: [-] 
        init_landfrac_res_flag: 
            Flag to compute land area fraction with reservoir or regulated 
            once at model start, Unit: [-] 
        landwaterfrac_excl_glolake_res : array
            Land water fracion without  global lakes and reservoirs/regulated lakes. 
        land_and_water_freq_flag: array
            Flag to compute land and water fractions,  Unit: [-] 
        water_freq: array
            Water fraction is sum of global lake, local lake, & global 
            reservoir (includes regulated lake) fraction, Unit: [-] 
        land_freq: array
            land fraction is (continental fraction minus water_freq) and 
            contains wetlands, Unit: [-]  
        updated_loclake_frac: array
            updated local lake fraction based on area reduction factor,  Unit: [-] 
        lai_days_since_start : int
            The number of days since the start of the model simulation for LAI, 
            Unit: [days] 
        lai_cum_precipitation : array
            Cumulative precipitation for LAI calulation,  Unit: [mm/day]    
        lai_growth_status : str
            Growth status for LAI calulation, Unit: [-]   
        canopy_storage : array
            Storage of water in the canopy,  Unit: [mm]   
        snow_storage : array
            Snow storage, Unit: [mm]   
        snow_storage_subgrid : array
            The subgrid-specific snow storage, Unit: [mm]    
        soil_water_content : array
            Water content in the soil, Unit: [mm]    
        daily_storage_transfer : array
            The daily storage transfer for land when land area fraction is zero,
            Unit: [mm]    
        groundwater_storage : array
            Groundwater storage, Unit: [km^3].   
        loclake_storage : array
            Local lake storage, Unit: [km^3].    
        locwet_storage : array
            Local wetland storage, Unit: [km^3].    
        glolake_storage : array
            Global lake storage, Unit: [km^3]. 
        glowet_storage : array
            Global wetland storage, Unit: [km^3].   
        river_storage : array
            River storage, Unit: [km^3].   
        glores_storage : array
            Global reservoir, Unit: [km^3].  
        k_release : array
            The release factor for reservoir operation, Unit: [-]    
        unsatisfied_potential_netabs_riparian : array
            Unsatisfied potential net abstraction for riparian cells, Unit: [km^3/day].
        unsat_potnetabs_sw_from_demandcell : array
            Unsatisfied potential net abstraction of surface water from demand cells
            to be given to the supply cells, Unit: [km^3/day]. 
        unsat_potnetabs_sw_to_supplycell : array
            Unsatisfied potential net abstraction to supply cell (multiple 
            demand cell can supply to one supply cell), Unit: [km^3/day]
        neighbouring_cells_map : array
            A map of neighboring cells.   
        accumulated_unsatisfied_potential_netabs_sw : array
            Accumulated unsatisfied potential net abstraction of surface water, Unit: [km^3/day]
        daily_unsatisfied_pot_nas : array
            Daily unsatisfied potential net abstraction from surface water, Unit: [km^3/day]
        prev_accumulated_unsatisfied_potential_netabs_sw : array
            Previous accumulated unsatisfied potential net abstraction of surface water, 
            Unit: [km^3/day]
        prev_potential_water_withdrawal_sw_irri : array
            Previous potential water withdrawal from surface water for irrigation, Unit: [km^3/day]
        prev_potential_consumptive_use_sw_irri : array
            Previous potential consumptive use from irrigation using surface water, Unit: [km^3/day]
        set_res_storage_flag : bool
            Flag indicating whether to set reservoir storage.

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
                          "init_landfrac_res_flag": init_landfrac_res_flag,
                          "landwaterfrac_excl_glolake_res":
                              landwaterfrac_excl_glolake_res,
                          "land_and_water_freq_flag": land_and_water_freq_flag,
                          "water_freq": water_freq,
                          "land_freq": land_freq,
                          "updated_loclake_frac": updated_loclake_frac,
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
                          "neighbouring_cells_map": neighbouring_cells_map,
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
                          "set_res_storage_flag": set_res_storage_flag}

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
        prev_date : datetime
            Previous day of simulation.

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
