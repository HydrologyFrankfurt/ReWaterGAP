# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Configuartion parser function."""

import json
import logging
import os
import sys
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

# ===============================================================
# Reading in configuration file and handling file related errors)
# ===============================================================


def config_handler(filename):
    """
    Handle all configuration file.

    Parameters
    ----------
    filename : str
        configuration filename

    Returns
    -------
    config_content : dict
        return content of the configuation file.

    """
    try:
        with open(filename) as config:
            config_content = json.load(config)
    except FileNotFoundError:
        log.config_logger(logging.ERROR, modname, 'Configuration file '
                          'not found', args.debug)
        sys.exit()  # don't run code if cofiguration file does not exist
    else:
        print('Configuration loaded successfully')
    return config_content


config_file = config_handler(args.name)

# =============================================================================
# Get path for climate forcing, water use and static land data
# =============================================================================
input_dir = config_file['FilePath']['inputDir']
climate_forcing_path = input_dir['climate_forcing']
water_use_data_path = input_dir['water_use_data']
static_land_data_path = input_dir['static_land_data']

# =============================================================================
# # Initializing Runtime Options (bottleneck to run simulation)
# =============================================================================
antnat_opts = \
    config_file['RuntimeOptions'][0]['SimulationOption']['AntNat_opts']

# For Anthropenic run (ant=True) or Naturalised run (ant=false).
ant = antnat_opts['ant']
# Enable or disable wateruse
subtract_use = antnat_opts['subtract_use']
# Enable or disable reservoir operation
reservior_opt = antnat_opts['res_opt']

# Temporal and spatial satisfaction options
demand_satisfaction_opts = \
    config_file['RuntimeOptions'][0]['SimulationOption']['Demand_satisfaction_opts']

delayed_use = demand_satisfaction_opts['delayed_use']
neighbouringcell = demand_satisfaction_opts['neighbouring_cell']


# Disable wateruse and reservoir if run is Naturalised
if ant is False:
    subtract_use = False
    reservior_opt = False
    delayed_use = False
    neighbouringcell = False

# Error Handling
# Here one forgot to either activate  reservoir operation or
# substract use in anthropogenic mode
if ant is True and reservior_opt is False and subtract_use is False:
    msg = ' None of the variant in anthropogenic run is ' + \
          'activated (reservoir opetration , wateruse or both). ' + \
          'Please choose an option'
    log.config_logger(logging.ERROR, modname, msg, args.debug)
    sys.exit()  # don't run code if cofiguration file does not exist

# =============================================================================
# # Initializing  simulation and spinup period
# =============================================================================
sim_period = config_file['RuntimeOptions'][2]['SimulationPeriod']

start = sim_period['start']
end = sim_period['end']
spinup_years = sim_period['spinup_years']

# +++++++++++++++++++++++++++++++
# Reservoir operation duration
# +++++++++++++++++++++++++++++++
if reservior_opt is True:
    reservoir_start_year = sim_period["reservoir_start_year"]
    reservoir_end_year = sim_period["reservoir_end_year"]

    # create an array of date of only first days from reservior_start_year
    # to reservoir_end_year
    reservoir_opt_years = \
        pd.date_range(str(reservoir_start_year)+"-01-01",
                      str(reservoir_end_year)+"-01-01", freq="YS")
    reservoir_opt_years = reservoir_opt_years.values.astype('datetime64[D]')
else:
    reservoir_opt_years = 0
# =============================================================================
# # Temporal resoulution
# =============================================================================
dailyRes = config_file['RuntimeOptions'][3]['TimeStep']['daily']

if dailyRes is True:
    temporal_res = 'Daily'
else:
    log.config_logger(logging.ERROR, modname, 'WaterGAP currently has only '
                      'daily resolution ', args.debug)
    sys.exit()  # don't run code if cofiguration file does not exist


# =============================================================================
# # Simulation Extent
# =============================================================================
extent_options = config_file['RuntimeOptions'][4]['SimulationExtent']
run_basin = extent_options["run_basin"]
path_to_stations_file = extent_options['path_to_stations_file']

# =============================================================================
# # Selection of ouput variable (fluxes, storages and flows)
# =============================================================================
# Vertical Water Balance (vb)
vb_fluxes = config_file['OutputVariable'][0]['VerticalWaterBalanceFluxes']
vb_storages = config_file['OutputVariable'][1]['VerticalWaterBalanceStorages']

# Lateral Water Balance (lb)
lb_fluxes = config_file['OutputVariable'][2]['LateralWaterBalanceFluxes']
lb_storages = config_file['OutputVariable'][3]['LateralWaterBalanceStorages']

# =============================================================================
# # Save and restart WaterGAP state
# =============================================================================
resart_save_option = config_file['RuntimeOptions'][1]['RestartOptions']
restart = resart_save_option['restart']
save_states = resart_save_option['save_model_states_for_restart']
save_and_read_states_path = resart_save_option["save_and_read_states_dir"]
