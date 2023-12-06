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
        sys.exit()  # dont run code if cofiguration file does not exist
    else:
        print('Configuration loaded successfully')
    return config_content


config_file = config_handler(args.name)

# =============================================================================
# Get path for climate forcing, water use and static land data
# =============================================================================
climate_forcing_path = config_file['FilePath']['inputDir']['climate_forcing']
water_use_data_path = config_file['FilePath']['inputDir']['water_use_data']
static_land_data_path = config_file['FilePath']['inputDir']['static_land_data']

# =============================================================================
# # Initializing Runtime Options (bottleneck to run simulation)
# =============================================================================
antnat_opts = \
    config_file['RuntimeOptions'][0]['SimulationOption']['AntNat_opts']

# For Anthropenic run (ant=True) or Naturalised run (ant=false).
ant = antnat_opts['ant']
subtract_use = antnat_opts['subtract_use']  # Enable or disable wateruse

# Disable wateruse if run is Naturalised
if ant is False:
    subtract_use = False


# Enable or disable reservoir operation
reservior_opt = antnat_opts['res_opt']

# Temporal and spatial satisfaction options
demand_satisfaction_opts = \
    config_file['RuntimeOptions'][0]['SimulationOption']['Demand_satisfaction_opts']

delayed_use = demand_satisfaction_opts['delayed_use']
neighbouringcell = demand_satisfaction_opts['neighbouring_cell']

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Error Handling
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Here one forgot to either activate either reservoir operation or
# substract use in anthropogenic mode
if ant is True and reservior_opt is False and subtract_use is False:
    msg = ' None of the variant in anthropogenic run is ' + \
          'activated (reservoir opetration , wateruse or both). ' + \
          'Please choose an option'
    log.config_logger(logging.ERROR, modname, msg, args.debug)
    sys.exit()  # dont run code if cofiguration file does not exist
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Reservoir operation duration
reservoir_start_year = 1901
reservoir_end_year = 1905

# create an array of date of only first days from reservior_start_year
# to reservoir_end_year
reservoir_opt_years = pd.date_range(str(reservoir_start_year)+"-01-01",
                                    str(reservoir_end_year)+"-01-01", freq="YS")

# =============================================================================
# # Save and restart WaterGAP state
# =============================================================================
restart = config_file['RuntimeOptions'][1]['RestartOptions']['restart']
save_states = config_file['RuntimeOptions'][1]['RestartOptions']['save_model_states_for_restart']

# =============================================================================
# # Initializing  simulation and spinup period
# =============================================================================
start = config_file['RuntimeOptions'][2]['SimilationPeriod']['start']
end = config_file['RuntimeOptions'][2]['SimilationPeriod']['end']
spinup_years = \
    config_file['RuntimeOptions'][2]['SimilationPeriod']['spinup_years']

# =============================================================================
# # Temporal resoulution
# =============================================================================
dailyRes = config_file['RuntimeOptions'][3]['TimeStep']['daily']

if dailyRes is True:
    temporal_res = 'Daily'
else:
    log.config_logger(logging.ERROR, modname, 'WaterGAP currently has only '
                      'daily resolution ', args.debug)
    sys.exit()  # dont run code if cofiguration file does not exist


# =============================================================================
# # Selection of ouput variable (fluxes, storages and flows)
# =============================================================================
# Vertical Water Balance (vb)
vb_fluxes = config_file['OutputVariable'][0]['VerticalWaterBalanceFluxes']
vb_storages = config_file['OutputVariable'][1]['VerticalWaterBalanceStorages']

# Lateral Water Balance (lb)
lb_fluxes = config_file['OutputVariable'][2]['LateralWaterBalanceFluxes']
lb_storages = config_file['OutputVariable'][3]['LateralWaterBalanceStorages']
