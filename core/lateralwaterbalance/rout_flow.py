# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"Routing"

# =============================================================================
# This module routes flow from surface runoff and groundwater to the river
# The routing scheme is based on figure 2 of  Müller Schmied et al. (2021).
#  The routing process involves compiting water balances including groundwater,
# local and global lakes, local and global wetlands,reservior & regulated lakes
# and river, storages and related fluxes for all grid cells based on section
# 4.5 to 4.7 of Müller Schmied et al. (2021)

# The routing sequence  folows the order:
# groudwater(only humidcells)->local lakes->local wetland->...
# global lakes->reservior & regulated lakes->global wetalnds->river

# This module also makes use of numba to optimize speed.
# =============================================================================

import numpy as np
from numba import njit
from core.lateralwaterbalance import groundwaterstorage as gws
from core.lateralwaterbalance import local_lakes_and_wetlands as lw
from core.lateralwaterbalance import fractional_routing as fr
from core.lateralwaterbalance import river_waterbalance as rb


@njit(cache=True)
def rout(rout_order, arid, drainage_direction,  groundwater_storage,
         diffuse_gw_recharge, cell_area, netabs_gw, remaining_use,
         land_area_frac, surface_runoff, loclake_frac, locwet_frac,
         glowet_frac, glolake_frac, glolake_area, reglake_frac, headwater,
         loclake_storage, locwet_storage, glolake_storage, glowet_storage,
         precipitation, openwater_pot_evap, river_storage, river_length,
         river_bottom_width, roughness, river_slope, outflow_cell,
         gw_dis_coeff, swb_drainage_area_factor, swb_outflow_coeff,
         gw_recharge_constant, reduction_exponent_lakewet, areal_corr_factor,
         lake_out_exp, activelake_depth, wetland_out_exp, activewetland_depth,
         stat_corr_fact):

    # =========================================================================
    #            Creating outputs for storages and fluxes
    # =========================================================================
    #                  =================================
    #                  ||           Groundwater       ||
    #                  =================================
    # Groundwater storage, Unit : km3
    gw_storage = np.zeros(groundwater_storage.shape)
    # Groundwater discharge, Unit : km3/day
    gw_discharge = np.zeros(groundwater_storage.shape)

    #                  =================================
    #                  ||           Local lake        ||
    #                  =================================
    # Local lake storage, Unit : km3
    local_lake_storage = np.zeros(groundwater_storage.shape)
    # Local lake outflow, Unit : km3/day
    loclake_outflow = np.zeros(groundwater_storage.shape)
    # Local lake groundwater recharge, Unit : km3/day
    gwr_loclake = np.zeros(groundwater_storage.shape)
    # Dynamic local lake fraction, Unit : (-)
    dyn_loclake_frac = np.zeros(groundwater_storage.shape)

    #                  =================================
    #                  ||        Local wetland        ||
    #                  =================================
    # Local wetland storage, Unit : km3
    local_wetland_storage = np.zeros(groundwater_storage.shape)
    # Local wetland outflow, Unit : km3/day
    locwet_outflow = np.zeros(groundwater_storage.shape)
    # Local wetland groundwater recharge, Unit : km3/day
    gwr_locwet = np.zeros(groundwater_storage.shape)
    # Dynamic local wetland fraction, Unit : (-)
    dyn_locwet_frac = np.zeros(groundwater_storage.shape)

    #                  =================================
    #                  ||           Global lake       ||
    #                  =================================
    # Global lake storage, Unit : km3
    global_lake_storage = np.zeros(groundwater_storage.shape)
    # Global lake outflow, Unit : km3/day
    glolake_outflow = np.zeros(groundwater_storage.shape)
    # Global lake groundwater recharge, Unit : km3/day
    gwr_glolake = np.zeros(groundwater_storage.shape)

    #                  =================================
    #                  ||        Global wetland       ||
    #                  =================================
    # Global wetland storage, Unit : km3
    global_wetland_storage = np.zeros(groundwater_storage.shape)
    # Global wetland outflow, Unit : km3/day
    glowet_outflow = np.zeros(groundwater_storage.shape)
    # Global wetland groundwater recharge, Unit : km3/day
    gwr_glowet = np.zeros(groundwater_storage.shape)
    # Dynamic global wetland fraction, Unit : (-)
    dyn_glowet_frac = np.zeros(groundwater_storage.shape)

    #                  =================================
    #                  ||           River             ||
    #                  =================================
    # River storage, Unit : km3
    river_storage_out = np.zeros(groundwater_storage.shape)
    # River streamflow, Unit : km3/day
    river_streamflow = np.zeros(groundwater_storage.shape)
    # River inflow, Unit : km3/day
    river_inflow = np.zeros(groundwater_storage.shape)
    # Cell runoff, Unit : km3/day
    cellrunoff = np.zeros(groundwater_storage.shape)

    # =========================================================================
    # Routing is calulated according to the routing order for individual cells
    # =========================================================================
    for i in range(len(rout_order)):
        # Get invidividual cells based on routing order
        x, y = rout_order[i]

        # Continent properties
        arid_cell = arid[x, y]
        drainage_direction_cell = drainage_direction[x, y]
        grid_cell_area = cell_area[x, y]
        land_area_frac_cell = land_area_frac[x, y]
        loclake_frac_cell = loclake_frac[x, y]
        locwet_frac_cell = locwet_frac[x, y]
        glowet_frac_cell = glowet_frac[x, y]
        glolake_frac_cell = glolake_frac[x, y]
        glolake_area_cell = glolake_area[x, y]
        reglake_frac_cell = reglake_frac[x, y]
        headwater_cell = headwater[x, y]

        # Water use
        netabs_gw_cell = netabs_gw[x, y]
        remaining_use_cell = remaining_use[x, y]

        # Input storages and fluxes
        groundwater_storage_cell = groundwater_storage[x, y]
        diffuse_gw_recharge_cell = diffuse_gw_recharge[x, y]
        surface_runoff_cell = surface_runoff[x, y]
        loclake_storage_cell = loclake_storage[x, y]
        locwet_storage_cell = locwet_storage[x, y]
        glolake_storage_cell = glolake_storage[x, y]
        glowet_storage_cell = glowet_storage[x, y]
        precipitation_cell = precipitation[x, y]
        openwater_pot_evap_cell = openwater_pot_evap[x, y]

        # River storage input and properties
        river_storage_cell = river_storage[x, y]
        river_length_cell = river_length[x, y]
        river_bottom_width_cell = river_bottom_width[x, y]
        roughness_cell = roughness[x, y]
        river_slope_cell = river_slope[x, y]

    #                  =================================
    #                  ||   Groundwater  balance      ||
    #                  =================================
    # =========================================================================
    # 1. Compute groundwater balance  for humid cells
    # =========================================================================
    # Groundwater storage is computed 1st for humid region (arid == 0)
    # Note!!!: WaterGAP assumes no groundwater discharge from arid
    # regions into surface waterbodies(local and global lakes and
    #  wetlands) except rivers. See section 4.5 of Müller Schmied et al. (2021)

    # Outputs from the  daily_groundwaterstorage_humid are
    # 0 = groundwater_storage(km3),  1 = groundwater_discharge(km3/day)

        if (arid_cell == 0) & (drainage_direction_cell >= 0):
            daily_groundwaterstorage_humid = \
                gws.compute_groundwater_storage("humid",
                                                groundwater_storage_cell,
                                                diffuse_gw_recharge_cell,
                                                grid_cell_area,
                                                netabs_gw_cell,
                                                remaining_use_cell,
                                                land_area_frac_cell,
                                                gw_dis_coeff[x, y])

            storage, discharge = daily_groundwaterstorage_humid

            gw_storage[x, y] = storage.item()
            gw_discharge[x, y] = discharge.item()

    # =========================================================================
    # 2. Compute groundwater storage for inland sink
    # =========================================================================
        if drainage_direction_cell < 0:
            daily_groundwaterstorage_landsink = \
                gws.compute_groundwater_storage("inland sink",
                                                groundwater_storage_cell,
                                                diffuse_gw_recharge_cell,
                                                grid_cell_area,
                                                netabs_gw_cell,
                                                remaining_use_cell,
                                                land_area_frac_cell,
                                                gw_dis_coeff[x, y])

            storage_sink, discharge_sink = daily_groundwaterstorage_landsink
            gw_storage[x, y] = storage_sink.item()
            gw_discharge[x, y] = discharge_sink.item()

    #                  =================================
    #                  ||   Fractional routing        ||
    #                  =================================
    # =========================================================================
    # Fractions of surface runoff and groundwater discharge(only humid cells)
    # are made to flow into surface water bodies to avoid that all runoff
    # generated in the grid cell is added to local lake or wetland.
    # The remaining discharge flows into a river.
    # See section 4 of Müller Schmied et al. (2021)
    # =========================================================================
    # Outputs from the  routed_flow are
    # 0 = inflow to surface waterbodies(km3/day),  1 = river inflow(km3/day)

        routed_flow = fr.frac_routing(surface_runoff_cell,
                                      gw_discharge[x, y],
                                      loclake_frac_cell, locwet_frac_cell,
                                      glowet_frac_cell, glolake_frac_cell,
                                      reglake_frac_cell, headwater_cell,
                                      drainage_direction_cell,
                                      swb_drainage_area_factor[x, y])

        inflow_to_swb, inflow_to_river = routed_flow

    #                  =================================
    #                  || Local lake  waterbalance    ||
    #                  =================================
    # =========================================================================
    # Local lake water balance including storages and fluxes are computed for
    # each cell. See section 4.6 of Müller Schmied et al. (2021)
    # =========================================================================
    # Outputs from the daily_loclake_storage are
    # 0 = local lake storage(km3),  1 = local lake outflow(km3/day),
    # 2 = groundwater recharge from local lake(km3/day)

        if loclake_frac_cell > 0:
            daily_loclake_storage = lw.\
                 lake_wetland_balance("local lake",
                                      loclake_storage_cell,
                                      loclake_frac_cell,
                                      precipitation_cell,
                                      openwater_pot_evap_cell,
                                      arid_cell,
                                      drainage_direction_cell,
                                      inflow_to_swb,
                                      swb_outflow_coeff[x, y],
                                      gw_recharge_constant[x, y],
                                      reduction_exponent_lakewet[x, y],
                                      areal_corr_factor[x, y],
                                      lake_outflow_exp=lake_out_exp[x, y],
                                      lake_depth=activelake_depth[x, y],
                                      area_of_cell=grid_cell_area)

            storage, outflow, recharge, frac = daily_loclake_storage
            local_lake_storage[x, y] = storage.item()
            loclake_outflow[x, y] = outflow.item()
            gwr_loclake[x, y] = recharge.item()
            dyn_loclake_frac[x, y] = frac.item()

            # update inflow to surface water bodies
            inflow_to_swb = outflow

    #                  =================================
    #                  || Local wetland waterbalance ||
    #                  =================================
    # =========================================================================
    # Local wetland water balance including storages and fluxes are computed
    # for each cell. See section 4.6 of Müller Schmied et al. (2021)
    # =========================================================================
    # Outputs from the daily_loclake_storage are
    # 0 = local wetland storage(km3),  1 =  local wetland outflow(km3/day),
    # 2 = groundwater recharge from local wetland(km3/day)

        # outflow of local lake becomes inflow to local wetland
        locwet_inflow = inflow_to_swb
        if locwet_frac_cell > 0:
            daily_locwet_storage = lw.\
                lake_wetland_balance('local wetland',
                                     locwet_storage_cell,
                                     locwet_frac_cell,
                                     precipitation_cell,
                                     openwater_pot_evap_cell,
                                     arid_cell,
                                     drainage_direction_cell,
                                     locwet_inflow,
                                     swb_outflow_coeff[x, y],
                                     gw_recharge_constant[x, y],
                                     reduction_exponent_lakewet[x, y],
                                     areal_corr_factor[x, y],
                                     wetland_outflow_exp=wetland_out_exp[x, y],
                                     wetland_depth=activewetland_depth[x, y],
                                     area_of_cell=grid_cell_area)

            storage, outflow, recharge, frac = daily_locwet_storage
            local_wetland_storage[x, y] = storage.item()
            locwet_outflow[x, y] = outflow.item()
            gwr_locwet[x, y] = recharge.item()
            dyn_locwet_frac[x, y] = frac.item()

            # update inflow to surface water bodies
            inflow_to_swb = outflow

    #                  =================================
    #                  || Global lake waterbalance    ||
    #                  =================================
    # =========================================================================
    # Global lake water balance including storages and fluxes are computed
    # for each cell. See section 4.6 of Müller Schmied et al. (2021)
    # =========================================================================
    # Outputs from the daily_glolake_storage are
    # 0 = global lake storage(km3),  1 = global lake outflow(km3/day),
    # 2 = groundwater recharge from global lake(km3/day)

        # Inflow from upstream river and outflow from local lakes becomes.
        # inflow into global lake.

        inflow_from_upstream = river_inflow[x, y]
        inflow_to_swb += river_inflow[x, y]

        if glolake_area_cell > 0:
            daily_glolake_storage = lw.\
                lake_wetland_balance('global lake',
                                     glolake_storage_cell,
                                     glolake_area_cell,
                                     precipitation_cell,
                                     openwater_pot_evap_cell,
                                     arid_cell,
                                     drainage_direction_cell,
                                     inflow_to_swb,
                                     swb_outflow_coeff[x, y],
                                     gw_recharge_constant[x, y],
                                     reduction_exponent_lakewet[x, y],
                                     areal_corr_factor[x, y],
                                     lake_outflow_exp=lake_out_exp[x, y],
                                     lake_depth=activelake_depth[x, y])

            # frac contains only 0's since global lake fraction is not updated
            storage, outflow, recharge, frac = daily_glolake_storage
            global_lake_storage[x, y] = storage.item()
            glolake_outflow[x, y] = outflow.item()
            gwr_glolake[x, y] = recharge.item()


            # update inflow to surface water bodies
            inflow_to_swb = outflow

    #                  =================================
    #                  || Global wetland waterbalance ||
    #                  =================================
    # =========================================================================
    # Global wetland water balance including storages and fluxes are computed
    # for each cell. See section 4.6 of Müller Schmied et al. (2021)
    # =========================================================================
    # Outputs from the  lake_wetland_balance are
    # 0 = global wetland storage(km3), 1 = global wetland outflow(km3/day),
    # 2 = groundwater recharge from global wetland(km3/day)

        # outflow of global lake becomes inflow to global wetland
        glowet_inflow = inflow_to_swb
        if glowet_frac_cell > 0:
            daily_glowet_storage = lw.\
                lake_wetland_balance('global wetland',
                                     glowet_storage_cell,
                                     glowet_frac_cell,
                                     precipitation_cell,
                                     openwater_pot_evap_cell,
                                     arid_cell,
                                     drainage_direction_cell,
                                     glowet_inflow,
                                     swb_outflow_coeff[x, y],
                                     gw_recharge_constant[x, y],
                                     reduction_exponent_lakewet[x, y],
                                     areal_corr_factor[x, y],
                                     wetland_outflow_exp=wetland_out_exp[x, y],
                                     wetland_depth=activewetland_depth[x, y],
                                     area_of_cell=grid_cell_area)

            storage, outflow, recharge, frac = daily_glowet_storage
            global_wetland_storage[x, y] = storage.item()
            glowet_outflow[x, y] = outflow.item()
            gwr_glowet[x, y] = recharge.item()
            dyn_glowet_frac[x, y] = frac.item()

            # update inflow to surface water bodies
            inflow_to_swb = outflow

    #                  =================================
    #                  ||   Groundwater  balance      ||
    #                  =================================
    # =========================================================================
    # 1. Compute groundwater balance  for (semi)arid cells
    # =========================================================================
    # Groundwater storage is now computed for  arid region (self.arid == 1)
    # since point source recharge from surface water bodies are computed.

        point_source_recharge = gwr_loclake[x, y] + gwr_locwet[x, y] + \
            gwr_glolake[x, y] + gwr_glowet[x, y]

        if (arid_cell == 1) & (drainage_direction_cell >= 0):

            daily_groundwater_storage_arid = \
               gws.compute_groundwater_storage("arid",
                                               groundwater_storage_cell,
                                               diffuse_gw_recharge_cell,
                                               grid_cell_area,
                                               netabs_gw_cell,
                                               remaining_use_cell,
                                               land_area_frac_cell,
                                               gw_dis_coeff[x, y],
                                               point_source_recharge)

            storage, discharge_arid = daily_groundwater_storage_arid

            gw_storage[x, y] = storage.item()
            gw_discharge[x, y] = discharge_arid.item()
            # In semi-arid/arid areas, groundwater reaches the river directly
            inflow_to_river += discharge_arid.item()

    #                  =================================
    #                  ||        River  balance      ||
    #                  =================================
    # =====================================================================
    # River water balance including storages and fluxes are computed
    # for each cell. See section 4.7 of Müller Schmied et al. (2021)
    # =====================================================================
        # outflow from global wetlands, the remaining flows from surface
        # runoff and all (semi)arid groundwater discharge are river inflows

        river_inflow[x, y] = inflow_to_swb

        if drainage_direction_cell >= 0:
            river_inflow[x, y] += (inflow_to_river)

        # ==========================
        # 1. Compute river velocity
        # ==========================
        # Output of "velocity_and_outflowconst" are
        # 0 = velocity (km/day),  1 =  outflow contstant (1/day)

        velocity_and_outflowconst = \
            rb.river_velocity(river_storage_cell, river_length_cell,
                              river_bottom_width_cell, roughness_cell,
                              river_slope_cell)

        velocity, outflow_constant = velocity_and_outflowconst

        # ================================================
        # 2. Compute storage(km3) and streamflow(km3/day)
        # ================================================
        daily_river_storage = rb.river_water_balance(river_storage_cell,
                                                     river_inflow[x, y],
                                                     outflow_constant,
                                                     stat_corr_fact[x, y])

        storage, streamflow = daily_river_storage
        river_storage_out[x, y] = storage.item()
        river_streamflow[x, y] = streamflow.item()

        # =================================
        # 3. Put water into downstream cell
        # ==================================
        # Get respective outflow cell for routing ordered cells.
        m, n = outflow_cell[i]
        # Do not rout flow if respective outflowcell has no latitude (m=0)
        # and longitude(n=0)[cell is an inland sink or flows to the ocean]
        if m > 0 and n > 0:
            river_inflow[m, n] += river_streamflow[x, y]

        # =================================
        # 4. compute cellrunoff(km3/day)
        # ==================================
        # Cell runoff is the part of the cell precipitation that has neither
        # been evapotranspirated nor stored. It is the net runoff production of
        # each grid cell (outflow of a grid cell minus inflow to the grid cell)
        # See equtaion 35 of Müller Schmied et al. (2021)
        if (drainage_direction_cell < 0):
            cellrunoff[x, y] = (-1 * inflow_from_upstream)
            # For inland sinks the  outflow is evaporated since no water
            # flows out of inland sinks.
            evaporated_streamflow_inlandsink = river_streamflow[x, y]
        else:
            cellrunoff[x,  y] = river_streamflow[x, y] - inflow_from_upstream

        # if x==184 and y==251:
        #     print(dyn_loclake_frac[x, y])

    return gw_storage, local_lake_storage, local_wetland_storage,\
        global_lake_storage,  global_wetland_storage, river_storage_out,\
        river_streamflow, cellrunoff, dyn_loclake_frac, dyn_locwet_frac, \
        dyn_glowet_frac
