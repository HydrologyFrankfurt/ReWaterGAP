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
# This module brings all lateral water balance functions together to run and
# makes use of numba to optimize speed (especially routing)
# =============================================================================

import numpy as np
import pandas as pd
from core.lateralwaterbalance import river_property as rvp
from core.lateralwaterbalance import rout_flow as rt
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
        self.arid = self.static_data.humid_arid
        self.drainage_direction = \
            self.static_data.soil_static_files.drainage_direction[0].values

        #                  =================================
        #                  ||          Groundwater        ||
        #                  =================================

        # Groundwater storage, Units : km3
        self.groundwater_storage = np.zeros((forcings_static.lat_length,
                                            forcings_static.lon_length))

        # Net groundwater abstraction , Units : km3/ day
        self.netabs_gw = np.zeros((forcings_static.lat_length,
                                   forcings_static.lon_length))
        # Total unsatified Water use, units = km3/ day
        self.remaining_use = np.zeros((forcings_static.lat_length,
                                      forcings_static.lon_length))

        #                  =================================
        #                  ||          Local lake         ||
        #                  =================================
        self.loclake_frac = self.static_data.\
            land_surface_water_fraction.loclak[0].values.astype(np.float64)/100

        # Initializing local lake storage to maximum
        m_to_km = 0.001
        max_loclake_storage = self.cell_area * self.loclake_frac * \
            self.parameters.activelake_depth * m_to_km

        # Local lake storage, Units : km3
        self.loclake_storage = max_loclake_storage

        #                  =================================
        #                  ||          Local wetland      ||
        #                  =================================

        self.locwet_frac = self.static_data.\
            land_surface_water_fraction.locwet[0].values.astype(np.float64)/100

        # Initializing local weltland storage to maximum
        max_locwet_storage = self.cell_area * self.locwet_frac * \
            self.parameters.activewetland_depth * m_to_km

        # Local wetland storage, Units : km3
        self.locwet_storage = max_locwet_storage

        #                  =================================
        #                  ||          Global lake        ||
        #                  =================================

        self.glolake_frac = self.static_data.\
            land_surface_water_fraction.glolak[0].values.astype(np.float64)/100

        # Global lake area Units : km2
        self.glolake_area = forcings_static.global_lake_area

        # Initializing global lake storage to maximum,  Units : km3
        self.glolake_storage = self.glolake_area * self.parameters.activelake_depth * \
            m_to_km

        #                  =================================
        #                  ||        Global  wetland      ||
        #                  =================================
        self.glowet_frac = self.static_data.\
            land_surface_water_fraction.glowet[0].values.astype(np.float64)/100

        # Initializing global weltland storage to maximum, , Units : km3
        max_glowet_storage = self.cell_area * self.glowet_frac * \
            self.parameters.activewetland_depth * m_to_km
        self.glowet_storage = max_glowet_storage

        #                  =================================
        #                  ||            River            ||
        #                  =================================

        # The following river properties are input into the RiverProperties
        # function  which ouputs other properties such as
        # river bottom width (km), maximum river storage (km3),  river length
        # corrected with continental area fraction (km).

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

        # River length (km)**
        river_length = self.static_data.river_static_files.\
            river_length[0].values.astype(np.float64)

        # Bank full river flow (m3/s)
        bankfull_flow = self.static_data.river_static_files.\
            bankfull_flow[0].values.astype(np.float64)

        # continental area fraction (-)
        continental_fraction = self.static_data.\
            land_surface_water_fraction.contfrac.values.astype(np.float64)

        self.get_river_prop = rvp.RiverProperties(river_slope, roughness,
                                                  river_length, bankfull_flow,
                                                  continental_fraction)

        # Initiliase routing order and respective outflow cell
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
        # Initializing global reservior stoarge, area and capacity to zero.
        # Note that once reservoirs are not active their coresponding storage,
        # area and capacity will be  zero.
        # (see activate_res_area_storage_capacity function).

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
        # read in units: m3/year, converted units : m3/s
        # 31536000=(365 * 24 * 60 * 60)
        year_to_s = 31536000
        self.mean_annual_demand_res = self.static_data.\
            res_reg_files.mean_nus[0].values.astype(np.float64) / year_to_s

        # Mean annual inflow in to reservior
        # read in units: km3/month, converted units : m3/s
        # note: km3/month is first converted to km3/year before m3/s
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

        # Regulated lake storage, Units : km3 *****

        #                  =================================
        #                  ||    Head water cells         ||
        #                  =================================
        self.headwater = self.static_data.\
            land_surface_water_fraction.headwater_cell.values

        #                  =================================
        #                  ||           WaterUSe         ||
        #                  =================================
        self.potential_net_abstraction = pot_net_abstraction.\
            potential_net_abstraction

    def activate_res_area_storage_capacity(self, simulation_date,
                                           reservoir_opt_year):
        """
        Activate storage,area and capacity of reservoir in current year.

        Parameters
        ----------
        simulation_date : TYPE
            DESCRIPTION.
        reservoir_opt_year : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        # Deactivate storage,area and capacity of reservoir that are not active
        # in current year
        if cm.reservior_opt == "on":
            if simulation_date in reservoir_opt_year:
                resyear = int(pd.to_datetime(simulation_date).year)

                glores_storage_active = self.static_data.\
                    res_reg_files.stor_cap[0].values.astype(np.float64)

                # Initialize reserviour and regulated lake area, Units :km2
                glores_area_active = self.static_data.\
                    land_surface_water_fraction.reservoir_and_regulated_lake_area[0].\
                    values.astype(np.float64)

                # Initialize reservior capacity,  Units : km3
                glores_capacity_active = self.static_data.\
                    res_reg_files.stor_cap[0].values.astype(np.float64)

                # # Initialize newly activated global reservior storage in
                # the current year to maximum,  Units : km3
                # Keep storage values of already activate reservoirs
                self.glores_storage = np.where(self.glores_startyear == resyear,
                                               glores_storage_active,
                                               self.glores_storage)

                # Initialize newly activated global reservior area, Units : km2
                # Keep area values of already activate reservoirs
                self.glores_area = np.where(self.glores_startyear == resyear,
                                            glores_area_active,
                                            self.glores_area)

                # Initialize newly activated global reservior capacity,
                # Units : km3, Keep capacity values of already activate
                # reservoirs
                self.glores_capacity = np.where(self.glores_startyear == resyear,
                                                glores_capacity_active,
                                                self.glores_capacity, )

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
        diffuse_gw_recharge = diffuse_gw_recharge * self.cell_area * mm_to_km * \
            current_landarea_frac

        daily_storage_transfer = daily_storage_transfer * self.cell_area * mm_to_km * \
            previous_landarea_frac

        surface_runoff = surface_runoff * self.cell_area * mm_to_km * \
            current_landarea_frac

        # When cuurent land area fraction = 0, canopy, snow, and soil storage
        # from the previous timestep  becomes surface runoff
        surface_runoff = np.where(current_landarea_frac == 0,
                                  daily_storage_transfer, surface_runoff)

        # =====================================================================
        # Selecting potential net abstraction for surface water for current
        # month
        # =====================================================================
        #           ===================================================
        #           || Potential net abstraction from surface water ||
        #           ==================================================
        date = simulation_date.astype("datetime64[M]")
        potential_net_abstraction = self.potential_net_abstraction.sel(
            time=str(date))
        # Actual name: Potential net abstraction from surface water NApot,
        # Unit=m3/month
        # yet to activate water use
        potential_net_abstraction_sw = np.zeros(surface_runoff.shape)
        # potential_net_abstraction.pnas.values.astype(np.float64)

        # =====================================================================
        # Preparing input variables for river routing
        # =====================================================================
        # Routing is optimised for with numba
        rout_order = self.rout_order.copy()
        arid = self.arid.copy()
        drainage_direction = self.drainage_direction.copy()
        groundwater_storage = self.groundwater_storage.copy()
        cell_area = self.cell_area.copy()
        netabs_gw = self.netabs_gw.copy()
        remaining_use = self.remaining_use.copy()
        loclake_frac = self.loclake_frac.copy()
        locwet_frac = self.locwet_frac.copy()
        glowet_frac = self.glowet_frac.copy()
        glolake_frac = self.glolake_frac.copy()
        reglake_frac = self.reglake_frac.copy()
        headwater = self.headwater.copy()
        loclake_storage = self.loclake_storage.copy()
        locwet_storage = self.locwet_storage.copy()
        glolake_storage = self.glolake_storage.copy()
        glolake_area = self.glolake_area.copy()

        glores_storage = self.glores_storage.copy()
        glores_capacity = self.glores_capacity.copy()
        glores_area = self.glores_area.copy()
        glores_type = self.glores_type.copy()
        mean_annual_demand_res = self.mean_annual_demand_res.copy()
        mean_annaul_inflow_res = self.mean_annaul_inflow_res.copy()
        allocation_coeff = self.allocation_coeff.copy()
        glores_startmonth = self.glores_startmonth.copy()
        k_release = self.k_release.copy()
        # current_mon_day will be used to check if reservoirs opreation start
        # in current month. This is required to calulate the release factor
        # using the  Hanasaki reservoir algorithm
        # (see module reservior_and_regulated_lakes.py )
        current_mon_day = np.array([int(pd.to_datetime(simulation_date).month),
                                    int(pd.to_datetime(simulation_date).day)])

        glowet_storage = self.glowet_storage.copy()

        river_storage = self.river_storage.copy()
        river_length = self.get_river_prop.river_length.copy()
        river_bottom_width = self.get_river_prop.river_bottom_width.copy()
        roughness = self.get_river_prop.roughness.copy()
        roughness_multiplier = self.roughness_multiplier.copy()
        river_slope = self.get_river_prop.river_slope.copy()
        outflow_cell = self.outflow_cell.copy()

        # =====================================================================
        # Routing
        # =====================================================================
        #                   ++Sequence++
        # groudwater(only humidcells)->local lakes->local wetland->...
        # global lakes->reservior & regulated lakes->global wetalnds->river

        out = rt.rout(rout_order, arid, drainage_direction,
                      groundwater_storage, diffuse_gw_recharge, cell_area,
                      netabs_gw, remaining_use, current_landarea_frac,
                      surface_runoff, loclake_frac, locwet_frac,
                      glowet_frac, glolake_frac, glolake_area,
                      reglake_frac, headwater, loclake_storage,
                      locwet_storage, glolake_storage, glowet_storage,
                      glores_storage, glores_capacity, glores_area,
                      glores_type, mean_annual_demand_res,
                      mean_annaul_inflow_res, allocation_coeff, k_release,
                      glores_startmonth, precipitation, openwater_pot_evap,
                      river_storage, river_length, river_bottom_width,
                      roughness, roughness_multiplier, river_slope,
                      outflow_cell,
                      self.parameters.gw_dis_coeff,
                      self.parameters.swb_drainage_area_factor,
                      self.parameters.swb_outflow_coeff,
                      self.parameters.gw_recharge_constant,
                      self.parameters.reduction_exponent_lakewet,
                      self.parameters.reduction_exponent_res,
                      self.parameters.areal_corr_factor,
                      self.parameters.lake_out_exp,
                      self.parameters.activelake_depth,
                      self.parameters.wetland_out_exp,
                      self.parameters.activewetland_depth,
                      self.parameters.stat_corr_fact,
                      current_mon_day,
                      potential_net_abstraction_sw)

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
        streamflow = np.where(drainage_direction >= 0, out[13], np.nan)

        updated_locallake_fraction = out[15]
        updated_localwetland_fraction = out[16]
        updated_globalwetland_fraction = out[17]

        # print(streamflow[94, 193], streamflow[182, 257])
        # =====================================================================
        # Getting all storages
        # =====================================================================
        # Remove ocean cells from data
        mask_con = (cell_area/cell_area)

        LateralWaterBalance.storages.\
            update({'groundwater_storage': self.groundwater_storage*mask_con,
                    'locallake_storage': self.loclake_storage*mask_con,
                    'localwetland_storage': self.locwet_storage*mask_con,
                    'globallake_storage': self.glolake_storage*mask_con,
                    'globalwetland_storage': self.glowet_storage*mask_con,
                    'river_storage': self.river_storage*mask_con})

        # =====================================================================
        # Getting all fluxes
        # =====================================================================

        LateralWaterBalance.fluxes.\
            update({'groundwater_discharge': groundwater_discharge*mask_con,
                   'locallake_outflow': loclake_outflow*mask_con,
                    'localwetland_outflow': locwet_outflow*mask_con,
                    'globallake_outflow': glolake_outflow*mask_con,
                    'globalwetland_outflow': glowet_outflow*mask_con,
                    'streamflow': streamflow*mask_con})

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
        Update vertical balance parameters for model restart.

        Parameters
        ----------
        vertbalance_states : TYPE
            DESCRIPTION.

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
