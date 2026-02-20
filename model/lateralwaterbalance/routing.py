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
from model.lateralwaterbalance import groundwater as gw
from model.lateralwaterbalance import lakes_wetlands as lw
from model.lateralwaterbalance import routing_to_surface_water_bodies as rt_surf
from model.lateralwaterbalance import river
from model.lateralwaterbalance import reservoir_regulated_lakes as res_reg
from model.lateralwaterbalance import distribute_net_abstraction as dist_netabstr
from model.lateralwaterbalance import neighbouring_cell as nbcell
from model.lateralwaterbalance import local_lake_net_abstraction as lake_netabstr


@njit(cache=True)
def river_routing(rout_order, outflow_cell, drainage_direction, aridhumid,
                  precipitation, openwater_pot_evap, surface_runoff,
                  diffuse_gw_recharge, groundwater_storage, loclake_storage,
                  locwet_storage, glolake_storage, glores_storage, glowet_storage,
                  river_storage, max_loclake_storage, max_locwet_storage,
                  max_glolake_storage, max_glowet_storage, glores_capacity,
                  max_loclake_area, max_locwet_area, glolake_area, glores_area,
                  max_glowet_area, loclake_frac, locwet_frac, glowet_frac, glolake_frac,
                  reglake_frac, headwatercell, gw_dis_coeff, swb_drainage_area_factor,
                  swb_outflow_coeff, gw_recharge_constant, reduction_exponent_lakewet,
                  reduction_exponent_res, lake_out_exp, wetland_out_exp,
                  areal_corr_factor, stat_corr_fact,
                  river_length, river_bottom_width, roughness, roughness_multiplier,
                  river_slope, glwdunits, glores_startmonth, current_mon_day, k_release,
                  glores_type, allocation_coeff, mean_annual_demand_res,
                  mean_annual_inflow_res, potential_net_abstraction_gw,
                  potential_net_abstraction_sw,  unagregrgated_potential_netabs_sw,
                  accumulated_unsatisfied_potential_netabs_sw,
                  prev_accumulated_unsatisfied_potential_netabs_sw,
                  daily_unsatisfied_pot_nas, monthly_potential_net_abstraction_sw,
                  prev_potential_water_withdrawal_sw_irri,
                  prev_potential_consumptive_use_sw_irri, frac_irri_returnflow_to_gw,
                  unsatisfied_potential_netabs_riparian, neigbourcells,
                  neighbourcells_outflowcell, unsat_potnetabs_sw_from_demandcell,
                  unsat_potnetabs_sw_to_supplycell, neighbouring_cells_map,
                  subtract_use_option, neighbouringcell_option, reservoir_operation,
                  num_days_in_month, all_reservoir_and_regulated_lake_area,
                  reg_lake_redfactor_firstday, basin, delayed_use_option,
                  landwaterfrac_excl_glolake_res, cell_area, land_aet_corr,
                  sum_canopy_snow_soil_storage):

    """Route flow to river. """

    # Volume at which storage is set to zero, units: [km3]
    minstorage_volume = 1e-15
    # =========================================================================
    #   Creating outputs for storages, fluxes and factors(eg. reduction factor)
    # =========================================================================
    cell_calculated = np.zeros(groundwater_storage.shape)

    # consistent precipitation, Unit : km3/day
    consistent_precip = basin.copy()
    # total water_ storage, Unit : km3/day
    total_water_storage = basin.copy()

    #                  =================================
    #                  ||           Groundwater       ||
    #                  =================================
    # Groundwater storage, Unit : km3
    groundwater_storage_out = basin.copy() + groundwater_storage.copy()
    # Groundwater discharge, Unit : km3/day
    groundwater_discharge = basin.copy()
    # Groundwater recharge from surface waterbodies, Unit : km3/day
    point_source_recharge = basin.copy()

    #                  =================================
    #                  ||           Local lake        ||
    #                  =================================
    # Local lake storage, Unit : km3
    loclake_storage_out = basin.copy() + loclake_storage.copy()
    # Local lake outflow, Unit : km3/day
    loclake_outflow = basin.copy()
    # Local lake groundwater recharge, Unit : km3/day
    gwr_loclake = basin.copy()
    # Dynamic local lake fraction, Unit : (-)
    dyn_loclake_frac = basin.copy()
    # Extent local lake, Unit : km2
    loclake_extent = basin.copy()

    #                  =================================
    #                  ||        Local wetland        ||
    #                  =================================
    # Local wetland storage, Unit : km3
    locwet_storage_out = basin.copy() + locwet_storage.copy()
    # Local wetland outflow, Unit : km3/day
    locwet_outflow = basin.copy()
    # Local wetland groundwater recharge, Unit : km3/day
    gwr_locwet = basin.copy()
    # Dynamic local wetland fraction, Unit : (-)
    dyn_locwet_frac = basin.copy()
    # Extent local wetland, Unit : km2
    locwet_extent = basin.copy()

    #                  =================================
    #                  ||           Global lake       ||
    #                  =================================
    # Global lake storage, Unit : km3
    glolake_storage_out = basin.copy() + glolake_storage.copy()
    # Global lake outflow, Unit : km3/day
    glolake_outflow = basin.copy()
    # Global lake groundwater recharge, Unit : km3/day
    gwr_glolake = basin.copy()

    # Global lake precipitation, Unit : km3/day
    # (to compute consistent precipitation)
    glolake_precip = basin.copy()

    #                  ==============================================
    #                  ||   Global reservior and regulated lake    ||
    #                  ==============================================
    # Global reservior and regulated lake  storage, Unit : km3
    glores_storage_out = basin.copy() + glores_storage.copy()
    # Global reservior and regulated lake  outflow, Unit : km3/day
    glores_outflow = basin.copy()
    glores_inflow  = basin.copy()
    # Global reservior and regulated lake  groundwater recharge, Unit : km3/day
    gwr_glores = basin.copy()
    # Reservoir reselease coefficient. Unit: (-)
    k_release_out = k_release.copy() + basin.copy()

    # Global reservior and regulated lake precipitation, Unit : km3/day
    # (to compute consistent precipitation)
    glores_precip = basin.copy()
    

    #                  =================================
    #                  ||        Global wetland       ||
    #                  =================================
    # Global wetland storage, Unit : km3
    glowet_storage_out = basin.copy() + glowet_storage.copy()
    # Global wetland outflow, Unit : km3/day
    glowet_outflow = basin.copy()
    # Global wetland groundwater recharge, Unit : km3/day
    gwr_glowet = basin.copy()
    # Dynamic global wetland fraction, Unit : (-)
    dyn_glowet_frac = basin.copy()
    # Extent global wetland, Unit : km2
    glowet_extent = basin.copy()
    
    #                  =================================
    #                  ||           River             ||
    #                  =================================
    # River storage, Unit : km3
    river_storage_out = basin.copy() + river_storage.copy()
    # River streamflow, Unit : km3/day
    river_streamflow = basin.copy()
    # River inflow, Unit : km3/day
    river_inflow = basin.copy()
    # Cell runoff, Unit : km3/day
    cellrunoff = basin.copy()
    # Inflow from upstream cell, Unit : km3/day
    inflow_from_upstream = basin.copy()
    # River velocity, Unit : km/day
    river_velocity = basin.copy()

    #                  =================================
    #                  ||           WaterUSe         ||
    #                  =================================
    actual_net_abstraction_gw = basin.copy()
    actual_daily_netabstraction_sw = basin.copy()

    # ++ All evaporation stuff are here (we add them to water use anyways) ++

    cell_aet_consuse = basin.copy()  # Unit : km3/day
    # Total actual evaporation from land (open water, canopy, snow and soil
    # evaporation)
    daily_total_aet = basin.copy()  # Unit : km3/day
    total_open_water_aet = basin.copy()  # Unit : km3/day

    loclake_evapo = basin.copy()  # Unit : km3/day
    locwet_evapo = basin.copy()  # Unit : km3/day
    glolake_evapo = basin.copy()  # Unit : km3/day
    glores_evapo = basin.copy()  # Unit : km3/day
    glowet_evapo = basin.copy()  # Unit : km3/da

    #                  =================================
    #                  ||          Neigbouring cell    ||
    #                  =================================
    total_demand_sw_noallocation = basin.copy()
    total_unsatisfied_demand_ripariancell = basin.copy()

    returned_demand_from_supplycell = basin.copy() * np.nan

    returned_demand_from_supplycell_nextday = basin.copy() * np.nan

    # =========================================================================
    # Routing is calulated according to the routing order for individual cells
    # =========================================================================
    for routflow_looper in range(len(rout_order)):
        # Get invidividual cells based on routing order
        x, y = rout_order[routflow_looper]

        if np.isnan(basin[x, y]) is False:
            # Get respective outflow cell for routing ordered cells.
            m, n = outflow_cell[routflow_looper]

            # Get neigbouring cells (for demand cell)and respective outflow cells
            neigbourcells_for_demandcell = neigbourcells[routflow_looper]
            outflowcell_for_neigbourcells = \
                neighbourcells_outflowcell[routflow_looper]

            # update  accumulated_unsatisfied_potential_netabs_sw  with
            # unsatisfied_potential_netabs_riparian.
            # Note: In riparaian cell water supply option, the unsatisfied demand
            # from a global lake outflow cell is attempted to be satisfied in
            # riparian cells (local lakes or rivers) either on the same day or the
            # next day depending on the routing order.

            if glwdunits[x, y] > 0 and subtract_use_option:
                accumulated_unsatisfied_potential_netabs_sw[x, y] += \
                    unsatisfied_potential_netabs_riparian[x, y]


            if subtract_use_option and neighbouringcell_option:

                if returned_demand_from_supplycell[x, y] >= 0:
                    # Here routing order of demand cell > supply cell.
                    # accumulated_unsatisfied_potential_netabs_sw  and
                    # daily_unsatisfied_pot_nas are adapated accordingly for demand
                    # cell. For detailed explanation see waterbalance_lateral.py
                    # module (Update accumulated unsatisfied potential net
                    # abstraction from surface water and daily_unsatisfied_pot_nas)
                    if delayed_use_option:
                        accumulated_unsatisfied_potential_netabs_sw[x, y] += \
                            returned_demand_from_supplycell[x, y]

                    daily_unsatisfied_pot_nas[x, y] = \
                        returned_demand_from_supplycell[x, y] - \
                        prev_accumulated_unsatisfied_potential_netabs_sw[x, y]

                    returned_demand_from_supplycell_nextday[x, y] = \
                        returned_demand_from_supplycell[x, y]
                    returned_demand_from_supplycell[x, y] = np.nan


                # Total demand without demand allocation (include previous
                # accumulated unsatified potential net abstraction from surface
                # water, Unsatisfied demand from riparian cell and current daily
                # potential net abstraction from surface water). only required for
                #  neigbouring cell water supply option
                total_demand_sw_noallocation[x, y] = \
                    accumulated_unsatisfied_potential_netabs_sw[x, y]

                # upate accumulated_unsatisfied_potential_netabs_sw with water
                # allocated from demand cell to supply cell
                accumulated_unsatisfied_potential_netabs_sw[x, y] += \
                    unsat_potnetabs_sw_to_supplycell[x, y]

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

            if (aridhumid[x, y] == 0) & (drainage_direction[x, y] >= 0):
                daily_groundwaterbalance_humid = \
                    gw.groundwater_balance(x, y,
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
        # =========================================================================
        # 2. Compute groundwater storage for inland sink
        # =========================================================================
            if drainage_direction[x, y] < 0:
                daily_groundwaterbalance_landsink = \
                    gw.groundwater_balance(x, y,
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
            routed_flow = rt_surf.frac_routing(x, y,
                                               surface_runoff[x, y],
                                               groundwater_discharge[x, y],
                                               loclake_frac[x, y], locwet_frac[x, y],
                                               glowet_frac[x, y], glolake_frac[x, y],
                                               reglake_frac[x, y], headwatercell[x, y],
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

            if loclake_frac[x, y] > 0:
                daily_loclake_balance = lw.\
                     lake_wetland_water_balance(x, y,
                                                "local lake",
                                                loclake_storage[x, y],
                                                precipitation[x, y],
                                                openwater_pot_evap[x, y],
                                                aridhumid[x, y],
                                                drainage_direction[x, y],
                                                inflow_to_swb,
                                                swb_outflow_coeff[x, y],
                                                gw_recharge_constant[x, y],
                                                reduction_exponent_lakewet[x, y],
                                                areal_corr_factor[x, y],
                                                max_storage=max_loclake_storage[x, y],
                                                max_area=max_loclake_area[x, y],
                                                lakewet_frac=loclake_frac[x, y],
                                                lake_outflow_exp=lake_out_exp[x, y])

                storage, outflow, recharge, frac, accum_unpot_netabs_sw, \
                    actual_use, openwater_evapo_cor, extent = daily_loclake_balance

                loclake_storage_out[x, y] = storage.item()
                loclake_outflow[x, y] = outflow.item()
                gwr_loclake[x, y] = recharge.item()
                dyn_loclake_frac[x, y] = frac.item()
                loclake_evapo[x, y] = openwater_evapo_cor.item()
                loclake_extent[x, y] = extent.item()

                # update inflow to surface water bodies
                inflow_to_swb = outflow

        #                  =================================
        #                  || Local wetland waterbalance ||
        #                  =================================
        # =========================================================================
        # Local wetland water balance including storages and fluxes are computed
        # for each cell. See section 4.6 of Müller Schmied et al. (2021)
        # =========================================================================
            # outflow of local lake becomes inflow to local wetland
            locwet_inflow = inflow_to_swb

            if locwet_frac[x, y] > 0:
                daily_locwet_balance = lw.\
                    lake_wetland_water_balance(x, y,
                                               'local wetland',
                                               locwet_storage[x, y],
                                               precipitation[x, y],
                                               openwater_pot_evap[x, y],
                                               aridhumid[x, y],
                                               drainage_direction[x, y],
                                               locwet_inflow,
                                               swb_outflow_coeff[x, y],
                                               gw_recharge_constant[x, y],
                                               reduction_exponent_lakewet[x, y],
                                               areal_corr_factor[x, y],
                                               max_storage=max_locwet_storage[x, y],
                                               wetland_outflow_exp=wetland_out_exp[x, y],
                                               max_area=max_locwet_area[x, y],
                                               lakewet_frac=locwet_frac[x, y],)

                storage, outflow, recharge, frac, accum_unpot_netabs_sw, \
                    actual_use, openwater_evapo_cor, extent = daily_locwet_balance

                locwet_storage_out[x, y] = storage.item()
                locwet_outflow[x, y] = outflow.item()
                gwr_locwet[x, y] = recharge.item()
                dyn_locwet_frac[x, y] = frac.item()
                locwet_evapo[x, y] = openwater_evapo_cor.item()
                locwet_extent[x, y] = extent.item()


                # update inflow to surface water bodies
                inflow_to_swb = outflow

        #                  =================================
        #                  || Global lake waterbalance    ||
        #                  =================================
        # =========================================================================
        # Global lake water balance including storages and fluxes are computed
        # for each cell. See section 4.6 of Müller Schmied et al. (2021)
        # =========================================================================
            # Inflow from upstream river and outflow from local lakes becomes.
            # inflow into global lake.
            inflow_from_upstream[x, y] = river_inflow[x, y]
            inflow_to_swb += river_inflow[x, y]

            if glolake_area[x, y] > 0:
                daily_glolake_balance = lw.\
                    lake_wetland_water_balance(x, y,
                            'global lake',
                            glolake_storage[x, y],
                            precipitation[x, y],
                            openwater_pot_evap[x, y],
                            aridhumid[x, y],
                            drainage_direction[x, y],
                            inflow_to_swb,
                            swb_outflow_coeff[x, y],
                            gw_recharge_constant[x, y],
                            reduction_exponent_lakewet[x, y],
                            areal_corr_factor[x, y],
                            max_storage=max_glolake_storage[x, y],
                            max_area=glolake_area[x, y],
                            lake_outflow_exp=lake_out_exp[x, y],
                            reservoir_area=glores_area[x, y],
                            accumulated_unsatisfied_potential_netabs_sw=
                            accumulated_unsatisfied_potential_netabs_sw[x, y])

                storage, outflow, recharge, frac, accum_unpot_netabs_sw, \
                    actual_use, openwater_evapo_cor, extent = daily_glolake_balance

                glolake_precip[x, y] = precipitation[x, y] * glolake_area[x, y]
                glolake_storage_out[x, y] = storage.item()
                glolake_outflow[x, y] = outflow.item()
                gwr_glolake[x, y] = recharge.item()
                actual_daily_netabstraction_sw[x, y] = actual_use.item()
                accu_unsatisfied_pot_netabstr_glolake = accum_unpot_netabs_sw.item()
                glolake_evapo[x, y] = openwater_evapo_cor.item()

                # update inflow to surface water bodies
                inflow_to_swb = outflow

        #                  ==================================================
        #                  || Reserviour and regulated lake waterbalance   ||
        #                  ==================================================
        # =========================================================================
        # Reserviors and regulated lakes water fluxes are computed
        # for each cell. See section 4.6.1 of Müller Schmied et al. (2021)
        # ** need to compute actual use from here too** (to be done**)
        # =========================================================================
            if glores_area[x, y] > 0:
                glores_inflow[x, y] =   inflow_to_swb

                daily_res_reg_balance = res_reg.\
                    reservoir_regulated_lake_water_balance(rout_order, routflow_looper,
                                        outflow_cell,
                                        glores_storage[x, y],
                                        glores_capacity[x, y],
                                        precipitation[x, y],
                                        openwater_pot_evap[x, y],
                                        aridhumid[x, y],
                                        drainage_direction[x, y],
                                        inflow_to_swb,
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
                                        mean_annual_inflow_res[x, y],
                                        glolake_area[x, y],
                                        accumulated_unsatisfied_potential_netabs_sw[x, y],
                                        accu_unsatisfied_pot_netabstr_glolake,
                                        num_days_in_month,
                                        all_reservoir_and_regulated_lake_area,
                                        reg_lake_redfactor_firstday[x, y],
                                        minstorage_volume)

                storage, outflow, recharge, res_k_release, accum_unpot_netabs_sw, \
                    actual_use, openwater_evapo_cor = daily_res_reg_balance

                glores_precip[x, y] = precipitation[x, y] * glores_area[x, y]
                glores_storage_out[x, y] = storage.item()
                glores_outflow[x, y] = outflow.item()
                gwr_glores[x, y] = recharge.item()
                k_release_out[x, y] = res_k_release.item()
                actual_daily_netabstraction_sw[x, y] += actual_use.item()
                accu_unsatisfied_pot_netabstr_glores = accum_unpot_netabs_sw.item()
                glores_evapo[x, y] = openwater_evapo_cor.item()

                # update inflow to surface water bodies
                inflow_to_swb = outflow


            # Update accumulated_unsatisfied_potential_netabs_sw  after global lake
            # and reservior abstraction since a cell may contain both.
            if glores_area[x, y] > 0:
                accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                    accu_unsatisfied_pot_netabstr_glores
            elif glolake_area[x, y] > 0:
                accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                    accu_unsatisfied_pot_netabstr_glolake

        #    -----------------------------------------------------------------
        #    || Resdistribute unsatisfied net abstraction to riparian cell  ||
        #    ||               for global lakes and reservoirs               ||
        #    -----------------------------------------------------------------
            if subtract_use_option:
                if (glores_area[x, y] > 0) | (glolake_area[x, y] > 0):

                    # demand_riparian_outflowcell: is the total unsatisfied demand
                    # of both outflow and riparian cells before distribution to
                    # riparian cell. This variable is  required to compute total unsatisfied demand
                    # of ripariancells which is needed for the neighbouring cell
                    # water supply algorithm
                    demand_riparian_outflowcell = \
                            accumulated_unsatisfied_potential_netabs_sw[x, y]

                    distributed_potnetabs = dist_netabstr.\
                        redistritute_to_riparian(
                            prev_accumulated_unsatisfied_potential_netabs_sw[x, y],
                            unsat_potnetabs_sw_to_supplycell[x, y],
                            accumulated_unsatisfied_potential_netabs_sw[x, y],
                            unagregrgated_potential_netabs_sw,
                            potential_net_abstraction_sw[x, y],
                            glwdunits, rout_order,
                            unsatisfied_potential_netabs_riparian,
                            returned_demand_from_supplycell_nextday[x, y],
                            x, y)

                    accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                        distributed_potnetabs[0]

                    # total unsatisfied demand of all riparian cells
                    total_unsatisfied_demand_ripariancell[x, y] = \
                        demand_riparian_outflowcell - \
                        accumulated_unsatisfied_potential_netabs_sw[x, y]
                    # unsatisfied potential net abstraction for each  riparian cell
                    unsatisfied_potential_netabs_riparian = \
                        distributed_potnetabs[1]

        #                  =================================
        #                  || Global wetland waterbalance ||
        #                  =================================
        # =========================================================================
        # Global wetland water balance including storages and fluxes are computed
        # for each cell. See section 4.6 of Müller Schmied et al. (2021)
        # =========================================================================
            # outflow of global lake becomes inflow to global wetland
            glowet_inflow = inflow_to_swb

            if glowet_frac[x, y] > 0:
                daily_glowet_balance = lw.\
                    lake_wetland_water_balance(x, y,
                                               'global wetland',
                                               glowet_storage[x, y],
                                               precipitation[x, y],
                                               openwater_pot_evap[x, y],
                                               aridhumid[x, y],
                                               drainage_direction[x, y],
                                               glowet_inflow,
                                               swb_outflow_coeff[x, y],
                                               gw_recharge_constant[x, y],
                                               reduction_exponent_lakewet[x, y],
                                               areal_corr_factor[x, y],
                                               max_storage=max_glowet_storage[x, y],
                                               wetland_outflow_exp=wetland_out_exp[x, y],
                                               max_area=max_glowet_area[x, y],
                                               lakewet_frac=glowet_frac[x, y])

                storage, outflow, recharge, frac, accum_unpot_netabs_sw, \
                    actual_use, openwater_evapo_cor, extent = daily_glowet_balance

                glowet_storage_out[x, y] = storage.item()
                glowet_outflow[x, y] = outflow.item()
                gwr_glowet[x, y] = recharge.item()
                dyn_glowet_frac[x, y] = frac.item()
                glowet_evapo[x, y] = openwater_evapo_cor.item()
                glowet_extent[x, y] = extent.item()


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

            point_source_recharge[x, y] = gwr_loclake[x, y] + gwr_locwet[x, y] + \
                gwr_glolake[x, y] + gwr_glowet[x, y] + gwr_glores[x, y]

            if (aridhumid[x, y] == 1) & (drainage_direction[x, y] >= 0):
                daily_groundwater_balance_arid = \
                   gw.groundwater_balance(x, y,
                                          "arid",
                                          groundwater_storage[x, y],
                                          diffuse_gw_recharge[x, y],
                                          potential_net_abstraction_gw[x, y],
                                          daily_unsatisfied_pot_nas[x, y],
                                          gw_dis_coeff[x, y],
                                          prev_potential_water_withdrawal_sw_irri[x, y],
                                          prev_potential_consumptive_use_sw_irri[x, y],
                                          frac_irri_returnflow_to_gw[x, y],
                                          point_source_recharge[x, y])

                storage, discharge_arid, actual_netabs_gw = \
                    daily_groundwater_balance_arid

                groundwater_storage_out[x, y] = storage.item()
                groundwater_discharge[x, y] = discharge_arid.item()
                actual_net_abstraction_gw[x, y] = actual_netabs_gw.item()

                # In semi-arid/arid areas, groundwater reaches the river directly
                inflow_to_river += groundwater_discharge[x, y]

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
                river.river_velocity(x, y,
                                     river_storage[x, y], river_length[x, y],
                                     river_bottom_width[x, y], roughness[x, y],
                                     roughness_multiplier[x, y], river_slope[x, y])

            velocity, outflow_constant = velocity_and_outflowconst
            river_velocity[x, y] = velocity
            # ================================================
            # 2. Compute storage(km3) and streamflow(km3/day)
            # ================================================
            # river_start_use= accumulated_unsatisfied_potential_netabs_sw[x, y]
            daily_river_balance = river.river_water_balance(x, y,
                                    river_storage[x, y],
                                    river_inflow[x, y],
                                    outflow_constant,
                                    stat_corr_fact[x, y],
                                    accumulated_unsatisfied_potential_netabs_sw[x, y],
                                    minstorage_volume)

            storage, streamflow, accum_unpot_netabs_sw, actual_use = \
                daily_river_balance

            river_storage_out[x, y] = storage.item()
            river_streamflow[x, y] = streamflow.item()
            accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                accum_unpot_netabs_sw.item()
            actual_daily_netabstraction_sw[x, y] += actual_use.item()

            # =================================
            # 3. Put water into downstream cell
            # ==================================
            # Do not rout flow if respective outflowcell has no latitude (m=0)
            # and longitude(n=0)[this cell is an inland sink or flows to the ocean]
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
                cellrunoff[x, y] = (-1 * inflow_from_upstream[x, y])
                # For inland sinks the  river_streamflow  is evaporated since no
                #  water flows out of inland sinks. Hence cellrunoff gets negative
                evaporated_streamflow_inlandsink = river_streamflow[x, y]
            else:
                evaporated_streamflow_inlandsink = 0
                cellrunoff[x,  y] = river_streamflow[x, y] - inflow_from_upstream[x, y]

            #    =================================================
            #    ||  Neighbouring cell Water supply option  &   ||
            #    ||  Abstraction from  local lake               ||
            #    ==================================================
            if subtract_use_option:
                #               ====================================
                #               ||  Abstraction from  local lake  ||
                #               ====================================
                #    ------------------------------------------------------------
                #    || Water can be abstracted from local lake storage if     ||
                #    || 1) there is a lake in the cell, 2)there is accumulated ||
                #    || unsatisfied use  after river abstraction, and 3)       ||
                #    || lake storage is above negative max_storage.            ||
                #    ||                                                        ||
                #    ------------------------------------------------------------

                if (loclake_frac[x, y] > 0) and \
                        (accumulated_unsatisfied_potential_netabs_sw[x, y] > 0):
                    if (loclake_storage_out[x, y] >
                            (-1 * max_loclake_storage[x, y])):

                        storage, accum_unpot_netabs_sw, frac, actual_use = lake_netabstr.\
                            abstract_from_local_lake(loclake_storage_out[x, y],
                                    max_loclake_storage[x, y],
                                    loclake_frac[x, y],
                                    reduction_exponent_lakewet[x, y],
                                    accumulated_unsatisfied_potential_netabs_sw[x, y],
                                    x, y)

                        loclake_storage_out[x, y] = storage.item()
                        accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                            accum_unpot_netabs_sw.item()
                        actual_daily_netabstraction_sw[x, y] += actual_use.item()

                        dyn_loclake_frac[x, y] = frac.item()

                #               =============================================
                #               ||  Neighbouring cell Water supply option  ||
                #               =============================================
                if neighbouringcell_option:
                    #         # +++++++++++++++++++++++++++++++++++++++++++++++++++
                    #         # Allocation of usatisfied demand  back to demandcell
                    #         # +++++++++++++++++++++++++++++++++++++++++++++++++++

                    (accum_unpot_netabs_sw, returned_demand_from_supplycell,
                     total_unsat_demand_supply_to_demand_cell) = nbcell.\
                        allocate_unsat_demand_to_demandcell(x, y,
                                neighbouring_cells_map,
                                accumulated_unsatisfied_potential_netabs_sw[x, y],
                                unsat_potnetabs_sw_from_demandcell,
                                unsat_potnetabs_sw_to_supplycell[x, y],
                                total_demand_sw_noallocation[x, y],
                                actual_daily_netabstraction_sw[x, y],
                                total_unsatisfied_demand_ripariancell[x, y],
                                rout_order,
                                returned_demand_from_supplycell,
                                current_mon_day)


                    # Unsatisfied use of supply cell to be allocated
                    accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                        accum_unpot_netabs_sw

                    # +++set to zero after allocation***
                    if unsat_potnetabs_sw_to_supplycell[x, y] > 0:
                        unsat_potnetabs_sw_to_supplycell[x, y] = 0

                    #      # +++++++++++++++++++++++++++++++++++
                    #      # Neighbouring cell identification &
                    #      # allocation of demand to supply cell
                    #      # +++++++++++++++++++++++++++++++++++

                    nbcell_lat, nbcell_lon = nbcell.\
                        get_neighbouringcell(neigbourcells_for_demandcell,
                                             outflowcell_for_neigbourcells,
                                             river_storage_out, loclake_storage_out,
                                             glolake_storage_out, max_loclake_storage,
                                             max_glolake_storage,
                                             accumulated_unsatisfied_potential_netabs_sw[x, y],
                                             reservoir_operation,
                                             glores_storage_out,
                                             x, y, current_mon_day,
                                             cell_calculated)

                    neighbouring_cells_map[x, y] = (nbcell_lat, nbcell_lon)

                    # Allocating unsatisfied demand to supply cell
                    if np.all(neighbouring_cells_map[x, y]) > 0:
                        unsat_potnetabs_sw_from_demandcell[x, y] = \
                            accumulated_unsatisfied_potential_netabs_sw[x, y]

                        # set demand to zero after allocating to neibouringcell
                        accumulated_unsatisfied_potential_netabs_sw[x, y] = 0

                        # Allocating unsatisfied demand to supply cell
                        # A cell may be identified as a "neibouringcell" for other
                        # cells in the  same timestep hence the '+=' instead of '='
                        unsat_potnetabs_sw_to_supplycell[nbcell_lat, nbcell_lon] += \
                            unsat_potnetabs_sw_from_demandcell[x, y]

                        if cell_calculated[nbcell_lat, nbcell_lon] > cell_calculated[x, y]:
                            daily_unsatisfied_pot_nas[x, y] = np.nan
                    else:
                        unsat_potnetabs_sw_from_demandcell[x, y] = 0

                # ***************************************
                cell_calculated[x, y] = 1
                # ***************************************

            #    =================================================
            #    ||             Additional Output                ||
            #    || for output and or water balance purpose only ||
            #    ==================================================
            # compute consistent precipitation (km3/day)
            consistent_precip[x, y] = \
                (landwaterfrac_excl_glolake_res[x, y] * precipitation[x, y] *
                 cell_area[x, y]) + glolake_precip[x, y] + glores_precip[x, y]

            # compute total actual evaporation from land (inlcuding open water
            # evaporation) km3/day
            total_open_water_aet[x, y] = \
                (loclake_evapo[x, y] + locwet_evapo[x, y] +
                 glolake_evapo[x, y] + glores_evapo[x, y] + glowet_evapo[x, y])

            if (drainage_direction[x, y] < 0):
                total_open_water_aet[x, y] += evaporated_streamflow_inlandsink

            daily_total_aet[x, y] = land_aet_corr[x, y] + total_open_water_aet[x, y]

            # cell_aet_consuse (km3/day) = actual consumptive use(NAg+NAs) +
            # total actual evaporation from land
            cell_aet_consuse[x, y] = actual_net_abstraction_gw[x, y] + \
                actual_daily_netabstraction_sw[x, y] + daily_total_aet[x, y]

            # total water_ storage (km3)
            total_water_storage[x, y] = groundwater_storage_out[x, y] + \
                loclake_storage_out[x, y] + locwet_storage_out[x, y] + \
                glolake_storage_out[x, y] + glores_storage_out[x, y] + \
                glowet_storage_out[x, y] + river_storage_out[x, y] + \
                sum_canopy_snow_soil_storage[x, y]

    return groundwater_storage_out, loclake_storage_out, locwet_storage_out,\
        glolake_storage_out, glores_storage_out, k_release_out, \
        glowet_storage_out, river_storage_out, groundwater_discharge, \
        loclake_outflow, locwet_outflow, glolake_outflow, glowet_outflow, \
        river_streamflow,  cellrunoff, dyn_loclake_frac, dyn_locwet_frac, \
        dyn_glowet_frac, accumulated_unsatisfied_potential_netabs_sw, \
        unsatisfied_potential_netabs_riparian, actual_net_abstraction_gw, \
        unsat_potnetabs_sw_from_demandcell, unsat_potnetabs_sw_to_supplycell,\
        returned_demand_from_supplycell, returned_demand_from_supplycell_nextday,\
        neighbouring_cells_map, daily_unsatisfied_pot_nas, glores_outflow, \
        actual_daily_netabstraction_sw, consistent_precip, inflow_from_upstream,\
        cell_aet_consuse, total_water_storage, point_source_recharge, river_velocity,\
            locwet_extent,glowet_extent,loclake_extent,glores_inflow\


