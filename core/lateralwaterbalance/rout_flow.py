# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Routing."""

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
from core.lateralwaterbalance import lakes_and_wetlands as lw
from core.lateralwaterbalance import fractional_routing as fr
from core.lateralwaterbalance import river_waterbalance as rb
from core.lateralwaterbalance import reservior_and_regulated_lakes as res_reg
from core.lateralwaterbalance import distribute_to_riparian as to_riparian
from core.lateralwaterbalance import neighbouringcell as nbcell
from core.lateralwaterbalance import net_abstraction_from_local_lake as \
    netsabs_lake


@njit(cache=True)
def rout(rout_order, arid, drainage_direction,  groundwater_storage,
         diffuse_gw_recharge, cell_area, potential_net_abstraction_gw,
         prev_potential_water_withdrawal_sw_irri,
         prev_potential_consumptive_use_sw_irri, frac_irri_returnflow_to_gw,
         accumulated_unsatisfied_potential_netabs_sw, daily_unsatisfied_pot_nas,
         land_area_frac,
         surface_runoff, loclake_frac, locwet_frac, glowet_frac, glolake_frac,
         glolake_area, reglake_frac, headwater, loclake_storage,
         locwet_storage, glolake_storage, glowet_storage, glores_storage,
         glores_capacity, glores_area,
         glores_type, mean_annual_demand_res, mean_annaul_inflow_res,
         allocation_coeff, k_release, glores_startmonth, precipitation,
         openwater_pot_evap, river_storage, river_length, river_bottom_width,
         roughness, roughness_multiplier, river_slope, outflow_cell, gw_dis_coeff,
         swb_drainage_area_factor, swb_outflow_coeff, gw_recharge_constant,
         reduction_exponent_lakewet, reduction_exponent_res, areal_corr_factor,
         lake_out_exp, activelake_depth, wetland_out_exp, activewetland_depth,
         stat_corr_fact, current_mon_day,
         monthly_potential_net_abstraction_sw,
         glwdunits, unagregrgated_potential_netabs_sw,
         potential_net_abstraction_sw,
         prev_accumulated_unsatisfied_potential_netabs_sw,
         unsatisfied_potential_netabs_riparian, subtract_use,
         neigbourcells):

    # =========================================================================
    #   Creating outputs for storages, fluxes and factors(eg. reduction factor)
    # =========================================================================
    #                  =================================
    #                  ||           Groundwater       ||
    #                  =================================
    # Groundwater storage, Unit : km3
    groundwater_storage_out = np.zeros(groundwater_storage.shape)
    # Groundwater discharge, Unit : km3/day
    groundwater_discharge = np.zeros(groundwater_storage.shape)

    #                  =================================
    #                  ||           Local lake        ||
    #                  =================================
    # Local lake storage, Unit : km3
    loclake_storage_out = np.zeros(groundwater_storage.shape)
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
    locwet_storage_out = np.zeros(groundwater_storage.shape)
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
    glolake_storage_out = np.zeros(groundwater_storage.shape)
    # Global lake outflow, Unit : km3/day
    glolake_outflow = np.zeros(groundwater_storage.shape)
    # Global lake groundwater recharge, Unit : km3/day
    gwr_glolake = np.zeros(groundwater_storage.shape)

    #                  ==============================================
    #                  ||   Global reservior and regulated lake    ||
    #                  ==============================================
    # Global reservior and regulated lake  storage, Unit : km3
    global_reservior_storage = np.zeros(groundwater_storage.shape)
    # Global reservior and regulated lake  outflow, Unit : km3/day
    glores_outflow = np.zeros(groundwater_storage.shape)
    # Global reservior and regulated lake  groundwater recharge, Unit : km3/day
    gwr_glores = np.zeros(groundwater_storage.shape)
    # Reservoir reselease coefficient. Unit: (-)
    k_release_out = np.zeros(groundwater_storage.shape)

    #                  =================================
    #                  ||        Global wetland       ||
    #                  =================================
    # Global wetland storage, Unit : km3
    glowet_storage_out = np.zeros(groundwater_storage.shape)
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

    #                  =================================
    #                  ||           WaterUSe         ||
    #                  =================================
    actual_net_abstraction_gw = np.zeros(groundwater_storage.shape)

    # =========================================================================
    # Routing is calulated according to the routing order for individual cells
    # =========================================================================
    for routflow_looper in range(len(rout_order)):
        # Get invidividual cells based on routing order
        x, y = rout_order[routflow_looper]

        # Get respective outflow cell for routing ordered cells.
        m, n = outflow_cell[routflow_looper]

        # Get neigbouring cells for demand cell
        neigbourcells_for_demandcell = neigbourcells[routflow_looper]

        # update  accumulated_unsatisfied_potential_netabs_sw  with
        # unsatisfied_potential_netabs_riparian.
        # Note: In riparaian cell water supply option, the unsatisfied demand
        # from a global lake outflow cell is attempted to be satisfied in
        # riparian cells (local lakes or rivers) either on the same day or the
        # next day depending on the routing order.

        if glwdunits[x, y] > 0 and subtract_use == True:
            accumulated_unsatisfied_potential_netabs_sw[x, y] += \
                unsatisfied_potential_netabs_riparian[x, y]
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

        if (arid[x, y] == 0) & (drainage_direction[x, y] >= 0):
            daily_groundwaterbalance_humid = \
                gws.compute_groundwater_balance(rout_order, routflow_looper,
                                                "humid",
                                                groundwater_storage[x, y],
                                                diffuse_gw_recharge[x, y],
                                                potential_net_abstraction_gw[x, y],
                                                daily_unsatisfied_pot_nas[x, y],
                                                gw_dis_coeff[x, y],
                                                prev_potential_water_withdrawal_sw_irri[x, y],
                                                prev_potential_consumptive_use_sw_irri[x, y],
                                                frac_irri_returnflow_to_gw[x, y])

            storage, discharge, actual_netabs_gw =\
                daily_groundwaterbalance_humid

            groundwater_storage_out[x, y] = storage.item()
            groundwater_discharge[x, y] = discharge.item()
            actual_net_abstraction_gw[x, y] = actual_netabs_gw.item()

        # if x==87 and y==224:
        #     print(groundwater_discharge[x, y], surface_runoff[x, y])
    # =========================================================================
    # 2. Compute groundwater storage for inland sink
    # =========================================================================

        if drainage_direction[x, y] < 0:
            daily_groundwaterbalance_landsink = \
                gws.compute_groundwater_balance(rout_order, routflow_looper,
                                                "inland sink",
                                                groundwater_storage[x, y],
                                                diffuse_gw_recharge[x, y],
                                                potential_net_abstraction_gw[x, y],
                                                daily_unsatisfied_pot_nas[x, y],
                                                gw_dis_coeff[x, y],
                                                prev_potential_water_withdrawal_sw_irri[x, y],
                                                prev_potential_consumptive_use_sw_irri[x, y],
                                                frac_irri_returnflow_to_gw[x, y])

            storage_sink, discharge_sink, actual_netabs_gw =\
                daily_groundwaterbalance_landsink

            groundwater_storage_out[x, y] = storage_sink.item()
            groundwater_discharge[x, y] = discharge_sink.item()
            actual_net_abstraction_gw[x, y] = actual_netabs_gw.item()

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

        routed_flow = fr.frac_routing(rout_order, routflow_looper,
                                      surface_runoff[x, y],
                                      groundwater_discharge[x, y],
                                      loclake_frac[x, y], locwet_frac[x, y],
                                      glowet_frac[x, y], glolake_frac[x, y],
                                      reglake_frac[x, y], headwater[x, y],
                                      drainage_direction[x, y],
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

        if loclake_frac[x, y] > 0:
            daily_loclake_balance = lw.\
                 lake_wetland_balance(rout_order, routflow_looper,
                                      "local lake",
                                      loclake_storage[x, y],
                                      loclake_frac[x, y],
                                      precipitation[x, y],
                                      openwater_pot_evap[x, y],
                                      arid[x, y],
                                      drainage_direction[x, y],
                                      inflow_to_swb,
                                      swb_outflow_coeff[x, y],
                                      gw_recharge_constant[x, y],
                                      reduction_exponent_lakewet[x, y],
                                      areal_corr_factor[x, y],
                                      lake_outflow_exp=lake_out_exp[x, y],
                                      lake_depth=activelake_depth[x, y],
                                      area_of_cell=cell_area[x, y])

            storage, outflow, recharge, frac, accum_unpot_netabs_sw =\
                daily_loclake_balance

            loclake_storage_out[x, y] = storage.item()
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
        if locwet_frac[x, y] > 0:
            daily_locwet_balance = lw.\
                lake_wetland_balance(rout_order, routflow_looper,
                                     'local wetland',
                                     locwet_storage[x, y],
                                     locwet_frac[x, y],
                                     precipitation[x, y],
                                     openwater_pot_evap[x, y],
                                     arid[x, y],
                                     drainage_direction[x, y],
                                     locwet_inflow,
                                     swb_outflow_coeff[x, y],
                                     gw_recharge_constant[x, y],
                                     reduction_exponent_lakewet[x, y],
                                     areal_corr_factor[x, y],
                                     wetland_outflow_exp=wetland_out_exp[x, y],
                                     wetland_depth=activewetland_depth[x, y],
                                     area_of_cell=cell_area[x, y])

            storage, outflow, recharge, frac, accum_unpot_netabs_sw = \
                daily_locwet_balance

            locwet_storage_out[x, y] = storage.item()
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

        if glolake_area[x, y] > 0:
            daily_glolake_balance = lw.\
                lake_wetland_balance(rout_order, routflow_looper,
                                     'global lake',
                                     glolake_storage[x, y],
                                     glolake_area[x, y],
                                     precipitation[x, y],
                                     openwater_pot_evap[x, y],
                                     arid[x, y],
                                     drainage_direction[x, y],
                                     inflow_to_swb,
                                     swb_outflow_coeff[x, y],
                                     gw_recharge_constant[x, y],
                                     reduction_exponent_lakewet[x, y],
                                     areal_corr_factor[x, y],
                                     lake_outflow_exp=lake_out_exp[x, y],
                                     lake_depth=activelake_depth[x, y],
                                     reservoir_area=glores_area[x, y],
                                     accumulated_unsatisfied_potential_netabs_sw=accumulated_unsatisfied_potential_netabs_sw[x, y])

            # frac contains only 0's since global lake fraction is not updated
            storage, outflow, recharge, frac, accum_unpot_netabs_sw =\
                daily_glolake_balance

            glolake_storage_out[x, y] = storage.item()
            glolake_outflow[x, y] = outflow.item()
            gwr_glolake[x, y] = recharge.item()
            accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                accum_unpot_netabs_sw.item()
            # update inflow to surface water bodies
            inflow_to_swb = outflow

    #                  ==================================================
    #                  || Reserviour and regulated lake waterbalance   ||
    #                  ==================================================
    # =========================================================================
    # Reserviors and regulated lakes water fluxes are computed
    # for each cell. See section 4.6.1 of Müller Schmied et al. (2021)
    # =========================================================================
        if glores_area[x, y] > 0:

            daily_res_reg_balance = res_reg.\
                reservior_and_regulated_lake(rout_order, routflow_looper,
                                             outflow_cell,
                                             glores_storage[x, y],
                                             glores_capacity[x, y],
                                             precipitation[x, y],
                                             openwater_pot_evap[x, y],
                                             arid[x, y],
                                             drainage_direction[x, y],
                                             inflow_to_swb,
                                             swb_outflow_coeff[x, y],
                                             gw_recharge_constant[x, y],
                                             glores_area,
                                             reduction_exponent_res[x, y],
                                             areal_corr_factor[x, y],
                                             glores_startmonth[x, y],
                                             current_mon_day,
                                             k_release[x, y],
                                             glores_type[x, y],
                                             allocation_coeff,
                                             monthly_potential_net_abstraction_sw,
                                             mean_annual_demand_res,
                                             mean_annaul_inflow_res[x, y])

            storage, outflow, recharge, res_k_release = daily_res_reg_balance

            global_reservior_storage[x, y] = storage.item()
            glores_outflow[x, y] = outflow.item()
            gwr_glores[x, y] = recharge.item()
            k_release_out[x, y] = res_k_release.item()
            # update inflow to surface water bodies
            inflow_to_swb = outflow

    #    -----------------------------------------------------------------
    #    || Resdistribute unsatisfied net abstraction to riparian cell  ||
    #    ||               for global lakes and reservoirs               ||
    #    -----------------------------------------------------------------
        if subtract_use == True:
            if (glores_area[x, y] > 0) | (glolake_area[x, y] > 0):

                distributed_potnetabs = to_riparian.\
                    redistritute_to_riparian(prev_accumulated_unsatisfied_potential_netabs_sw[x, y],
                                             accumulated_unsatisfied_potential_netabs_sw[x, y],
                                             unagregrgated_potential_netabs_sw,
                                             potential_net_abstraction_sw[x, y],
                                             glwdunits, rout_order,
                                             unsatisfied_potential_netabs_riparian,
                                             x, y)

                accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                    distributed_potnetabs[0]

                unsatisfied_potential_netabs_riparian = \
                    distributed_potnetabs[1]

    # =========================================================================
    # Global lake water balance including storages and fluxes are computed
    # for each cell. See section 4.6 of Müller Schmied et al. (2021)
    # =========================================================================

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
        if glowet_frac[x, y] > 0:
            daily_glowet_balance = lw.\
                lake_wetland_balance(rout_order, routflow_looper,
                                     'global wetland',
                                     glowet_storage[x, y],
                                     glowet_frac[x, y],
                                     precipitation[x, y],
                                     openwater_pot_evap[x, y],
                                     arid[x, y],
                                     drainage_direction[x, y],
                                     glowet_inflow,
                                     swb_outflow_coeff[x, y],
                                     gw_recharge_constant[x, y],
                                     reduction_exponent_lakewet[x, y],
                                     areal_corr_factor[x, y],
                                     wetland_outflow_exp=wetland_out_exp[x, y],
                                     wetland_depth=activewetland_depth[x, y],
                                     area_of_cell=cell_area[x, y])

            # frac contains only 0's since global lake fraction is not updated
            storage, outflow, recharge, frac, accum_unpot_netabs_sw = \
                daily_glowet_balance

            glowet_storage_out[x, y] = storage.item()
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

        if (arid[x, y] == 1) & (drainage_direction[x, y] >= 0):
            daily_groundwater_balance_arid = \
               gws.compute_groundwater_balance(rout_order, routflow_looper,
                                               "arid",
                                               groundwater_storage[x, y],
                                               diffuse_gw_recharge[x, y],
                                               potential_net_abstraction_gw[x, y],
                                               daily_unsatisfied_pot_nas[x, y],
                                               gw_dis_coeff[x, y],
                                               prev_potential_water_withdrawal_sw_irri[x, y],
                                               prev_potential_consumptive_use_sw_irri[x, y],
                                               frac_irri_returnflow_to_gw[x, y],
                                               point_source_recharge)

            storage, discharge_arid, actual_netabs_gw = \
                daily_groundwater_balance_arid

            groundwater_storage_out[x, y] = storage.item()
            groundwater_discharge[x, y] = discharge_arid.item()
            actual_net_abstraction_gw[x, y] = actual_netabs_gw.item()
            # In semi-arid/arid areas, groundwater reaches the river directly
            inflow_to_river += discharge_arid.item()

    #                  =================================
    #                  ||        River  balance      ||
    #                  =================================
    # =====================================================================
    # River water balance including storages and fluxes are computed
    # for each cell. See section 4.7 of Müller Schmied et al. (2021)
    # =====================================================================
        # Outflow from global wetlands, the remaining flows from surface
        # runoff and all (semi)arid groundwater discharge are river inflows

        river_inflow[x, y] = inflow_to_swb

        if drainage_direction[x, y] >= 0:
            river_inflow[x, y] += (inflow_to_river)

        # ==========================
        # 1. Compute river velocity
        # ==========================
        # Output of "velocity_and_outflowconst" are
        # 0 = velocity (km/day),  1 =  outflow contstant (1/day)

        velocity_and_outflowconst = \
            rb.river_velocity(rout_order, routflow_looper,
                              river_storage[x, y], river_length[x, y],
                              river_bottom_width[x, y], roughness[x, y],
                              roughness_multiplier[x, y], river_slope[x, y])

        velocity, outflow_constant = velocity_and_outflowconst

        # ================================================
        # 2. Compute storage(km3) and streamflow(km3/day)
        # ================================================
        daily_river_balance = rb.river_water_balance(rout_order,
                                                     routflow_looper,
                                                     river_storage[x, y],
                                                     river_inflow[x, y],
                                                     outflow_constant,
                                                     stat_corr_fact[x, y],
                                                     accumulated_unsatisfied_potential_netabs_sw[x, y])

        storage, streamflow, accum_unpot_netabs_sw = daily_river_balance
        river_storage_out[x, y] = storage.item()
        river_streamflow[x, y] = streamflow.item()
        accumulated_unsatisfied_potential_netabs_sw[x, y] = \
            accum_unpot_netabs_sw.item()

        # =================================
        # 3. Put water into downstream cell
        # ==================================
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
        if (drainage_direction[x, y] < 0):
            cellrunoff[x, y] = (-1 * inflow_from_upstream)
            # For inland sinks the  river_streamflow  is evaporated since no
            #  water flows out of inland sinks. Hence cellrunoff gets negative
            evaporated_streamflow_inlandsink = river_streamflow[x, y]
        else:
            cellrunoff[x,  y] = river_streamflow[x, y] - inflow_from_upstream

        #    =================================================
        #    ||  Neighbouring cell Water supply option  &   ||
        #    ||  Abstraction from  local lake               ||
        #    ==================================================

        if subtract_use == True :
            # compute loclake_maxstorage and glolake_maxstorage required for
            # neighbouring cell water supply option and abstraction from local
            # lake*(will refactor to be  have it  calulated once for all grid)*
            m_to_km = 0.001
            if (loclake_frac[x, y] > 0):

                loclake_maxstorage = cell_area[x, y] * loclake_frac[x, y] * \
                    activelake_depth[x, y] * m_to_km
            else:
                loclake_maxstorage = 0

            if (glolake_area[x, y] > 0):
                glolake_maxstorage = \
                    glolake_area[x, y]*activelake_depth[x, y] * m_to_km
            else:
                glolake_maxstorage = 0
            #               ====================================
            #               ||  Abstraction from  local lake  ||
            #               ====================================
            #    --------------------------------------------------------------
            #    || Water can be abstracted from local lake storage if       ||
            #    || 1) there is a lake in the cell, 2)there is accumulated   ||
            #    || unsatisfied use  after river abstraction, and 3)         ||
            #    || lake storage is above negative max_storage.              ||
            #    ||                                                          ||
            #    -----------------------------------------------------------------
            if (loclake_frac[x, y] > 0) and \
                    (accumulated_unsatisfied_potential_netabs_sw[x, y] > 0):

                if (loclake_storage_out[x, y] > (-1 * loclake_maxstorage)):

                    storage, accum_unpot_netabs_sw, frac,  = netsabs_lake.\
                        abstract_from_local_lake(loclake_storage_out[x, y],
                                                 loclake_maxstorage,
                                                 loclake_frac[x, y],
                                                 reduction_exponent_lakewet[x, y],
                                                 accumulated_unsatisfied_potential_netabs_sw[x, y])

                    loclake_storage_out[x, y] = storage.item()
                    accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                        accum_unpot_netabs_sw.item()
                    dyn_loclake_frac[x, y] = frac.item()

            #               =============================================
            #               ||  Neighbouring cell Water supply option  ||
            #               =============================================
            #    --------------------------------------------------------------
            #    ||       ||
            #    ||    ||
            #    ||          ||
            #    ||           ||
            #    ||                                                          ||
            #    --------------------------------------------------------------
            # nbcell_lat_lon = nbcell.\
            #     neighbouring_cell(neigbourcells_for_demandcell,
            #                       river_storage_out, loclake_storage_out,
            #                       glolake_storage_out, loclake_maxstorage,
            #                       glolake_maxstorage, rout_order,
            #                       outflow_cell, x, y)
            # if x==12 and y == 284:
            #     print(x, y, nbcell_lat_lon)

    return groundwater_storage_out, loclake_storage_out, locwet_storage_out,\
        glolake_storage_out, global_reservior_storage, k_release_out, \
        glowet_storage_out, river_storage_out, groundwater_discharge, \
        loclake_outflow, locwet_outflow, glolake_outflow, glowet_outflow, \
        river_streamflow,  cellrunoff, dyn_loclake_frac, dyn_locwet_frac, \
        dyn_glowet_frac, accumulated_unsatisfied_potential_netabs_sw, \
        unsatisfied_potential_netabs_riparian, actual_net_abstraction_gw
