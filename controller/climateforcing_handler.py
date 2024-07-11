# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Climate forcing handler."""


import logging
import json
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
modname = os.path.basename(__file__)
modname = modname.split('.')[0]

# ++++++++++++++++++++++++++++++++++++++++++++++++
# Parsing  Argguments for CLI from cli_args module
# +++++++++++++++++++++++++++++++++++++++++++++++++
args = cli.parse_cli()

# ===============================================================
# Read in filepath from configuration file and opens file
# ===============================================================


class ClimateForcing:
    """Handles climate forcing data."""

    def __init__(self, run_calib):
        """
        Get file path.

        Return
        ------
        climate forcings

        """
        # ==============================================================
        # path to climate forcing netcdf data
        # ==============================================================
        precipitation_path = str(Path(cm.climate_forcing_path +
                                      r'/precipitation/*'))

        longwave_radiation_path = str(Path(cm.climate_forcing_path +
                                           r'/rad_longwave/*'))

        shortwave_radiation_path = str(Path(cm.climate_forcing_path +
                                            r'/rad_shortwave/*'))

        temperature_path = str(Path(cm.climate_forcing_path +
                                    r'/temperature/*'))
        # ==============================================================
        # Loading in climate forcing
        # ==============================================================
        try:
            #  Actual name: Precipitation, Unit:  kg m-2 s-1
            self.precipitation = \
                xr.open_mfdataset(glob.glob(precipitation_path),
                                  chunks={'time': 365})

            #  Actual name: Downward longwave radiation  Unit: Wm−2
            self.down_longwave_radiation = \
                xr.open_mfdataset(glob.glob(longwave_radiation_path),
                                  chunks={'time': 365})

            #  Actual name: Downward shortwave radiation  Unit: Wm−2
            self.down_shortwave_radiation = \
                xr.open_mfdataset(glob.glob(shortwave_radiation_path),
                                  chunks={'time': 365})

            #  Actual name: Air temperature, Unit: K
            self.temperature = \
                xr.open_mfdataset(glob.glob(temperature_path),
                                  chunks={'time': 365})

        except FileNotFoundError:
            log.config_logger(logging.ERROR, modname, 'Climate forcing '
                              'not found', args.debug)
            sys.exit()  # don't run code if file does not exist
        except ValueError:
            log.config_logger(logging.ERROR, modname, 'File(s) extension '
                              'should be NETCDF', args.debug)
            sys.exit()  # don't run code if file does not exist
        else:
            if run_calib is False:
                print('Climate forcing loaded successfully')

            self.var_name = [list(self.precipitation.data_vars)[0],
                             list(self.down_longwave_radiation.data_vars)[0],
                             list(self.down_shortwave_radiation.data_vars)[0],
                             list(self.temperature.data_vars)[0]]

            self.units = [self.precipitation[self.var_name[0]].units,

                          self.down_longwave_radiation[self.var_name[1]].units,

                          self.down_shortwave_radiation[self.var_name[2]].units,

                          self.temperature[self.var_name[3]].units]

    def check_unitandvarname(self):
        """
        Check data units and variable name.

        Returns
        -------
        None.

        """
        # ==============================================================
        # Opening cf convention file for units and variable name check
        # ==============================================================

        try:
            with open('cf_conv.json', encoding="utf-8") as cf_info:
                cf_info = json.load(cf_info)
        except FileNotFoundError:
            log.config_logger(logging.ERROR, modname, 'Cf convention file for'
                              ' variable and unit check not found', args.debug)

        print('++++++++++++++++++++++' + '\n' + 'Checking variable name'
              + '\n' + '++++++++++++++++++++++')

        # Note!!! undesrcore means I am not interested in the index(numbers)
        for _, var_name in enumerate(self.var_name):
            if var_name in cf_info['variables']['shortname']:
                print(var_name + ' follows cf convention')
            else:
                log.config_logger(logging.WARNING, modname, var_name +
                                  ' does not follow cf convention', args.debug)

        print('\n'+'+++++++++++++++' + '\n' + 'Checking units' + '\n' +
              '+++++++++++++++')

        extra_units = ["mm/day", " mm day-1", "°C", "C", "degree celcius",
                       "celcius"]
        for index, units in enumerate(self.units):
            if units in cf_info['variables']['units'] or units in extra_units:
                print('*' + self.var_name[index] + '*' + ' required in ' +
                      units + ' found')
            else:
                log.config_logger(logging.ERROR, modname, units +
                                  ' is not a known cf convention unit.'
                                  ' Plesae check data units', args.debug)
                sys.exit()  # don't run code if units does not exist
