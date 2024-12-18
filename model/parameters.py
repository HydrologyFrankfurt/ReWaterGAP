# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Model parameter values."""

# =============================================================================
# This module contains all paameter values to run  WaterGAP
# =============================================================================
import logging
import os
import sys
from pathlib import Path
import xarray as xr
import misc.cli_args as cli
import watergap_logger as log


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


class Parameters:
    """WaterGAP parameters."""

    def __init__(self, run_calib, basin_id):
        # read in global parameters
        try:
            if run_calib is True:
                # calibration_test
                param_path = str(Path(f"./calibration/calib_out/{basin_id}"
                                      f"/WaterGAP_2.2e_global_parameters_basin_{basin_id}.nc"))
            else:
                # Default
                param_path = str(Path('model/WaterGAP_2.2e_global_parameters.nc'))

            self.global_params = xr.open_dataset(param_path, decode_times=False)

        except FileNotFoundError:
            log.config_logger(logging.ERROR, modname, 'Global parameter data  '
                              '(WaterGAP_2.2e_global_parameters.nc) not found', args.debug)
            sys.exit()  # dont run code if file does not exist
