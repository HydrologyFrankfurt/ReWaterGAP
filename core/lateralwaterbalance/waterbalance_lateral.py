# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Lateral waterbalance."""

# =============================================================================
# This module brings all lateral water balance functions together and
# makes use of numba to optimize speed (especially routing)
# =============================================================================
import numpy as np
import pandas as pd
from core.lateralwaterbalance import river_init
from core.lateralwaterbalance import routing as rt
from controller import configuration_module as cm


class LateralWaterBalance:
    """Compute lateral waterbalance."""

    # Getting all storages and fluxes in this dictionary container
    fluxes = {}
    storages = {}
    land_swb_fraction = {}

    def __init__(self, forcings_static, pot_net_abstraction, parameters,
                 global_lake_area, glolake_frac, loclake_frac):
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Initialize storages, wateruse and process properies for lateral
        # water balance
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.static_data = forcings_static.static_data
        #                  =================================
        #                  ||     Continent properties    ||
        #                  =================================
        # Cell area , Units : km2
        self.cell_area = self.static_data.cell_area.\
            astype(np.float64)

        self.parameters = parameters.global_params
        self.aridhumid = self.static_data.humid_arid
        self.drainage_direction = \
            self.static_data.soil_static_files.drainage_direction[0].values

        #                  =================================
        #                  ||          Groundwater        ||
        #                  =================================

        # Groundwater storage, Units : km3
        self.groundwater_storage = np.zeros((forcings_static.lat_length,
                                            forcings_static.lon_length))

        #                  =================================
        #                  ||          Local lake         ||
        #                  =================================
        self.loclake_frac = loclake_frac/100
        # Initializing local lake storage to maximum
        # Local lake area and storage,  Units : km2 & km3 respectively
        m_to_km = 0.001

        self.max_loclake_area = self.cell_area * self.loclake_frac

        self.max_loclake_storage = self.max_loclake_area * \
            self.parameters.activelake_depth.values * m_to_km

        self.loclake_storage = self.max_loclake_storage

        #                  =================================
        #                  ||          Local wetland      ||
        #                  =================================

        self.locwet_frac = self.static_data.\
            land_surface_water_fraction.locwet[0].values.astype(np.float64)/100

        # Initializing local weltland storage to maximum
        # Local wetland area and storage,  Units : km2 & km3 respectively
        self.max_locwet_area = self.cell_area * self.locwet_frac
        self.max_locwet_storage = self.max_locwet_area * \
            self.parameters.activewetland_depth.values * m_to_km

        self.locwet_storage = self.max_locwet_storage

        #                  =================================
        #                  ||          Global lake        ||
        #                  =================================
        self.glolake_frac = glolake_frac/100

        # Global lake area Units : km2
        self.glolake_area = global_lake_area

        # Initializing global lake storage to maximum,  Units : km3
        self.max_glolake_storage = self.glolake_area * \
            self.parameters.activelake_depth.values * m_to_km
        self.glolake_storage = self.max_glolake_storage

        #                  =================================
        #                  ||        Global  wetland      ||
        #                  =================================
        self.glowet_frac = self.static_data.\
            land_surface_water_fraction.glowet[0].values.astype(np.float64)/100

        # Initializing global weltland storage to maximum, , Units : km3
        # Global wetland area and storage,  Units : km2 & km3 respectively
        self.max_glowet_area = self.cell_area * self.glowet_frac
        self.max_glowet_storage = self.max_glowet_area * \
            self.parameters.activewetland_depth.values * m_to_km
        self.glowet_storage = self.max_glowet_storage

        #                  =================================
        #                  ||            River            ||
        #                  =================================

        # The following river properties are required to compute the
        # river bottom width (km) and  maximum river storage (km3).
        #  see also the river_property.py module.

        # River slope (-),
        river_slope = self.static_data.river_static_files.\
            river_slope[0].values.astype(np.float64)

        # Roughness (-)
        roughness = \
            self.static_data.river_static_files.\
            river_bed_roughness[0].values.astype(np.float64)

        # Roughness multiplier (-)
        self.roughness_multiplier = \
            self.static_data.river_static_files.\
            river_roughness_coeff_mult.values.astype(np.float64)

        # River length  with uncorrected length in coastal cells (km).
        # Note: River length is later corrected with continental cell fraction
        # (see RiverProperties function in river_property.py module)
        river_length = self.static_data.river_static_files.\
            river_length[0].values.astype(np.float64)

        # Bank full river flow (m3/s)
        bankfull_flow = self.static_data.river_static_files.\
            bankfull_flow[0].values.astype(np.float64)

        # continental area fraction (-)
        continental_fraction = self.static_data.\
            land_surface_water_fraction.contfrac.values.astype(np.float64)

        self.get_river_prop = \
            river_init.RiverProperties(river_slope, roughness,
                                       river_length, bankfull_flow,
                                       continental_fraction)

        # Initialise routing order and respective outflow cell
        rout_order = self.static_data.rout_order
        self.rout_order = rout_order[['Lat_index_routorder',
                                      'Lon_index_routorder']].to_numpy()

        self.outflow_cell = rout_order[['Lat_index_outflowcell',
                                       'Lon_index_outflowcell']].to_numpy()

        # Initializing river storage to maximum (River at bankfull condition),
        # Units : km3
        self.river_storage = self.get_river_prop.max_river_storage

        #                  ===============================================
        #                  ||   Reservior and  Regulated lake storage   ||
        #                  ===============================================
        # Initializing reservior and regulated lake stoarge, area and capacity
        # to zero. once reservoirs are active their coresponding storage,
        # area and capacity will be read in.
        # (see activate_res_area_storage_capacity function uder the heading
        # *Activcate Reservior and Regulated lake storage* in this module).

        self.glores_storage = np.zeros((forcings_static.lat_length,
                                        forcings_static.lon_length))

        self.glores_area = np.zeros((forcings_static.lat_length,
                                     forcings_static.lon_length))

        self.glores_capacity = np.zeros((forcings_static.lat_length,
                                         forcings_static.lon_length))

        # Reservoir type (1==irrgiation, 2==non irrigation)
        self.glores_type = self.static_data.\
            res_reg_files.reservoir_type[0].values.astype(np.int32)

        # Reservoir start year  units: year
        self.glores_startyear = self.static_data.\
            res_reg_files.startyear[0].values.astype(np.int32)

        # Reservoir start year  units: year
        self.glores_startmonth = self.static_data.\
            res_reg_files.startmonth[0].values.astype(np.int32)

        # Allocation coefficient for 5 downstream cells according to routing
        # order (see Hanasaki et al 2006.)
        alloc_coeff = self.static_data.alloc_coeff
        self.allocation_coeff = \
            alloc_coeff[alloc_coeff.columns[-5:]].to_numpy()

        # Mean annual total water demand of the reservoir from 1971 to 2000
        #  m3/year
        self.mean_annual_demand_res = self.static_data.\
            res_reg_files.mean_nus[0].values.astype(np.float64)

        # Mean annual inflow in to reservior
        # Units was converted from km3/month to m3/s
        # 31536000=(365 * 24 * 60 * 60)
        year_to_s = 31536000
        self.mean_annual_inflow_res = self.static_data.res_reg_files.\
            mean_inflow[0].values.astype(np.float64) * 12 * 1e9 / year_to_s

        # Monthly demand for reservoir release compution (km3/month)
        self.monthly_potential_net_abstraction_sw = \
            np.zeros((forcings_static.lat_length,
                      forcings_static.lon_length))

        # reservoir release coefficient  units: (-)
        # E.g  for environmental flow requirement reselease is initialised
        # as 0.1
        self.k_release = np.zeros((forcings_static.lat_length,
                                   forcings_static.lon_length)) + 0.1

        # Regulated lake fraction
        self.reglake_frac = self.static_data.\
            land_surface_water_fraction.reglak[0].values.astype(np.float64)/100

        self.regulated_lake_status = self.static_data.\
            land_surface_water_fraction.regulated_lake_status.values

        # Initialize reservior and regulated lake area, Units :km2
        self.all_reservoir_and_regulated_lake_area = self.static_data.\
            land_surface_water_fraction.reservoir_and_regulated_lake_area[0].\
            values.astype(np.float64)

        # To convert units for monthly downstream demand from km3/month to m3/s
        self.num_days_in_month = 0

        self.reg_lake_redfactor_firstday = \
            np.zeros((forcings_static.lat_length,
                      forcings_static.lon_length))

        # To help initialize reservoir and regulated lake storage only once
        # at simiulation start or spin up.
        self.set_res_storage_flag = True
        
        # To help make sure that reservior and regalated lake area and capacity 
        # are initiallized once each year
        self.check_res_area_flag = cm.restart
        
        #
        #                  =================================
        #                  ||    Head water cells         ||
        #                  =================================
        self.headwatercell = self.static_data.\
            land_surface_water_fraction.headwater_cell.values

        #                  =================================
        #                  ||           WaterUSe         ||
        #                  =================================
        # Contains both surface and groundwater monthly potential net
        # abstraction data
        self.potential_net_abstraction = pot_net_abstraction.\
            potential_net_abstraction

        # Get aggregation function and glwdunits from the pot_net_abstraction
        # class
        self.get_aggr_func = pot_net_abstraction

        # Potential net groundwater abstraction , Units : km3/ day
        self.potential_net_abstraction_gw = \
            np.zeros((forcings_static.lat_length,
                      forcings_static.lon_length))

        # Potential net surface water abstraction , Units : km3/ day
        self.potential_net_abstraction_sw = \
            np.zeros((forcings_static.lat_length,
                      forcings_static.lon_length))

        # Current and previous accumulated unsatified potential net
        # abstraction, units = km3/ day.
        # This represents the portion of potential net abstraction from surface
        # water that could not be satisfied over time after spatial satifaction
        # (see adapt_netabs_groundwater.py module for more details)
        self.accumulated_unsatisfied_potential_netabs_sw = \
            np.zeros((forcings_static.lat_length,
                      forcings_static.lon_length))
        self.prev_accumulated_unsatisfied_potential_netabs_sw = \
            np.zeros((forcings_static.lat_length,
                      forcings_static.lon_length))

        # Daily unsatisfied potential net abstraction, units = km3/ day
        # This is calculated as the difference between current and
        # previous accumulated_unsatisfied_potential_netabs_sw . This is
        # required to adapt adapts potential net ground water abstraction
        # (see adapt_netabs_groundwater.py module for more details)
        self.daily_unsatisfied_pot_nas = np.zeros((forcings_static.lat_length,
                                                   forcings_static.lon_length))

        # Current and previous potential water withdrawal from surfacewater
        # for irrigation units = km3/ day. Required to adapt potential net
        # abstraction from groundwter.
        # (see adapt_netabs_groundwater.py module for more details)
        self.potential_water_withdrawal_sw_irri =\
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))
        self.prev_potential_water_withdrawal_sw_irri =\
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))

        # Current and previous potential water consumptive use from
        # surfacewater for irrigation units = km3/ day. Required to adapt
        # potential net abstraction from groundwter.
        # (see adapt_netabs_groundwater.py module for more details)
        self.potential_consumptive_use_sw_irri = \
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))
        self.prev_potential_consumptive_use_sw_irri = \
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))

        # Fraction of return flow from irrigation to groundwater
        # See Döll et al 2012, eqn 1.  Required  to  adapt potential net
        # abstraction from groundwter.
        # (see adapt_netabs_groundwater.py module for more details)
        self.frac_irri_returnflow_to_gw = pot_net_abstraction.\
            frac_irri_returnflow_to_gw

        # Unsatisfied potential net abstraction from global lake or reservoir
        # outflow cell to riparian cell, units = km3/ day.
        self.unsatisfied_potential_netabs_riparian = \
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))

        # Unaggregated potential net abstraction from surface water (riaprian
        # cells are not agrregated to outflow cells),  units = km3/ day.
        self.unagregrgated_potential_netabs_sw = \
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))

        #                  =================================
        #                  ||    Neigbouring cells        ||
        #                  =================================
        # Neighbouuring cells (8 per cell) from which wateruse from demand
        # cells could be satified. Data is a numpy array of lat and lon index
        # for cells.
        self.neighbourcells = \
            self.static_data.neighbourcells.iloc[:, 1:].values
        # Respective outflow for neigbouring cells
        self.neighbourcells_outflowcell = \
            self.static_data.neighbourcells_outflowcell.iloc[:, 1:].values

        # Unsatisfied potential net abstraction from demand cell and to
        # supply cell. Required for neigbouuring cell water suplly option, 
        # units = km3/ day.
        self.unsat_potnetabs_sw_from_demandcell = \
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))
        self.unsat_potnetabs_sw_to_supplycell = \
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))

        self.previous_demand_before_second_cell_allocation = np.nan * \
            np.zeros((forcings_static.lat_length, forcings_static.lon_length))

        # This is a 2d array of integer tuples which contains lat and lon index
        # values of selected neighbour cell with high water availability
        self.get_neighbouring_cells_map = np.zeros((forcings_static.lat_length,
                                                    forcings_static.lon_length),
                                                   dtype=np.dtype('(2,)i4'))

    #                  =====================================================
    #                  ||  Activcate Reservior and Regulated lake storage ||
    #                  =====================================================
    def activate_res_area_storage_capacity(self, simulation_date,
                                           reservoir_opt_year, restart):
        """
        Activate storage,area and capacity of reservoir in current year.

        see run_watergap.py module

        Parameters
        ----------
        simulation_date : np.datetime64
            Current day, month and year of simulation.
        reservoir_opt_year : np.datetime64
            Year of operation  for reservoir

        Returns
        -------
        None.

        """
        if cm.ant is True and cm.reservior_opt is True:

            m_to_km = 0.001
            # Activate  area and capacity of reservoir and regulated lake that
            # are  active in current year
            if simulation_date.astype('datetime64[D]') in reservoir_opt_year \
                or self.set_res_storage_flag == True or \
                    self.check_res_area_flag == True:
                
                resyear = pd.to_datetime(simulation_date).year

                # Initialize reservior and regulated lake capacity, Units : km3
                glores_capacity_active = self.static_data.\
                    res_reg_files.stor_cap[0].values.astype(np.float64)

                # ---------------------------------
                # Regulated Lakes Area and Capacity
                # ----------------------------------
                self.glores_area = \
                    np.where((self.regulated_lake_status == 1),
                             self.all_reservoir_and_regulated_lake_area,
                             self.glores_area)

                self.glores_capacity = \
                    np.where((self.regulated_lake_status == 1),
                             glores_capacity_active, self.glores_capacity)

                # ---------------------------
                # Reservoir Area and Capacity
                # ---------------------------
                # Initialize newly activated reservior area, Units : km2
                # Keep area values of already activate reservoirs
                self.glores_area =\
                    np.where(resyear >= self.glores_startyear,
                             self.all_reservoir_and_regulated_lake_area,
                             self.glores_area)

                # Initialize newly activated global reservior capacity,
                # Units : km3, Keep capacity values of already activate
                # reservoirs
                self.glores_capacity = \
                    np.where(resyear >= self.glores_startyear,
                             glores_capacity_active, self.glores_capacity)

                # ------------------------------------------------------
                # Reservoir area is added to global lake if
                # mean_annual_inflow_res = 0. reservoir area has to be set
                #  to zero after.
                # ------------------------------------------------------
                mask_mean_annual_inflow = \
                    ((self.glores_area > 0)
                     & (resyear >= self.glores_startyear)
                     & (self.mean_annual_inflow_res == 0))

                self.glolake_area =\
                    np.where(mask_mean_annual_inflow,
                             self.glores_area + self.glolake_area,
                             self.glolake_area)

                self.glores_area[mask_mean_annual_inflow] = 0
                self.all_reservoir_and_regulated_lake_area[mask_mean_annual_inflow] = 0

                # update maximum storage of global lake if reservoir becomes
                # global lake due to mean_annual_inflow_res = 0.
                # 1. Note (if mean_annual_inflow_res = 0.in 1st sim day):!!!!!!!****
                # (change/add maximum storage to reservoir capacity/2.
                # case:1 global lake aready exit (add)
                # case:2 no global lake (change)--->> based on Mohammeds regulated lake stuff 
                
                # 2. (if mean_annual_inflow_res = 0. in other years ):!!!!!!!****
                # case:1 global lake aready exit (add resrvoir initial storage to it )
                # case:2 no global lake (make a new global lake with resrvoir 
                # initial storage))--->> 
                
                self.max_glolake_storage = self.glolake_area * \
                    self.parameters.activelake_depth.values * m_to_km 
                
                # This is set should be set to false to enable that 
                # reservoir and regulated lake are initiallised once each year 
                self.check_res_area_flag = False
                    
                    
            # Note!: Storages are activated on the 1st day of the year
            if self.set_res_storage_flag == True:

                simu_start_year = pd.to_datetime(cm.start).year

                # If run is a restart run, saved storage is used
                # -----------------
                # Reservoir Storage
                # -----------------
                # # Initialize newly activated reservior storage in
                # the current year to maximum,  Units : km3
                # Keep storage values of already activate reservoirs
                glores_storage_active = self.static_data.\
                    res_reg_files.stor_cap[0].values.astype(np.float64)

                self.glores_storage = \
                    np.where(simu_start_year >= self.glores_startyear,
                             glores_storage_active,
                             self.glores_storage)

                # -------------------------
                # Regulated Lake Storage
                # -----------------------
                # For regulated lake: if it's not yet operational
                # increase reservoir storage by multiplying the area with
                # lake depth (Treat it as a global lake)- changed by mohammed 
                self.glores_storage =\
                    np.where((simu_start_year < self.glores_startyear) &
                             (self.regulated_lake_status == 1),
                             (self.all_reservoir_and_regulated_lake_area *
                              self.parameters.activelake_depth.values * m_to_km)
                             + self.glores_storage,
                             self.glores_storage)

                self.reg_lake_redfactor_firstday = \
                    np.where((simu_start_year < self.glores_startyear) &
                             (self.regulated_lake_status == 1), 1,
                             0)

                self.reg_lake_redfactor_firstday = \
                    np.where((self.glores_storage == glores_storage_active) &
                             (self.regulated_lake_status == 1), 0,
                             self.reg_lake_redfactor_firstday)

                # update initial storage of global lake if reservoir
                # becomes global lake due to mean_annual_inflow_res = 0.
                self.glolake_storage = self.max_glolake_storage

                # set initialization flag to False
                self.set_res_storage_flag = False

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Calculate Lateral Water Balance
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def calculate(self, diffuse_gw_recharge, openwater_pot_evap, precipitation,
                  surface_runoff, daily_storage_transfer,
                  current_landarea_frac, previous_landarea_frac,
                  simulation_date, first_day_of_month, basin):
        """
        Calculate lateral water balance.

        Parameters
        ----------
        diffuse_gw_recharge : array
            Daily difuuse groundwater recharge, Unit: mm/day
        openwater_pot_evap : array
            Daily open water potential evaporation, Unit: mm/day
        precipitation : array
            Daily precipitation, Unit: mm/day
        surface_runoff : array
            Daily surface runoff, unit: mm/day.
        daily_storage_transfer : array
            Storage to be transfered to runoff when land area fraction of
            current time step is zero, Units: mm
        current_landarea_frac: array
            Current land area fraction
        previous_landarea_frac: array
            Previous land area fraction
        simulation_date: np.datetime64
            Current day, month and year of simulation.

        Returns
        -------
        None.

        """
        # =====================================================================
        # Converting input fluxes from  mm/day to km/day or km3/day
        # =====================================================================
        mm_to_km = 1e-6
        # Fluxes in km/day
        precipitation *= mm_to_km
        openwater_pot_evap *= mm_to_km

        # Fluxes in km3/day
        diffuse_gw_recharge = diffuse_gw_recharge * self.cell_area * \
            mm_to_km * current_landarea_frac

        daily_storage_transfer = daily_storage_transfer * self.cell_area * \
            mm_to_km * previous_landarea_frac

        surface_runoff = surface_runoff * self.cell_area * mm_to_km * \
            current_landarea_frac

        # When cuurent land area fraction = 0, canopy, snow, and soil storage
        # from the previous timestep (stored in daily_storage_transfer)
        # becomes surface runoff
        surface_runoff = np.where(current_landarea_frac == 0,
                                  daily_storage_transfer, surface_runoff)

        # =====================================================================
        # Selecting potential net abstraction (surface or groundwater) for
        # current day
        # =====================================================================
        #      =============================================================
        #      || Potential net abstraction from surface and ground water ||
        #      =============================================================
        # get current year and month to select relevant net abstraction data
        current_year_mon_day = [str(pd.to_datetime(simulation_date).year),
                                str(pd.to_datetime(simulation_date).month),
                                int(pd.to_datetime(simulation_date).day)]

        date = current_year_mon_day[0] + "-" + current_year_mon_day[1]

        # Select monthly abastraction data and convert to daily
        m3_to_km3 = 1e9
        days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31,
                         8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
        # Check if current day is first available day of the month.
        # Required to load in NAs and NAg value (during a restart run)
        first_day = [pd.to_datetime(date).day for date in first_day_of_month if
                     pd.to_datetime(date) == pd.to_datetime(simulation_date)]
        first_day = first_day[0] if len(first_day) > 0 else 0

        # get cuurent day
        current_day = current_year_mon_day[2]

        # Only consider abstraction in anthropogenic run.

        # if cm.subtract_use is True:
        for month, num_of_days in days_in_month.items():
            if month == int(pd.to_datetime(simulation_date).month) and \
                    current_day == first_day:
                self.num_days_in_month = num_of_days

                if cm.subtract_use is True:
                    # data unit read in =m3/month
                    self.potential_net_abstraction_gw = self.potential_net_abstraction.pnag.\
                        sel(time=date)[0].values.astype(np.float64)

                    # coverted to units = km3/day
                    self.potential_net_abstraction_gw = \
                        self.potential_net_abstraction_gw / (num_of_days * m3_to_km3)

                    # *********************************************************
                    # Aggregate potential net abstaraction of riparaian cell to
                    # outflow cell and convert to km3/day
                    # *********************************************************
                    # data unit read in = m3/month
                    self.potential_net_abstraction_sw = self.potential_net_abstraction.pnas.\
                        sel(time=date)[0].values.astype(np.float64)

                    # Monthly demand for reservoir release compution (km3/month)
                    self.monthly_potential_net_abstraction_sw = \
                        self.potential_net_abstraction_sw.copy()/m3_to_km3

                    #  coverted to units = km3/day
                    self.unagregrgated_potential_netabs_sw = self.potential_net_abstraction_sw.copy()/(num_of_days * m3_to_km3)

                    self.potential_net_abstraction_sw = self.get_aggr_func.\
                        aggregate_riparian_netpotabs(self.glolake_area,
                                                     self.glores_area,
                                                     self.potential_net_abstraction_sw)

                    # outflow cells of global lakes, regulated lakes and
                    # reseviors have aggregated potential net abstraction.
                    # Respective riparian cells have values of 0.
                    #  coverted to units = km3/day
                    self.potential_net_abstraction_sw = \
                        self.potential_net_abstraction_sw / (num_of_days * m3_to_km3)
                        
                    # *********************************************************
                    # load in Potential water withdrawal from surfacewater and
                    #  consumptive use and convert to km3/day
                    # *********************************************************
                    # data unit read in =m3/month
                    self.potential_water_withdrawal_sw_irri = self.potential_net_abstraction.pirrig_ww.\
                        sel(time=date)[0].values.astype(np.float64)

                    #  coverted to units = km3/day
                    self.potential_water_withdrawal_sw_irri = \
                        self.potential_water_withdrawal_sw_irri / (num_of_days * m3_to_km3)

                    # data unit read in =m3/month
                    self.potential_consumptive_use_sw_irri = self.potential_net_abstraction.pirrig_cu.\
                        sel(time=date)[0].values.astype(np.float64)

                    #  coverted to units = km3/day
                    self.potential_consumptive_use_sw_irri = \
                        self.potential_consumptive_use_sw_irri / (num_of_days * m3_to_km3)

        # ------------
        # Delayed use
        # ------------
        # At the begining of each day accumulated unsatisfied potential net
        # abstraction from surface water is added to daily potential net
        # abstraction from surface water. This is attempted to be satisfied
        # untill the end of the calendar year where it is set to zero
        # (see section *Update accumulated unsatisfied potential net
        # abstraction from surface water and and daily_unsatisfied_pot_nas* in
        # this module below)

        accumulated_unsatisfied_potential_netabs_sw = \
            np.zeros_like(self.potential_net_abstraction_sw) # changes im the loop need fix !!!!!!!!!!!!!!!!
        if cm.subtract_use is True:
            if cm.delayed_use is True:
                accumulated_unsatisfied_potential_netabs_sw =  \
                    self.potential_net_abstraction_sw + \
                    self.accumulated_unsatisfied_potential_netabs_sw
            else:
                accumulated_unsatisfied_potential_netabs_sw =  \
                     self.potential_net_abstraction_sw.copy()
        demand_with_delayed_use = accumulated_unsatisfied_potential_netabs_sw.copy()
        # =====================================================================
        #   Additional  input variables for river routing
        # =====================================================================

        glwdunits = self.get_aggr_func.glwdunits

        # current_mon_day will be used to check if reservoirs opreation start
        # in current month. This is required to calulate the release factor
        # using the  Hanasaki reservoir algorithm
        # (see module reservior_and_regulated_lakes.py )
        current_mon_day = np.array([int(current_year_mon_day[1]),
                                    current_year_mon_day[2]])

        river_length = self.get_river_prop.river_length
        river_bottom_width = self.get_river_prop.river_bottom_width
        roughness = self.get_river_prop.roughness
        river_slope = self.get_river_prop.river_slope
        neighbouring_cells_map = self.get_neighbouring_cells_map.copy()
        
        # =====================================================================
        # Routing (Routing function is optimised for with numba)
        # =====================================================================
        #                   ++Sequence++
        # groudwater(only humidcells)->local lakes->local wetland->...
        # global lakes->reservior & regulated lakes->global wetalnds->river
        out = rt.rout(self.rout_order, self.outflow_cell,
                      self.drainage_direction, self.aridhumid,
                      precipitation, openwater_pot_evap, surface_runoff,
                      diffuse_gw_recharge, self.groundwater_storage,
                      self.loclake_storage, self.locwet_storage,
                      self.glolake_storage, self.glores_storage,
                      self.glowet_storage, self.river_storage,
                      self.max_loclake_storage, self.max_locwet_storage,
                      self.max_glolake_storage, self.max_glowet_storage,
                      self.glores_capacity, self.max_loclake_area,
                      self.max_locwet_area, self.glolake_area,
                      self.glores_area, self.max_glowet_area,
                      self.loclake_frac, self.locwet_frac,
                      self.glowet_frac, self.glolake_frac,
                      self.reglake_frac, self.headwatercell,
                      self.parameters.gw_dis_coeff.values,
                      self.parameters.swb_drainage_area_factor.values,
                      self.parameters.swb_outflow_coeff.values,
                      self.parameters.gw_recharge_constant.values,
                      self.parameters.reduction_exponent_lakewet.values,
                      self.parameters.reduction_exponent_res.values,
                      self.parameters.lake_out_exp.values,
                      self.parameters.wetland_out_exp.values,
                      self.parameters.areal_corr_factor.values,
                      self.parameters.stat_corr_fact.values,
                      river_length, river_bottom_width, roughness,
                      self.roughness_multiplier, river_slope,
                      glwdunits, self.glores_startmonth, current_mon_day,
                      self.k_release, self.glores_type, self.allocation_coeff,
                      self.mean_annual_demand_res, self.mean_annual_inflow_res,
                      self.potential_net_abstraction_gw,
                      self.potential_net_abstraction_sw,
                      self.unagregrgated_potential_netabs_sw,
                      accumulated_unsatisfied_potential_netabs_sw,
                      self.prev_accumulated_unsatisfied_potential_netabs_sw,
                      self.daily_unsatisfied_pot_nas,
                      self.monthly_potential_net_abstraction_sw,
                      self.prev_potential_water_withdrawal_sw_irri,
                      self.prev_potential_consumptive_use_sw_irri,
                      self.frac_irri_returnflow_to_gw,
                      self.unsatisfied_potential_netabs_riparian,
                      self.neighbourcells, self.neighbourcells_outflowcell,
                      self.unsat_potnetabs_sw_from_demandcell,
                      self.unsat_potnetabs_sw_to_supplycell,
                      neighbouring_cells_map,
                      cm.subtract_use,
                      cm.neighbouringcell, cm.reservior_opt,
                      self.num_days_in_month,
                      self.all_reservoir_and_regulated_lake_area,
                      self.reg_lake_redfactor_firstday, basin, cm.delayed_use)

        # update variables for next timestep or output.
        self.groundwater_storage = out[0]
        self.loclake_storage = out[1]
        self.locwet_storage = out[2]
        self.glolake_storage = out[3]
        self.glores_storage = out[4]
        self.k_release = out[5]
        self.glowet_storage = out[6]
        self.river_storage = out[7]
        groundwater_discharge = out[8]
        loclake_outflow = out[9]
        locwet_outflow = out[10]
        glolake_outflow = out[11]
        glowet_outflow = out[12]
        glores_outflow = out[28]
        

        # Streamflow is only stored for all cells except inland sinks
        streamflow = np.where(self.drainage_direction >= 0, out[13], np.nan)

        updated_locallake_fraction = out[15]
        updated_localwetland_fraction = out[16]
        updated_globalwetland_fraction = out[17]
        self.accumulated_unsatisfied_potential_netabs_sw = out[18]
        self.unsatisfied_potential_netabs_riparian = out[19]
        actual_net_abstraction_gw = out[20]
        self.unsat_potnetabs_sw_from_demandcell = out[21]
        self.unsat_potnetabs_sw_to_supplycell = out[22]
        water_demand_satis_neigbhourcell = out[23] # remove  !!!
        returned_demand_from_supply_cell = out[24]
        prev_returned_demand_from_supply_cell = out[25]
        self.get_neighbouring_cells_map = out[26]
        check_daily_unsatisfied_pot_nas = out[27]
        actual_daily_netabstraction_sw = out[29]

        # Egypt 
        # print(self.potential_net_abstraction_sw[117, 421],  
        #       actual_daily_netabstraction_sw[117, 421], 
        #       self.unsat_potnetabs_sw_from_demandcell[117, 421], 
        #       self.unsat_potnetabs_sw_to_supplycell[117, 421],
        #       returned_demand_from_supply_cell[117, 421], 
        #       prev_returned_demand_from_supply_cell[117, 421],
        #       self.accumulated_unsatisfied_potential_netabs_sw[117, 421])
        

        #  Morocco
        # print(total_demand[115, 343],
        #        actual_daily_netabstraction_sw[115, 343], 
        #        self.unsat_potnetabs_sw_from_demandcell[115, 343], 
        #        self.unsat_potnetabs_sw_to_supplycell[115, 343],
        #        returned_demand_from_supply_cell[115, 343], 
        #        prev_returned_demand_from_supply_cell[115, 343],
        #        self.accumulated_unsatisfied_potential_netabs_sw[115, 343])

        # x,y=179, 426
        # print(self.glores_storage[x, y], glores_outflow[x, y], current_landarea_frac[x, y])
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Update accumulated unsatisfied potential net abstraction from
        # surface water and daily_unsatisfied_pot_nas.
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Delayed Use and Neighbouring Cell Cases
        # 1. Routing order of demand cell > supply cell.
        #    The demand returned from the supply cell to the demand cell is
        #    calculated in the current time step. The daily unsatisfied use for
        #    the demand cell is computed at the end of the day.

        # 2. Routing order of demand cell < supply cell.
        #    The demand that is returned from the supply cell to the demand
        #    cell is calculated in the next time step. The daily unsatisfied
        #    use for the demand cell is set to zero for the previous step.
        #    - At the beginning of this next time step:
        #       • The daily unsatisfied use for the demand cell is computed
        #       • The returned demand of the demand cell (computed in the next
        #          time step) is added to the accumulated unsatisfied use to
        #          obey the delayed use principle.
        #   - At the end of this next time step:
        #       • This same returned demand is used to calculate the daily
        #           unsatisfied use, together with the new accumulated
        #           remaining use, at the end of this day.

        self.accumulated_unsatisfied_potential_netabs_sw = \
            np.where(~np.isnan(returned_demand_from_supply_cell),
                     returned_demand_from_supply_cell,
                     self.accumulated_unsatisfied_potential_netabs_sw)

        if cm.subtract_use is True:
            if cm.delayed_use is True:
                
                self.prev_accumulated_unsatisfied_potential_netabs_sw = \
                    np.where(~np.isnan(prev_returned_demand_from_supply_cell),
                             prev_returned_demand_from_supply_cell,
                             self.prev_accumulated_unsatisfied_potential_netabs_sw)
                
                end_of_year = [str(pd.to_datetime(simulation_date).month),
                               str(pd.to_datetime(simulation_date).day)]
                # accumulated_unsatisfied_potential_netabs_sw and
                # daily_unsatisfied_pot_nas is zero at the end of the calender
                # year
                if end_of_year[0] == '12' and end_of_year[1] == '31':
                    self.accumulated_unsatisfied_potential_netabs_sw = \
                        np.zeros_like(self.accumulated_unsatisfied_potential_netabs_sw)
                    self.daily_unsatisfied_pot_nas = \
                        np.zeros_like(self.daily_unsatisfied_pot_nas)
                else:
                    self.daily_unsatisfied_pot_nas = \
                        np.where(~np.isnan(check_daily_unsatisfied_pot_nas),
                                  self.accumulated_unsatisfied_potential_netabs_sw - 
                                  self.prev_accumulated_unsatisfied_potential_netabs_sw,
                                  0)
                        
                self.prev_accumulated_unsatisfied_potential_netabs_sw = \
                    np.where(~np.isnan(check_daily_unsatisfied_pot_nas),
                             self.accumulated_unsatisfied_potential_netabs_sw.copy(),
                             self.prev_accumulated_unsatisfied_potential_netabs_sw)
                        
            else:
                self.daily_unsatisfied_pot_nas = \
                    self.accumulated_unsatisfied_potential_netabs_sw.copy()

        

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # The ff. variables also needed to  adapt potential net abstraction
        # from groundwter. previous potential water withdrawal and comsumptive
        # use from surfacewater for irrigation
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.prev_potential_water_withdrawal_sw_irri =\
            self.potential_water_withdrawal_sw_irri.copy()

        self.prev_potential_consumptive_use_sw_irri = \
            self.potential_consumptive_use_sw_irri.copy()

        self.reg_lake_redfactor_firstday = \
            np.zeros_like(self.reg_lake_redfactor_firstday)
        # =====================================================================
        # Getting all storages
        # =====================================================================
        LateralWaterBalance.storages.\
            update({'groundwstor': self.groundwater_storage,
                    'locallakestor': self.loclake_storage,
                    'localwetlandstor': self.locwet_storage,
                    'globallakestor': self.glolake_storage,
                    'globalwetlandstor': self.glowet_storage,
                    'riverstor': self.river_storage,
                    "glores_stor": self.glores_storage})

        # =====================================================================
        # Getting all fluxes
        # =====================================================================
        # Note that these variables are directly changed in the "rout"
        # function and hence they are copied to prevent variables from being 
        # overwritten when writing out.
        unsat_potnetabs_sw_to_supplycell_out =  self.unsat_potnetabs_sw_to_supplycell.copy() 
        unsat_potnetabs_sw_from_demandcell_out =  self.unsat_potnetabs_sw_from_demandcell.copy() 
        accumulated_unsatisfied_potential_netabs_sw_out = self.accumulated_unsatisfied_potential_netabs_sw.copy() 
        unsatisfied_potential_netabs_riparian_out = self.unsatisfied_potential_netabs_riparian.copy() 
        get_neighbouring_cells_map_out = self.get_neighbouring_cells_map.copy()
        
        LateralWaterBalance.fluxes.\
            update({'qg': groundwater_discharge,
                   'locallake_outflow': loclake_outflow,
                    'localwetland_outflow': locwet_outflow,
                    'globallake_outflow': glolake_outflow,
                    'globalwetland_outflow': glowet_outflow,
                    'dis': streamflow,
                    'actual_net_abstraction_gw':
                        actual_net_abstraction_gw,
                    "demand_satisfied_by_cell":
                        actual_daily_netabstraction_sw,
                    "demand_with_delayed_use": demand_with_delayed_use,
                    "unsat_potnetabs_sw_from_demandcell":
                        unsat_potnetabs_sw_from_demandcell_out,
                    "returned_demand_from_supply_cell": 
                        returned_demand_from_supply_cell,
                    "prev_returned_demand_from_supply_cell":
                        prev_returned_demand_from_supply_cell,
                    "accumulated_unsatisfied_potential_netabs_sw":
                        accumulated_unsatisfied_potential_netabs_sw_out,
                    "unsat_potnetabs_sw_to_supplycell": 
                        unsat_potnetabs_sw_to_supplycell_out, 
                    "unsatisfied_potential_netabs_riparian":
                        unsatisfied_potential_netabs_riparian_out,
                    "get_neighbouring_cells_map": get_neighbouring_cells_map_out})
            
        # =====================================================================
        #  Get dynamic area fraction for local lakes and local and
        #  global wetlands
        # =====================================================================
        LateralWaterBalance.land_swb_fraction.update({
            "current_landareafrac": current_landarea_frac,
            "new_locallake_fraction":  updated_locallake_fraction,
            "new_localwetland_fraction": updated_localwetland_fraction,
            "new_globalwetland_fraction":  updated_globalwetland_fraction})

    def get_storages_and_fluxes(self):
        """
        Get daily storages and fluxes for vertical waterbalance.

        Returns
        -------
        dict
            Dictionary of all storages.
        dict
           Dictionary of all fluxes.

        """
        return LateralWaterBalance.storages, LateralWaterBalance.fluxes

    def get_new_swb_fraction(self):
        """
        Get daily  dynamic fraction.

        These fractions constist of updated local lakes and local and global
        wetland fractions.

        Returns
        -------
        dict
          updated fractions from surface water bodies without rivers and
          global lakes.

        """
        return LateralWaterBalance.land_swb_fraction

    def update_latbal_for_restart(self, latbalance_states):
        """
        Update vertical balance parameters for model restart from pickle file.

        Parameters
        ----------
        latbalance_states : dictionary
            Dictionary of all lateral balance storages.

        Returns
        -------
        None.

        """
        self.groundwater_storage = \
            latbalance_states["groundwater_storage"]
        self.loclake_storage = latbalance_states["loclake_storage"]
        self.locwet_storage = latbalance_states["locwet_storage"]

        self.glolake_storage = latbalance_states["glolake_storage"]
        self.glowet_storage = latbalance_states["glowet_storage"]
        self.river_storage = latbalance_states["river_storage"]

        self.glores_storage = latbalance_states["glores_storage"]
        self.k_release = latbalance_states["k_release"]

        self.unsatisfied_potential_netabs_riparian = \
            latbalance_states["unsatisfied_potential_netabs_riparian"]
        self.unsat_potnetabs_sw_from_demandcell = \
            latbalance_states["unsat_potnetabs_sw_from_demandcell"]
        self.unsat_potnetabs_sw_to_supplycell =  \
            latbalance_states["unsat_potnetabs_sw_to_supplycell"]      
        self.get_neighbouring_cells_map = \
            latbalance_states["neighbouring_cells_map"]
            
        self.accumulated_unsatisfied_potential_netabs_sw = \
            latbalance_states["accumulated_unsatisfied_potential_netabs_sw"]
        self.daily_unsatisfied_pot_nas = \
            latbalance_states["daily_unsatisfied_pot_nas"]

        self.prev_accumulated_unsatisfied_potential_netabs_sw = \
            latbalance_states["prev_accumulated_unsatisfied_potential_netabs_sw"]
        self.prev_potential_water_withdrawal_sw_irri = \
            latbalance_states["prev_potential_water_withdrawal_sw_irri"]
        self.prev_potential_consumptive_use_sw_irri = \
            latbalance_states["prev_potential_consumptive_use_sw_irri"]
        
        self.set_res_storage_flag = latbalance_states["set_res_storage_flag"]
