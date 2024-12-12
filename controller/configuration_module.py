# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Configuration parser function."""

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
modname = os.path.basename(__file__)
modname = modname.split('.')[0]

# ++++++++++++++++++++++++++++++++++++++++++++++++
# Parsing  Arguments for CLI from cli_args module
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
        return content of the configuration file.

    """
    try:
        with open(filename, encoding="utf-8") as config:
            config_content = json.load(config)
    except FileNotFoundError as error:
        log.config_logger(logging.ERROR, modname, f'Configuration file '
                          f'not found: {error} ', args.debug)
        sys.exit()  # don't run code if configuration file does not exist
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

# For Anthropogenic run (ant=True) or Naturalised run (ant=false).
ant = antnat_opts['ant']
# Enable or disable water use
SUBTRACT_USE = antnat_opts['subtract_use']
# Enable or disable reservoir operation
RESERVOIR_OPT = antnat_opts['res_opt']

# Temporal and spatial satisfaction options
demand_satisfaction_opts = \
    config_file['RuntimeOptions'][0]['SimulationOption']['Demand_satisfaction_opts']

DELAYED_USE = demand_satisfaction_opts['delayed_use']
NEIGHBOURING_CELL = demand_satisfaction_opts['neighbouring_cell']


# Disable water use and reservoir if run is Naturalised
if ant is False:
    SUBTRACT_USE = False
    RESERVOIR_OPT = False
    DELAYED_USE = False
    NEIGHBOURING_CELL = False

# Error Handling
# Here one forgot to either activate  reservoir operation or
# subtract use in anthropogenic mode
if ant and RESERVOIR_OPT is False and SUBTRACT_USE is False:
    MSG = ' None of the variant in anthropogenic run is ' + \
          'activated (reservoir operation , water use or both). ' + \
          'Please choose an option'
    log.config_logger(logging.ERROR, modname, MSG, args.debug)
    sys.exit()  # don't run code if configuration file does not exist

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
if RESERVOIR_OPT:
    reservoir_start_year = sim_period["reservoir_start_year"]
    reservoir_end_year = sim_period["reservoir_end_year"]

    # create an array of date of only first days from reservior_start_year
    # to reservoir_end_year
    RESERVOIR_OPT_YEARS = \
        pd.date_range(str(reservoir_start_year)+"-01-01",
                      str(reservoir_end_year)+"-01-01", freq="YS")
    RESERVOIR_OPT_YEARS = RESERVOIR_OPT_YEARS.values.astype('datetime64[D]')
else:
    RESERVOIR_OPT_YEARS = 0
# =============================================================================
# # Temporal resolution
# =============================================================================
dailyRes = config_file['RuntimeOptions'][3]['TimeStep']['daily']

if dailyRes:
    TEMPORAL_RES = 'Daily'
else:
    log.config_logger(logging.ERROR, modname, 'WaterGAP currently has only '
                      'daily resolution ', args.debug)
    sys.exit()  # don't run code if configuration file does not exist


# =============================================================================
# # Simulation Extent
# =============================================================================
extent_options = config_file['RuntimeOptions'][4]['SimulationExtent']
run_basin = extent_options["run_basin"]
path_to_stations_file = extent_options['path_to_stations_file']

# =============================================================================
# # Selection of output variable (fluxes, storages and flows)
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
restart_save_option = config_file['RuntimeOptions'][1]['RestartOptions']
restart = restart_save_option['restart']
save_states = restart_save_option['save_model_states_for_restart']
save_and_read_states_path = restart_save_option["save_and_read_states_dir"]


# =============================================================================
# Run WaterGAP calibration
# =============================================================================
calibration_options = config_file['RuntimeOptions'][5]["Calibrate WaterGAP"]
run_calib = calibration_options["run_calib"]
observed_discharge_filepath = calibration_options["path_to_observed_discharge"]
