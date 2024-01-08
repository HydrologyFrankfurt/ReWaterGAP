# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Land surfacewater fraction."""

import numpy as np
import pandas as pd
from core import land_surfacewater_fraction as lsf


class LandsurfacewaterFraction:
    """Compute and update land and surfacewater fractions."""

    def __init__(self, static_data, reservior_opt):
        self.static_data = static_data
        self.reservior_opt = reservior_opt
        # =====================================================================
        # Get initial fractions for local lakes, local and global wetland
        # =====================================================================
        self.previous_loclakefrac = self.static_data.\
            land_surface_water_fraction.loclak[0].values.astype(np.float64)/100
        self.previous_locwetfrac = self.static_data.\
            land_surface_water_fraction.locwet[0].values.astype(np.float64)/100
        self.previous_glowetfrac = self.static_data.\
            land_surface_water_fraction.glowet[0].values.astype(np.float64)/100

        self.previous_swb_frac = self.previous_loclakefrac + \
            self.previous_locwetfrac + self.previous_glowetfrac
        self.current_swb_frac = 0

        # =====================================================================
        # Initialize fraction variables for reservoir
        # =====================================================================
        self.glores_frac_prevyear = 0
        self.gloresfrac_change = 0

        # =====================================================================
        # initialize land area fracion variables
        # =====================================================================
        self.current_landareafrac = 0
        self.landareafrac_ratio = 0
        self.previous_landareafrac = 0

        # Note!!! if run is naturalised or reservoirs are not considered
        # (in anthropogenic run) regulated lakes becomes global lakes.
        # Also if reservoirs are considered in anthropogenic run, local
        # reservoirs are added to local lakes
        self.glolake_frac = self.static_data.\
            land_surface_water_fraction.glolak[0].values.astype(np.float64)
        reglake_frac = self.static_data.\
            land_surface_water_fraction.reglak[0].values.astype(np.float64)
        self.loclake_frac = self.static_data.\
            land_surface_water_fraction.loclak[0].values.astype(np.float64)
        locres_frac = self.static_data.\
            land_surface_water_fraction.locres[0].values.astype(np.float64)

        if self.reservior_opt is False:
            # land area fraction is computed without reservior fraction. land
            # area fraction is calulated once at model start and updated daily.
            # (see update_landareafrac function).
            # if reservoir fractions are considered in land area fraction
            # See function "landareafrac_with_reservior".
            self.current_landareafrac = \
                lsf.compute_landareafrac(self.static_data.
                                         land_surface_water_fraction,
                                         self.current_landareafrac)
            self.landareafrac_ratio = \
                np.ones(self.current_landareafrac.shape).astype(np.float64)
            self.previous_landareafrac = \
                np.zeros(self.current_landareafrac.shape).astype(np.float64)

            self.glolake_frac += reglake_frac
        else:
            self.loclake_frac += locres_frac

        # =====================================================================
        # Get global lake area
        # =====================================================================
        self.global_lake_area = \
            lsf.get_glolake_area(self.static_data.land_surface_water_fraction)

    def landareafrac_with_reservior(self, date, reservoir_opt_year,
                                    time_step, restart, restart_year):
        """
        Get land area fraction.

        Parameters
        ----------
        date : TYPE
            DESCRIPTION.
        reservoir_opt_year : TYPE
            DESCRIPTION.
        timestep: TYPE
            DESCRIPTION.
        restart: TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        # Here land area fraction considers reservoir fraction which is read in
        # yearly. Hence Land area area fraction is recalulated every year.
        # Note!!! that land area fraction is also updated daily after yearly
        # calulation. (see update_landareafrac function)
        if self.reservior_opt is True:
            self.date = date.astype('datetime64[D]')
            self.reservoir_opt_year = reservoir_opt_year
            self.restart_year = restart_year

            if self.date in self.reservoir_opt_year:
                self.resyear = str(pd.to_datetime(self.date).year)
                # =============================================================
                # Get land area fracion
                # =============================================================
                # Use saved current_landareafrac and glores_frac_prevyear,
                # if run is a restart run
                if self.resyear != str(self.restart_year):

                    lsf_out = \
                        lsf.compute_landareafrac(self.static_data.
                                                 land_surface_water_fraction,
                                                 self.current_landareafrac,
                                                 self.static_data.resyear_frac,
                                                 self.resyear,
                                                 self.glores_frac_prevyear)

                    self.current_landareafrac = lsf_out[0]
                    self.gloresfrac_change = lsf_out[1]

                if time_step == 0 and restart != True:
                    self.landareafrac_ratio = \
                        np.ones(self.current_landareafrac.shape).\
                        astype(np.float64)
                    self.previous_landareafrac = \
                        np.zeros(self.current_landareafrac.shape).\
                        astype(np.float64)

    # =========================================================================
    # Adjusting Reservoir Storage Based on Changes in Land Fraction
    # =========================================================================
    # This funtion needs to be checked (more explanation needed from old code.
    # Hannes will get back to me)

    # Adapt global reservoir storage due to  net change in land fraction as a
    # result  changes in wetland  and loc.lakes  (fractional routing in
    # routing_to_surface_water_bodies module) + new reservoir

    def adapt_glores_storage(self, canopy_storage, snow_water_storage,
                             soil_water_content, glores_area, glores_storage):
        """
        Adapt reservoir storage and land area fraction.

        Parameters
        ----------
        canopy_storage : TYPE
            DESCRIPTION.
        soil_water_content : TYPE
            DESCRIPTION.
        snow_water_storage : TYPE
            DESCRIPTION.
        glores_area : TYPE
            DESCRIPTION.
        glores_storage : TYPE
            DESCRIPTION.

        Returns
        -------
        glores_storage : TYPE
            DESCRIPTION.

        """
        if self.reservior_opt is True:
            if self.date in self.reservoir_opt_year:
                if self.resyear != str(self.restart_year):

                    landareafrac_change = \
                        self.current_landareafrac - self.previous_landareafrac

                    # The case when landareafrac_change >= 0 :
                    # Increased land area fraction has nothing to do with added
                    # reservoirs. In the fractional routing, it could be that
                    # less water is routed from land to the various surface
                    # water bodies (Note: reservoirs are not included in
                    # fractional routing as there also upstream inflow is
                    # involved). Also this happens only in edge cases
                    # (the positive land area frac changes)
                    mask_positive_laf_change = (self.gloresfrac_change > 0) & \
                        (landareafrac_change >= 0)

                    self.current_landareafrac = \
                        np.where(mask_positive_laf_change,
                                 self.previous_landareafrac,
                                 self.current_landareafrac)

                    # The case when landareafrac_change < 0 :
                    # Calculate absolute storage volume in km3 from reduced
                    # ("lost") land surface fraction
                    cell_area = self.static_data.cell_area.astype(np.float64)
                    mm_to_km = 1e-6
                    mask_negative_laf_change = (self.gloresfrac_change > 0) & \
                        (landareafrac_change < 0)

                    canopy_watercontent_change_km3 = \
                        np.where(mask_negative_laf_change,
                                 (canopy_storage * mm_to_km * cell_area *
                                  (-1 * landareafrac_change)), 0)

                    soil_watercontent_change_km3 = \
                        np.where(mask_negative_laf_change,
                                 (soil_water_content * mm_to_km *
                                  cell_area * (-1 * landareafrac_change)), 0)

                    snow_watercontent_change_km3 = \
                        np.where(mask_negative_laf_change,
                                 (snow_water_storage * mm_to_km *
                                  cell_area * (-1 * landareafrac_change)), 0)

                    # Add previous storage to reservoir storage volume located
                    # in outflow cell,
                    glores_storage = \
                        np.where(glores_area > 0, (glores_storage +
                                 canopy_watercontent_change_km3 +
                                 soil_watercontent_change_km3 +
                                 snow_watercontent_change_km3),
                                 glores_storage)

                    # Assigning current reservoir year to previous year.
                    glores_frac_currentyear = self.static_data.resyear_frac.\
                        glores_frac.sel(time=self.resyear).values.\
                        astype(np.float64)
                    glores_frac_currentyear = glores_frac_currentyear[0]
                    self.glores_frac_prevyear = glores_frac_currentyear

        return glores_storage

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

        self.previous_swb_frac = self.current_swb_frac.copy()

        # current fractions becomes previous
        # update current and previous land area fraction
        self.previous_landareafrac = current_landareafrac.copy()

        self.current_landareafrac = self.previous_landareafrac - change_in_frac
        self.current_landareafrac[self.current_landareafrac < 0] = 0

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
        self.previous_swb_frac = landfrac_state["previous_swb_frac"]
        self.glores_frac_prevyear = landfrac_state["glores_frac_prevyear"]
        self.gloresfrac_change = landfrac_state["gloresfrac_change"]
