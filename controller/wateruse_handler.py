# -*- coding: utf-8 -*-
"""
ReWaterGAP.

Created on Thu Mar  3 18:21:35 2022

@author: nyenah
"""
import logging
import numpy as np
from pathlib import Path
import glob
import os
import sys
import xarray as xr
import watergap_logger as log
import misc.cli_args as cli
from controller import configuration_module as cm
from core.lateralwaterbalance import aggregate_netabstraction as aggr

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
    """Handles water use and relevant static data."""

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

        frgi_path = str(Path(cm.config_file['FilePath']['inputDir'] +
                             r'static_input/watergap_22d_frgi.nc4'))

        glwdunits_path = str(Path(cm.config_file['FilePath']['inputDir'] +
                             r'static_input/watergap_22d_glwdunits.nc'))

        # ==============================================================
        # Loading in Wateruse
        # ==============================================================
        try:
            self.potential_net_abstraction = \
                xr.open_mfdataset(glob.glob(potential_net_abstraction_path),
                                  chunks={'time': 365})
            # Fraction of return flow from irrigation to groundwater
            # See Döll et al 2012, eqn 1
            self.frac_irri_returnflow_to_gw = \
                xr.open_dataset(frgi_path, decode_times=False)

            # Riprian cells of global lake or reservoir
            self.glwdunits = \
                xr.open_dataset(glwdunits_path, decode_times=False)

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

    def aggregate_riparian_netpotabs(self, lake_area, res_area, netabs):
        """
        Aggregate riparian potential net abstractiion.

        Parameters
        ----------
        lake_area : TYPE
            DESCRIPTION.
        res_area : TYPE
            DESCRIPTION.
        netabs : TYPE
            DESCRIPTION.

        Returns
        -------
        aggreagted_potnet_abstraction : TYPE
            DESCRIPTION.

        """
        glwdunits = self.glwdunits.glwdunits.values
        unique_glwdunits = np.unique(glwdunits)[1:-1]

        aggreagted_potnet_abstraction = \
            aggr.aggregate_potnetabs(glwdunits, lake_area, res_area,
                                     netabs, unique_glwdunits)
        return aggreagted_potnet_abstraction
