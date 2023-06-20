# -*- coding: utf-8 -*-
"""
ReWaterGAP.

Created on Thu Mar  3 18:21:35 2022

@author: nyenah
"""
import logging
from pathlib import Path
import glob
import os
import sys
import xarray as xr
import watergap_logger as log
import misc.cli_args as cli
from controller import configuration_module as cm


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
# Read in filepath from configuration file and opens file
# ===============================================================


class Wateruse:
    """Handles climate forcing data."""

    def __init__(self):
        """
        Get file path.

        Return
        ------
        climate forcings

        """
        # ==============================================================
        # path to Wateruse netcdf data
        # ==============================================================
        potential_net_abstraction_path = \
            str(Path(cm.config_file['FilePath']['inputDir'] + r'water_use/*'))

        # ==============================================================
        # Loading in Wateruse
        # ==============================================================
        try:
            self.potential_net_abstraction = \
                xr.open_mfdataset(glob.glob(potential_net_abstraction_path),
                                  chunks={'time': 365})

        except FileNotFoundError:
            log.config_logger(logging.ERROR, modname, 'Climate forcing '
                              'not found', args.debug)
            sys.exit()  # dont run code if file does not exist
        except ValueError:
            log.config_logger(logging.ERROR, modname, 'File(s) extension '
                              'should be NETCDF', args.debug)
            sys.exit()  # dont run code if file does not exist
        else:
            print('Water-use input files loaded successfully')

