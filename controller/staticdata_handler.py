# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Static data parser."""

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
modname = os.path.basename(__file__)
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

    def __init__(self, run_calib):
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
                                   r'/watergap_22e_landcover.nc4'))

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
                     r'/watergap_22e_elevrange.nc4'))

        cell_area_path = str(Path(cm.static_land_data_path +
                                  r'/watergap_22e_continentalarea.nc'))

        river_static_file_path = \
            str(Path(cm.static_land_data_path + r'/river_static_data/*'))

        reservoir_reglake_file_path = str(Path(cm.static_land_data_path +
                                               r'/reservoir_regulated_lake/*'))

        reservoir_frac_file_path = \
            str(Path(cm.static_land_data_path +
                     r'/watergap_22e_gloresfrac_*.nc'))
        
        rout_order_path = str(Path(cm.static_land_data_path +
                                   r'/routing_order.csv'))

        alloc_coeff_path = str(Path(cm.static_land_data_path +
                                    r'/alloc_coeff_by_routorder.csv'))
        neighbourcells_path = str(Path(cm.static_land_data_path +
                                       r'/neigbouringcells_latlon.csv'))

        neighbourcells_outflowcell_path = \
            str(Path(cm.static_land_data_path +
                     r'/neigbouringcells_outflow_latlon.csv'))

        lat_lon_arcid_path = \
            str(Path(cm.static_land_data_path +
                r'/ArcID_GCRC_Lon_Lat.txt'))

        upstream_cells_path = \
            str(Path(cm.static_land_data_path +
                r'/upstream_cells_for_grid_arcid.csv'))

        arc_id_path = \
            str(Path(cm.static_land_data_path + r'/watergap_22e_arc_id.nc'))

        station_path = str(Path(cm.path_to_stations_file +
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

            # Elevations(m) according to GTOPO30 (U.S. Geological Survey, 1996)
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
            self.cell_area = cell_area.continentalarea.values

            # River static files
            self.river_static_files = \
                xr.open_mfdataset(river_static_file_path, decode_times=False)

            # Reserviour and regulated lakes (data for computing waterbalance)
            self.res_reg_files = \
                xr.open_mfdataset(reservoir_reglake_file_path,
                                  decode_times=False)

            # Yearly Reserviour fractions
            self.resyear_frac = \
                xr.open_mfdataset(reservoir_frac_file_path)

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
            self.arc_id = xr.open_dataarray(arc_id_path, decode_times=False)
            self.upstream_cells = pd.read_csv(upstream_cells_path)
            self.lat_lon_arcid = pd.read_csv(lat_lon_arcid_path)
            self.stations = pd.read_csv(station_path)

        except FileNotFoundError as error:
            log.config_logger(logging.ERROR, modname, error, args.debug)
            sys.exit()  # dont run code if file does not exist
        except ValueError:
            log.config_logger(logging.ERROR, modname, 'File(s) extension '
                              'should be NETCDF(.nc or .nc4) or CSV for canopy model'
                              'parameters', args.debug)
            sys.exit()  # dont run code if file does not exist
        else:
            if run_calib is False:
                print('\n'+'Static data loaded successfully')

    def soil_static_data(self):
        """
        Parse soil static data needed for soil water balance.

        Returns
        -------
        builtup_area_frac : array
            Built up area fraction, Unit: [-]
        total_avail_water_content : array
            Total available water content,  Unit: [mm]
        drainage_direction : array
            Drainage direction of grid cell, Unit: [mm]
        max_groundwater_recharge : array
            Maxumum ground water recharge, Unit: [mm]
        soil_texture : array
           Soil texture, Unit: [-]
        groundwater_recharge_factor : array
           groundwater recharge factor with Missipi corrected,  Unit: [-]

        """
        # Built up area fraction, units = (-)
        builtup_area_frac = self.soil_static_files.builtup_area_frac[0].values

        # Total available water content , units = mm (per 1m soil)
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

        return builtup_area_frac, total_avail_water_content, drainage_direction,\
            max_groundwater_recharge, soil_texture, groundwater_recharge_factor
