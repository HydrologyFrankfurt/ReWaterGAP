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
import numpy as np
from core.utility import land_surfacewater_fraction as lsf
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
        # Get global lake area
        # =====================================================================
        self.global_lake_area = \
            lsf.get_glolake_area(self.static_data.land_surface_water_fraction)

        # =====================================================================
        # Get initial land area fracion
        # =====================================================================
        self.current_landareafrac = \
            lsf.get_landareafrac(self.static_data.land_surface_water_fraction)
        self.landareafrac_ratio = \
            np.ones(self.current_landareafrac.shape).astype(np.float64)
        self.previous_landareafrac = \
            np.zeros(self.current_landareafrac.shape).astype(np.float64)

        # =====================================================================
        # Get initial fractions for local lakes and local and global wetland
        # =====================================================================
        self.previous_loclakefrac = self.static_data.\
            land_surface_water_fraction.loclak[0].values.astype(np.float64)/100
        self.previous_locwetfrac = self.static_data.\
            land_surface_water_fraction.locwet[0].values.astype(np.float64)/100
        self.previous_glowetfrac = self.static_data.\
            land_surface_water_fraction.glowet[0].values.astype(np.float64)/100

        self.previous_swb_frac = self.previous_loclakefrac + self.previous_locwetfrac + \
            self.previous_glowetfrac
        self.current_swb_frac = 0

    def update_landareafrac(self, land_swb_fraction):
        """
        Update land area fraction.

        Parameters
        ----------
        land_surface_frac : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        # updated fractions for current time step
        current_landareafrac = land_swb_fraction["current_landareafrac"]
        loclake_frac = land_swb_fraction["new_locallake_fraction"]
        locwet_frac = land_swb_fraction["new_localwetland_fraction"]
        glowet_frac = land_swb_fraction["new_globalwetland_fraction"]

        # compute change in fraction based on previous and current
        # local lakes and local and global wetland fractions

        self.current_swb_frac = loclake_frac + locwet_frac + glowet_frac

        change_in_frac = self.current_swb_frac - self.previous_swb_frac
        # print( change_in_frac[117, 454])
        self.previous_swb_frac = self.current_swb_frac.copy()

        # current fractions becomes previous
        # update current and previous land area fraction
        self.previous_landareafrac = current_landareafrac.copy()

        self.current_landareafrac = self.previous_landareafrac - change_in_frac
        self.current_landareafrac[self.current_landareafrac < 0] = 0
        # print( self.current_landareafrac[117, 454])
        self.landareafrac_ratio =  \
            np.divide(self.previous_landareafrac, self.current_landareafrac,
                      out=np.zeros_like(self.current_landareafrac),
                      where=self.current_landareafrac != 0)

    def update_landfrac_for_restart(self, landfrac_state):
        """
        Update Land area fraction for model restart.

        Parameters
        ----------
        landfrac_state : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.current_landareafrac = landfrac_state["current_landareafrac"]
        self.previous_landareafrac = landfrac_state["previous_landareafrac"]
        self.landareafrac_ratio = landfrac_state["landareafrac_ratio"]
