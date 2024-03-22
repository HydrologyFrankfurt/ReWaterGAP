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
        self.init_landfrac_res_flag = True

        # =====================================================================
        # initialize land area fracion variables
        # =====================================================================

        self.cont_frac = self.static_data.land_surface_water_fraction.\
            contfrac.values.astype(np.float64)
        self.current_landareafrac =  np.zeros_like(self.cont_frac)
        self.landareafrac_ratio =  np.zeros_like(self.cont_frac)
        self.previous_landareafrac =  np.zeros_like(self.cont_frac)
        self.landwaterfrac_excl_glolake_res =  np.zeros_like(self.cont_frac)
        
        # Land and water fractions (used to calculate total PET)
        # water_freq is sum of glolake, loclake, & glores (includes reglake)
        # land_freq is (cont_frac - waterfreq) and contains wetlands 
        self.water_freq =  np.zeros_like(self.cont_frac)
        self.land_freq =   np.zeros_like(self.cont_frac)
        # updated_loclake_frac is local lake fraction * reduction factor
        self.updated_loclake_frac =  np.zeros_like(self.cont_frac)
        self.land_and_water_freq_flag = True
        
        # =====================================================================
        # Initialize fraction variables for reservoir
        # =====================================================================
        self.glores_frac_prevyear = np.zeros_like(self.cont_frac)
        self.gloresfrac_change = np.zeros_like(self.cont_frac)
        self.current_swb_frac = np.zeros_like(self.cont_frac)


        # Note!!! if run is naturalised or reservoirs are not considered
        # (in anthropogenic run) regulated lakes becomes global lakes.
        # Also, if reservoirs are considered in anthropogenic run, local
        # reservoirs are added to local lakes
        self.glolake_frac = self.static_data.\
            land_surface_water_fraction.glolak[0].values.astype(np.float64)
        reglake_frac = self.static_data.\
            land_surface_water_fraction.reglak[0].values.astype(np.float64)
        self.loclake_frac = self.static_data.\
            land_surface_water_fraction.loclak[0].values.astype(np.float64)
        locres_frac = self.static_data.\
            land_surface_water_fraction.locres[0].values.astype(np.float64)

        locwet_frac = self.static_data.\
            land_surface_water_fraction.locwet[0].values.astype(np.float64)
        glowet_frac = self.static_data.\
            land_surface_water_fraction.glowet[0].values.astype(np.float64)

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
            self.current_landareafrac[self.current_landareafrac<0]=0
            # if initial land area fraction is zero (surface waterbody
            # fraction is 100 % ) set initial landareafrac_ratio (prev/current)
            # to zero
            self.landareafrac_ratio = np.where(self.current_landareafrac==0,
                                               0, 1)

            self.previous_landareafrac = \
                np.zeros(self.current_landareafrac.shape).astype(np.float64)

            self.glolake_frac += reglake_frac 

            # self.previous_swb_frac will be used to update daily land area
            # fraction  see "update_landareafrac" function below
            self.previous_swb_frac = \
                (self.loclake_frac + locwet_frac + glowet_frac)/100
                
            # =====================================================================
            # Get land area fraction without global lake & reservoirs/regulated lakes. 
            # This variable will be used to compute consistent precipitation
            # =====================================================================
            self.landwaterfrac_excl_glolake_res = (self.cont_frac - self.glolake_frac)/100
            self.landwaterfrac_excl_glolake_res[self.landwaterfrac_excl_glolake_res < 0] = 0

        else:
            self.loclake_frac += locres_frac

            # compute swb fraction after local res is added to local lake
            self.previous_swb_frac = \
                (self.loclake_frac + locwet_frac + glowet_frac)/100

        
        # =====================================================================
        # Get global lake area
        # =====================================================================
        self.global_lake_area = \
            lsf.get_glolake_area(self.static_data.land_surface_water_fraction)
        # =====================================================================

        # ---------------------------------------------------------------------
        # Variables needed tp adapt global reservoir storage due to  net change
        # in land fraction. see  "adapt_glores_storage" function
        self.outflow_cell_assignment = self.static_data.res_reg_files.\
            outflowcell_assignment_glores.values
        self.unique_outflow_cell_assignment = \
            np.unique(self.outflow_cell_assignment)[1:-1]
        # ---------------------------------------------------------------------

    def landareafrac_with_reservior(self, date, reservoir_opt_year):
        """
        Get land area fraction.

        Parameters
        ----------
        date : datetime
            Simulation date
        reservoir_opt_year : integer
            List of years for all operational reservoir from start year to 
            end year.

        Returns
        -------
        None.

        """
        # Here land area fraction considers reservoir fraction which is read in
        # yearly. Hence, Land area fraction is recalulated every year.
        # Note!!! that land area fraction is also updated daily after yearly
        # calulation. (see update_landareafrac function)
        if self.reservior_opt is True:
            self.date = date.astype('datetime64[D]')
            self.reservoir_opt_year = reservoir_opt_year


            if self.date in self.reservoir_opt_year or \
                self.init_landfrac_res_flag is True:
                    
                self.resyear = str(pd.to_datetime(self.date).year)
                # =============================================================
                # Get land area fracion
                # =============================================================
                # Use saved current_landareafrac and glores_frac_prevyear,
                # if run is a restart run
                lsf_out = \
                    lsf.compute_landareafrac(self.static_data.
                                             land_surface_water_fraction,
                                             self.current_landareafrac,
                                             self.static_data.resyear_frac,
                                             self.resyear,
                                             self.glores_frac_prevyear,
                                             self.init_landfrac_res_flag)

                self.current_landareafrac = lsf_out[0]
                self.current_landareafrac[self.current_landareafrac<0]=0
                self.gloresfrac_change = lsf_out[1]
                
                if self.init_landfrac_res_flag:
                    # if initial land area fraction is zero (surface waterbody
                    # fraction is 100 %) set initial landareafrac_ratio 
                    # (prev/current) to zero
                    self.landareafrac_ratio = \
                        np.where(self.current_landareafrac==0, 0, 1)

                    self.previous_landareafrac = \
                        np.zeros(self.current_landareafrac.shape).\
                        astype(np.float64)

                self.init_landfrac_res_flag = False


                # =============================================================
                # Get land water fracion without  global lakes and 
                # reservoirs/regulated lakes. 
                # =============================================================
                res_year_lakewet_frac = str(pd.to_datetime(self.date).year)
                glores_frac_currentyear = self.static_data.resyear_frac.glores_frac.\
                    sel(time=res_year_lakewet_frac).values.astype(np.float64)
            
                self.landwaterfrac_excl_glolake_res = (self.cont_frac - self.glolake_frac - glores_frac_currentyear[0])/100
                self.landwaterfrac_excl_glolake_res[self.landwaterfrac_excl_glolake_res < 0] = 0
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
        canopy_storage : array
           Canopy storage,  Units: [mm]
        soil_water_content : array
            Soil water storage, Units: [mm].
        snow_water_storage : array
            Snow water storage, Units: [mm]
        glores_area : array
           Global reservoir area, Unit: [km^2]
        glores_storage : array
            Global reservoir storage, Unit: [km^3]

        Returns
        -------
        glores_storage : array
            Global reservoir storage, Unit: [km^3]

        """
        if self.reservior_opt is True:
            if self.date in self.reservoir_opt_year:
 
                
                landareafrac_change = \
                    self.current_landareafrac - self.previous_landareafrac

                # The case when landareafrac_change >= 0 :
                # Increased land area fraction has nothing to do with added
                # reservoirs. In the fractional routing, it could be that
                # less water is routed from land to the various surface
                # water bodies (Note: reservoirs are not included in
                # fractional routing as there also upstream inflow is
                # involved). Also, this happens only in edge cases
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

                # ---------------------------------------------------------
                # Add previous storage to reservoir storage volume
                # located in assinged outflow cell according to the
                # glwdunits
                # ---------------------------------------------------------
                for i in range(len(self.unique_outflow_cell_assignment)):
                    assinged_outflowcell_index = \
                        np.where((self.outflow_cell_assignment ==
                                  self.unique_outflow_cell_assignment[i]) &
                                 (glores_area > 0))

                    if assinged_outflowcell_index[0].shape[0] != 0:
                        lat_x, lon_y = assinged_outflowcell_index[0][0],\
                            assinged_outflowcell_index[1][0]

                        all_storage = \
                            np.where(self.outflow_cell_assignment ==
                                     self.unique_outflow_cell_assignment[i],
                                     canopy_watercontent_change_km3 +
                                     soil_watercontent_change_km3 +
                                     snow_watercontent_change_km3, 0)

                        glores_storage[lat_x, lon_y] += all_storage.sum()
                # ---------------------------------------------------------
                
                # Assigning current reservoir year to previous year.
                glores_frac_currentyear = self.static_data.resyear_frac.\
                    glores_frac.sel(time=self.resyear).values.\
                    astype(np.float64)
                glores_frac_currentyear = glores_frac_currentyear[0]
                self.glores_frac_prevyear = glores_frac_currentyear

        return glores_storage


    def get_land_and_water_freq(self, date):
        """
        Land and water fractions (used to calculate total PET)

        Parameters
        ----------
        date : datetime
            Simulation date
        update_loclake_frac : array
            updated local lake fraction

        Returns
        -------
        None.

        """
        if self.land_and_water_freq_flag is True: # start of simulation 
            if self.reservior_opt is True:
                res_year_lakewet_frac = str(pd.to_datetime(date).year)
                glores_frac_currentyear = self.static_data.resyear_frac.glores_frac.\
                    sel(time=res_year_lakewet_frac).values.astype(np.float64)
            else: 
                glores_frac_currentyear = np.zeros_like(self.cont_frac)
                
            self.water_freq = self.glolake_frac + self.loclake_frac +  glores_frac_currentyear[0]
            self.land_freq =  self.cont_frac - self.water_freq
            self.land_and_water_freq_flag = False 

        else:  
            if (pd.to_datetime(date).month == 1) and (pd.to_datetime(date).day == 1):
                if self.reservior_opt is True:
                    res_year_lakewet_frac = str(pd.to_datetime(date).year)
                    glores_frac_currentyear = self.static_data.resyear_frac.glores_frac.\
                        sel(time=res_year_lakewet_frac).values.astype(np.float64)
                else: 
                    glores_frac_currentyear = np.zeros_like(self.cont_frac)
                    
                self.water_freq = self.glolake_frac + \
                    (self.updated_loclake_frac*100) +  glores_frac_currentyear[0]
                self.land_freq = self.cont_frac - self.water_freq


    def update_landareafrac(self, land_swb_fraction):
        """
        Update land area fraction.

        Parameters
        ----------
        land_swb_fraction : array
           updated surafce water bodies fracion (local lake and local and global 
                                                 wetland)

        Returns
        -------
        None.

        """
        # updated fractions for current time step
        current_landareafrac = land_swb_fraction["current_landareafrac"]
        loclake_frac = land_swb_fraction["new_locallake_fraction"]
        locwet_frac = land_swb_fraction["new_localwetland_fraction"]
        glowet_frac = land_swb_fraction["new_globalwetland_fraction"]
        
        self.updated_loclake_frac = loclake_frac # required for computing land_freq and water_freq 
        
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
        landfrac_state : array
            State varibles to update land area fraction

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
        self.init_landfrac_res_flag = landfrac_state["init_landfrac_res_flag"]
        self.landwaterfrac_excl_glolake_res = landfrac_state["landwaterfrac_excl_glolake_res"]
        self.land_and_water_freq_flag = landfrac_state["land_and_water_freq_flag"]
        self.water_freq = landfrac_state["water_freq"]
        self.land_freq =  landfrac_state["land_freq"] 
        self.updated_loclake_frac = landfrac_state["updated_loclake_frac"]
