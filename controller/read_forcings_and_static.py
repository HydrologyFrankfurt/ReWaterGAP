# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"Parameters"

# =============================================================================
#  This module reads in climate forcings and static data. Its also gets the
# dimensions of the input variables to create the output variables
# =============================================================================

from controller import climateforcing_handler as cf
from controller import staticdata_handler as sd
from controller import configuration_module as cm


class InitializeForcingsandStaticdata:
    """Reads in climate forcings and static data."""

    def __init__(self):
        # =====================================================================
        # Get static data and climate forcing
        # Please see staticdata and climateforcing handlers for varibale units
        # =====================================================================
        self.static_data = sd.StaticData()
        self.climate_forcing = cf.ClimateForcing()
        self.climate_forcing.check_unitandvarname()

        # =====================================================================
        # Get grid to create ouput variable
        # =====================================================================
        # Note!!! grid_coord contains latitiude, longitude and time (based on
        # simulation period ).
        # I am only selecting the coordinates(lat, lon and time) of the
        # temperature variable. the actual temperature forcing is not used here

        # Select forcing data for a year if run is less than or equal to a year
        # This is required to run initialization years for good results.
        if cm.start.split("-")[0] == cm.end.split("-")[0]:
            year_end = cm.end.split('-')[0]+'-12-31'
            self.grid_coords = \
                self.climate_forcing.temperature.\
                sel(time=slice(cm.start, year_end)).coords
        else:
            self.grid_coords = \
                self.climate_forcing.temperature.sel(time=slice(cm.start,
                                                                cm.end)).coords

        # Geting length of lat,lon from grid coordinates (grid_coords)
        # to create temporary data.
        self.lat_length = len(self.grid_coords['lat'].values)
        self.lon_length = len(self.grid_coords['lon'].values)
