# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================


# =============================================================================
#  This module reads in climate forcings and static data. Its also gets the
# dimensions of the input variables to create the output variables
# =============================================================================
import numpy as np
from core.utility import land_surfacewater_fraction as lsf
from controller import climateforcing_handler as cf
from controller import staticdata_handler as sd
from controller import configuration_module as cm


class InitializeForcingsandStaticdata:
    """ Reads in climate forcings and static data."""

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
        # Note!!! coord contains latitiude, longitude and time (based on
        # simulation period )
        self.grid_coords = \
            self.climate_forcing.temperature.sel(time=slice(cm.start,
                                                            cm.end)).coords

        # Geting length of lat,lon from grid coordinates (grid_coords)
        # to create temporary data.
        self.lat_length = len(self.grid_coords['lat'].values)
        self.lon_length = len(self.grid_coords['lon'].values)

        # =====================================================================
        # Getting Global lake area
        # =====================================================================
        self.global_lake_area = \
            lsf.get_glolake_area(self.static_data.land_surface_water_fraction)

        # =====================================================================
        # Gettining initial land area fracion
        # =====================================================================
        self.previous_landareafrac = \
            lsf.get_landareafrac(self.static_data.land_surface_water_fraction)
        self.curent_landareafrac = self.previous_landareafrac
        self.updated_landareafrac =  \
            np.divide(self.previous_landareafrac, self.curent_landareafrac,
                      out=np.zeros_like(self.previous_landareafrac),
                      where=self.curent_landareafrac != 0)

    def update_land_area_frac(self, loclake, locwet, glowet):
        change_in_area = 0
        self.previous_landareafrac = self.curent_landareafrac
        self.curent_landareafrac = self.previous_landareafrac - change_in_area
        self.updated_landareafrac =  \
            np.divide(self.previous_landareafrac, self.curent_landareafrac,
                      out=np.zeros_like(self.previous_landareafrac),
                      where=self.curent_landareafrac != 0)


# I will add printing of data information here as functions.
#  More functions will come here so dont worry
