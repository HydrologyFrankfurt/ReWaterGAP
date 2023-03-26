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

# Initializing Runtime Options (bottleneck to run simulation)
ant = config_file['RuntimeOptions'][0]['SimilationOption']['ant']


restart = config_file['RuntimeOptions'][1]['RestartOptions']['restart']
save_states = config_file['RuntimeOptions'][1]['RestartOptions']['save_model_states_for_restart']

# Initializing  simulation and spinup period 
start = config_file['RuntimeOptions'][2]['SimilationPeriod']['start']
end = config_file['RuntimeOptions'][2]['SimilationPeriod']['end']
spinup_years = \
    config_file['RuntimeOptions'][2]['SimilationPeriod']['spinup_years']

# Temporal resoulution
dailyRes = config_file['RuntimeOptions'][3]['TimeStep']['daily']
hourly = config_file['RuntimeOptions'][3]['TimeStep']['hourly']


if dailyRes:
    temporal_res = 'Daily'
else:
    temporal_res = 'Hourly'

# Selection of ouput variable (fluxes, storages and flows)
# Vertical Water Balance (vb)
vb_fluxes = config_file['outputVariable'][0]['VerticalWaterBalanceFluxes']
vb_storages = config_file['outputVariable'][1]['VerticalWaterBalanceStorages']

# Lateral Water Balance (lb)
lb_fluxes = config_file['outputVariable'][2]['LateralWaterBalanceFluxes']
lb_storages = config_file['outputVariable'][3]['LateralWaterBalanceStorages']
