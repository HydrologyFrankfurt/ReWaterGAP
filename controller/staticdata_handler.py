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
import geopandas as gpd
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
        land_cover_path = str(Path(cm.static_land_data_path +
                                   r'/watergap_22d_landcover.nc4'))

        humid_arid_path = str(Path(cm.static_land_data_path +
                                   r'/watergap_22e_aridhumid.nc4'))

        canopy_snow_soil_parameters_path = \
            str(Path(cm.static_land_data_path +
                     r'/canopy_snow_parameters.csv'))

        land_surface_waterfraction_path = \
            str(Path(cm.static_land_data_path + r'/land_water_fractions/*'))

        soil_static_files_path = \
            str(Path(cm.static_land_data_path + r'/soil_storage/*'))

        gtopo30_elevation_path = \
            str(Path(cm.static_land_data_path +
                     r'/watergap_22e_v001_elevrange.nc4'))

        cell_area_path = str(Path(cm.static_land_data_path + r'/cell_area.nc'))

        river_static_file_path = \
            str(Path(cm.static_land_data_path + r'/river_static_data/*'))

        reservoir_reglake_file_path = str(Path(cm.static_land_data_path +
                                               r'/reservior_regulated_lake/*'))

        reservoir_frac_file_path = \
            str(Path(cm.static_land_data_path +
                     r'/watergap_22d_gloresfrac_1901_2020.nc'))

        rout_order_path = str(Path(cm.static_land_data_path +
                                   r'/routing_order.csv'))

        alloc_coeff_path = str(Path(cm.static_land_data_path +
                                    r'/alloc_coeff_by_routorder.csv'))
        neighbourcells_path = str(Path(cm.static_land_data_path +
                                       r'/neigbouringcells_latlon.csv'))

        neighbourcells_outflowcell_path = \
            str(Path(cm.static_land_data_path +
                     r'/neigbouringcells_outflow_latlon.csv'))
            
        super_basins_shapefile = \
            str(Path(cm.static_land_data_path +
                r'/super_basins/WLM_superbasins_names_outflowcellcoords_upstreamarea.shp'))
            
        station_path =  str(Path(cm.path_to_stations_file +
                               r'/stations.csv'))   
        # ==============================================================
        # Loading in climate forcing
        # ==============================================================
        try:
            # Actual name: Land cover , Unit: (-)
            land_cover = xr.open_dataset(land_cover_path,
                                         decode_times=False)
            self.land_cover = land_cover.landcover[0].values

            # Humid-arid calssification based on Müller Schmied et al. 2021
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

            # Reserviour and regulated lakes (data for computing waterbalance)
            self.res_reg_files = \
                xr.open_mfdataset(reservoir_reglake_file_path,
                                  decode_times=False)

            # Yearly Reserviour fractions
            self.resyear_frac = \
                xr.open_dataset(reservoir_frac_file_path)

            # routing order data
            self.rout_order = pd.read_csv(rout_order_path)

            # Allocation coeffiencient according to routing order
            # Required for computing reselease from Hanasaki algorithm
            # see Hanasaki et al 2006
            self.alloc_coeff = pd.read_csv(alloc_coeff_path)

            # Neighbouuring cells from which wateruse from demand cells could
            # be satified.
            self.neighbourcells = pd.read_csv(neighbourcells_path)
            self.neighbourcells_outflowcell = \
                pd.read_csv(neighbourcells_outflowcell_path)
            
            # To select region or basin.
            self.mask_watergap = cell_area.cell_area.copy() # needed to create a mask
            self.super_basins = gpd.read_file(super_basins_shapefile)
            self.stations = pd.read_csv(station_path)
                
                

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
