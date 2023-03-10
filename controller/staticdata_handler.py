# -*- coding: utf-8 -*-
"""
Created on Tue May 10 13:15:40 2022.

@author: nyenah
"""

import logging
from pathlib import Path
import os
import sys
import numpy as np
import xarray as xr
import pandas as pd
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


class StaticData:
    """Handles static data."""

    def __init__(self):
        """
        Get file path.

        Return
        ------
        Static data

        """
        # ==============================================================
        # path to climate forcing netcdf data
        # ==============================================================
        land_cover_path = str(Path(cm.config_file['FilePath']['inputDir'] +
                                   r'static_input/watergap_22d_landcover.nc4'))

        humid_arid_path = str(Path(cm.config_file['FilePath']['inputDir'] +
                                   r'static_input/watergap_22e_aridhumid.nc4'))

        canopy_snow_soil_parameters_path = str(Path(cm.config_file['FilePath']
                                               ['inputDir']+r'static_input'
                                               '/canopy_snow_'
                                               'parameters.csv'))
        land_surface_waterfraction_path = \
            str(Path(cm.config_file['FilePath']['inputDir'] +
                     r'static_input/land_water_fractions/*'))

        soil_static_files_path = \
            str(Path(cm.config_file['FilePath']['inputDir'] +
                     r'static_input/soil_storage/*'))

        gtopo30_elevation_path = \
            str(Path(cm.config_file['FilePath']['inputDir'] +
                     r'static_input/watergap_22e_v001_elevrange.nc4'))

        cell_area_path = \
            str(Path(cm.config_file['FilePath']['inputDir'] +
                     r'static_input/cell_area.nc'))

        river_static_file_path = \
            str(Path(cm.config_file['FilePath']['inputDir'] +
                     r'static_input/river_static_data/*'))
        rout_order_path = str(Path(cm.config_file['FilePath']['inputDir'] +
                                   r'static_input/routing_order.csv'))
        # ==============================================================
        # Loading in climate forcing
        # ==============================================================
        try:
            # Actual name: Land cover , Unit: (-)
            land_cover = xr.open_dataset(land_cover_path,
                                         decode_times=False)
            self.land_cover = land_cover.landcover[0].values

            # Humid-arid calssification based on M??ller Schmied et al. 2021
            humid_arid = xr.open_dataset(humid_arid_path,
                                         decode_times=False)
            self.humid_arid = humid_arid.aridhumid[0].values

            # Elevations according to GTOPO30 (U.S. Geological Survey, 1996)
            gtopo30_elevation = xr.open_dataset(gtopo30_elevation_path,
                                                decode_times=False)
            self.gtopo30_elevation = gtopo30_elevation.elevrange.values

            # Canopy model paramters (Table)
            self.canopy_snow_soil_parameters = \
                pd.read_csv(canopy_snow_soil_parameters_path)

            # Land and surface water fractions
            self.land_surface_water_fraction = \
                xr.open_mfdataset(land_surface_waterfraction_path,
                                  decode_times=False)
            # Soil static files
            self.soil_static_files = \
                xr.open_mfdataset(soil_static_files_path,
                                  decode_times=False)
            # Cell Area
            cell_area = xr.open_dataset(cell_area_path, decode_times=False)
            self.cell_area = cell_area.cell_area.values

            # River static files**
            self.river_static_files = \
                xr.open_mfdataset(river_static_file_path, decode_times=False)

            # routing order data
            self.rout_order = pd.read_csv(rout_order_path)

        except FileNotFoundError:
            log.config_logger(logging.ERROR, modname, 'Static data '
                              'not found', args.debug)
            sys.exit()  # dont run code if file does not exist
        except ValueError:
            log.config_logger(logging.ERROR, modname, 'File(s) extension '
                              'should be NETCDF or CSV for canopy model'
                              'parameters', args.debug)
            sys.exit()  # dont run code if file does not exist
        else:
            print('\n'+'Static data loaded successfully')

    def soil_static_data(self):
        """
        Update land area fraction.

        Returns
        -------
        None.

        """
        # Built up area, units = (-)
        builtup_area = self.soil_static_files.builtup_area_frac[0].values

        # Total available water content , units = mm
        total_avail_water_content = \
            self.soil_static_files.tawc[0].values.astype(np.float64)

        # Drainage direction of the grid cell, units = (-)
        drainage_direction = \
            self.soil_static_files.drainage_direction[0].values

        # Maxumum ground water recharge = mm
        max_groundwater_recharge = \
            self.soil_static_files.max_recharge[0].values/100

        # Soil texture, units= (-)
        soil_texture = self.soil_static_files.texture.values

        # groundwater recharge factor with Missipi corrected, units= (-)
        groundwater_recharge_factor = \
            self.soil_static_files.gw_factor_corr[0].values.astype(np.float64)

        return builtup_area, total_avail_water_content, drainage_direction,\
            max_groundwater_recharge, soil_texture, groundwater_recharge_factor

# =============================================================================
#     def update_surfacewater_fractions(self):
#         """
#         Update land area fraction.
#
#         Returns
#         -------
#         None.
#
#         """
#         return self.land_surface_water_fraction
# =============================================================================
