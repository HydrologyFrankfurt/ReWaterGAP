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

    def __init__(self, forcings_static, pot_net_abstraction, parameters):
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

        self.parameters = parameters
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
        self.loclake_frac = self.static_data.\
            land_surface_water_fraction.loclak[0].values.astype(np.float64)/100

        # Initializing local lake storage to maximum
        # Local lake area and storage,  Units : km2 & km3 respectively
        m_to_km = 0.001

        self.max_loclake_area = self.cell_area * self.loclake_frac
        self.max_loclake_storage = self.max_loclake_area * \
            self.parameters.activelake_depth * m_to_km

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
            self.parameters.activewetland_depth * m_to_km

        self.locwet_storage = self.max_locwet_storage

        #                  =================================
        #                  ||          Global lake        ||
        #                  =================================

        self.glolake_frac = self.static_data.\
            land_surface_water_fraction.glolak[0].values.astype(np.float64)/100

        # Global lake area Units : km2
        self.glolake_area = forcings_static.global_lake_area

        # Initializing global lake storage to maximum,  Units : km3
        self.max_glolake_storage = self.glolake_area * \
            self.parameters.activelake_depth * m_to_km
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
            self.parameters.activewetland_depth * m_to_km
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
        # units was converted from m3/year to m3/s
        # 31536000=(365 * 24 * 60 * 60)
        year_to_s = 31536000
        self.mean_annual_demand_res = self.static_data.\
            res_reg_files.mean_nus[0].values.astype(np.float64) / year_to_s

        # Mean annual inflow in to reservior
        # Units was converted from km3/month to m3/s
        self.mean_annaul_inflow_res = self.static_data.res_reg_files.\
            mean_inflow[0].values.astype(np.float64) * 12 * 1e9 / year_to_s

        # reservoir release coefficient  units: (-)
        # E.g  for environmental flow requirement reselease is initialised
        # as 0.1
        self.k_release = np.zeros((forcings_static.lat_length,
                                   forcings_static.lon_length)) + 0.1

        # Regulated lake fraction
        self.reglake_frac = self.static_data.\
            land_surface_water_fraction.reglak[0].values.astype(np.float64)/100

        # Regulated lake storage, Units : km3 *****(yet to be done)

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

        # This is a 2d array of integer tuples which contains lat and lon index
        # values of selected neighbour cell with high water availability
        self.neighbouring_cells_map = np.zeros((forcings_static.lat_length,
                                               forcings_static.lon_length),
                                               dtype=np.dtype('(2,)i4'))

    #                  =====================================================
    #                  ||  Activcate Reservior and Regulated lake storage ||
    #                  =====================================================
    def activate_res_area_storage_capacity(self, simulation_date,
                                           reservoir_opt_year):
        """
        Activate storage,area and capacity of reservoir in current year.

        see run_watergap.py module

        Parameters
        ----------
        simulation_date : np.datetime64
            Current day, month and year of simulation.
        reservoir_opt_year : int
            Year of activation for reservoir

        Returns
        -------
        None.

        """
        # Activate storage, area and capacity of reservoir that are  active
        # in current year
        if cm.ant is True and cm.reservior_opt is True:
            if simulation_date in reservoir_opt_year:
                resyear = int(pd.to_datetime(simulation_date).year)

                glores_storage_active = self.static_data.\
                    res_reg_files.stor_cap[0].values.astype(np.float64)

                # Initialize reservior and regulated lake area, Units :km2
                glores_area_active = self.static_data.\
                    land_surface_water_fraction.reservoir_and_regulated_lake_area[0].\
                    values.astype(np.float64)

                # Initialize reservior capacity,  Units : km3
                glores_capacity_active = self.static_data.\
                    res_reg_files.stor_cap[0].values.astype(np.float64)

                # # Initialize newly activated reservior storage in
                # the current year to maximum,  Units : km3
                # Keep storage values of already activate reservoirs
                self.glores_storage = \
                    np.where(self.glores_startyear == resyear,
                             glores_storage_active,
                             self.glores_storage)

                # Initialize newly activated reservior area, Units : km2
                # Keep area values of already activate reservoirs
                self.glores_area = np.where(self.glores_startyear == resyear,
                                            glores_area_active,
                                            self.glores_area)

                # Initialize newly activated global reservior capacity,
                # Units : km3, Keep capacity values of already activate
                # reservoirs
                self.glores_capacity = \
                    np.where(self.glores_startyear == resyear,
                             glores_capacity_active,
                             self.glores_capacity)

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Calculate Lateral Water Balance
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def calculate(self, diffuse_gw_recharge, openwater_pot_evap, precipitation,
                  surface_runoff, daily_storage_transfer,
                  current_landarea_frac, previous_landarea_frac,
                  simulation_date):
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
        # from the previous timestep  becomes surface runoff
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
        first_day = current_year_mon_day[2]

        # Only consider abstraction in anthropogenic run.
        if cm.subtract_use is True:
            for month, num_of_days in days_in_month.items():
                if month == int(pd.to_datetime(simulation_date).month) and \
                        first_day == 1:
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
                    # data unit read in =m3/month
                    self.potential_net_abstraction_sw = self.potential_net_abstraction.pnas.\
                        sel(time=date)[0].values.astype(np.float64)

                    #  coverted to units = km3/day
                    self.unagregrgated_potential_netabs_sw = self.potential_net_abstraction_sw.copy()/(num_of_days * m3_to_km3)

                    self.potential_net_abstraction_sw = self.get_aggr_func.\
                        aggregate_riparian_netpotabs(self.glolake_area,
                                                     self.glores_area,
                                                     self.potential_net_abstraction_sw)

                    # outflow cells of global lakes, regulated lakes and
                    # reseviors have aggregated potential net abstraction.
                    # Respective riparian cells have values of 0
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

        if cm.subtract_use is True and cm.delayed_use is True:
            self.accumulated_unsatisfied_potential_netabs_sw += \
                self.potential_net_abstraction_sw
        else:
            self.accumulated_unsatisfied_potential_netabs_sw = \
                self.potential_net_abstraction_sw

        # --------------------------------------------------------------------

        # Actual name: Potential net abstraction from surface water (NApot,s),
        # Unit=m3/month (for hanasaki i will change later)
        monthly_potential_net_abstraction_sw = np.zeros(surface_runoff.shape)
        # potential_net_abstraction.pnas.values.astype(np.float64)

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
                      self.parameters.gw_dis_coeff,
                      self.parameters.swb_drainage_area_factor,
                      self.parameters.swb_outflow_coeff,
                      self.parameters.gw_recharge_constant,
                      self.parameters.reduction_exponent_lakewet,
                      self.parameters.reduction_exponent_res,
                      self.parameters.lake_out_exp,
                      self.parameters.wetland_out_exp,
                      self.parameters.areal_corr_factor,
                      self.parameters.stat_corr_fact,
                      river_length, river_bottom_width, roughness,
                      self.roughness_multiplier, river_slope,
                      glwdunits, self.glores_startmonth, current_mon_day,
                      self.k_release, self.glores_type, self.allocation_coeff,
                      self.mean_annual_demand_res, self.mean_annaul_inflow_res,
                      self.potential_net_abstraction_gw,
                      self.potential_net_abstraction_sw,
                      self.unagregrgated_potential_netabs_sw,
                      self.accumulated_unsatisfied_potential_netabs_sw,
                      self.prev_accumulated_unsatisfied_potential_netabs_sw,
                      self.daily_unsatisfied_pot_nas,
                      monthly_potential_net_abstraction_sw,
                      self.prev_potential_water_withdrawal_sw_irri,
                      self.prev_potential_consumptive_use_sw_irri,
                      self.frac_irri_returnflow_to_gw,
                      self.unsatisfied_potential_netabs_riparian,
                      self.neighbourcells, self.neighbourcells_outflowcell,
                      self.unsat_potnetabs_sw_from_demandcell,
                      self.unsat_potnetabs_sw_to_supplycell,
                      self.neighbouring_cells_map,
                      cm.subtract_use,
                      cm.neighbouringcell)

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

        # Streamflow is only stored for all cells except inland sinks
        streamflow = np.where(self.drainage_direction >= 0, out[13], np.nan)

        updated_locallake_fraction = out[15]
        updated_localwetland_fraction = out[16]
        updated_globalwetland_fraction = out[17]
        self.unsatisfied_potential_netabs_riparian = out[19]
        actual_net_abstraction_gw = out[20]
        self.unsat_potnetabs_sw_from_demandcell = out[21]
        self.unsat_potnetabs_sw_to_supplycell = out[22]

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Update accumulated unsatisfied potential net abstraction from
        # surface water and daily_unsatisfied_pot_nas.
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.accumulated_unsatisfied_potential_netabs_sw = out[18]

        if cm.subtract_use is True and cm.delayed_use is True:
            end_of_year = [str(pd.to_datetime(simulation_date).month),
                           str(pd.to_datetime(simulation_date).day)]
            # accumulated_unsatisfied_potential_netabs_sw and
            # daily_unsatisfied_pot_nas is zero at the end of the calender year
            if end_of_year[0] == '12' and end_of_year[1] == '31':
                self.accumulated_unsatisfied_potential_netabs_sw = \
                    np.zeros_like(self.accumulated_unsatisfied_potential_netabs_sw)
                self.daily_unsatisfied_pot_nas = \
                    np.zeros_like(self.daily_unsatisfied_pot_nas)
            else:
                self.daily_unsatisfied_pot_nas = \
                    self.accumulated_unsatisfied_potential_netabs_sw - \
                    self.prev_accumulated_unsatisfied_potential_netabs_sw
        else:
            self.daily_unsatisfied_pot_nas = \
                self.accumulated_unsatisfied_potential_netabs_sw

        self.prev_accumulated_unsatisfied_potential_netabs_sw = \
            self.accumulated_unsatisfied_potential_netabs_sw.copy()
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # The ff. variables also needed to  adapt potential net abstraction
        # from groundwter.
        # previous potential water withdrawal from surfacewater for irrigation

        self.prev_potential_water_withdrawal_sw_irri =\
            self.potential_water_withdrawal_sw_irri.copy()

        self.prev_potential_consumptive_use_sw_irri = \
            self.potential_consumptive_use_sw_irri.copy()

        print(self.river_storage[17, 192], streamflow[17, 192])

        # =====================================================================
        # Getting all storages
        # =====================================================================
        # Remove ocean cells from data
        mask_con = (self.cell_area/self.cell_area)

        LateralWaterBalance.storages.\
            update({'groundwstor': self.groundwater_storage*mask_con,
                    'locallakestor': self.loclake_storage*mask_con,
                    'localwetlandstor': self.locwet_storage*mask_con,
                    'globallakestor': self.glolake_storage*mask_con,
                    'globalwetlandstor': self.glowet_storage*mask_con,
                    'riverstor': self.river_storage*mask_con})

        # =====================================================================
        # Getting all fluxes
        # =====================================================================

        LateralWaterBalance.fluxes.\
            update({'qg': groundwater_discharge*mask_con,
                   'locallake_outflow': loclake_outflow*mask_con,
                    'localwetland_outflow': locwet_outflow*mask_con,
                    'globallake_outflow': glolake_outflow*mask_con,
                    'globalwetland_outflow': glowet_outflow*mask_con,
                    'dis': streamflow*mask_con,
                    'actual_net_abstraction_gw':
                        actual_net_abstraction_gw*mask_con})

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
            latbalance_states["groundwater_storage_prev"]
        self.loclake_storage = latbalance_states["loclake_storage_prev"]
        self.locwet_storage = latbalance_states["locwet_storage_prev"]

        self.glolake_storage = latbalance_states["glolake_storage_prev"]
        self.glowet_storage = latbalance_states["glowet_storage_prev"]
        self.river_storage = latbalance_states["river_storage_prev"]