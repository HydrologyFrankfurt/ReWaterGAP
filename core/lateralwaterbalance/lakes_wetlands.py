# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Lakes and wetland storages and fluxes."""

# =============================================================================
# This module computes water balance for global and local lakes and wetlands,
# including storage and related fluxes for all grid cells based on section 4.6
#  of (Müller Schmied et al. (2021)).
# =============================================================================

import numpy as np
from numba import njit
from core.lateralwaterbalance import storage_reduction_factor as rf


@njit(cache=True)
def lake_wetland_balance(x, y,
                         choose_swb, storage, precipitation,
                         openwater_pot_evap, aridity, drainage_direction,
                         inflow_to_swb, swb_outflow_coeff,
                         groundwater_recharge_constant,
                         reduction_exponent_lakewet, areal_corr_factor,
                         max_storage=None, max_area=None, lakewet_frac=0,
                         lake_outflow_exp=None, wetland_outflow_exp=None,
                         reservoir_area=0,
                         accumulated_unsatisfied_potential_netabs_sw=0):
    """
    Compute water balance for global and local lakes and wetlands including
    storage and related fluxes.

    Parameters
    ----------
     x : int
         Latitude index of cell
     y : int
         Longitude index of cell
    choose_swb : string
        Select surface waterbody (global and local lakes and wetlands)
    storage : float
        Daily surface waterbody storage, Unit: [km3]
    lakewet_frac : float
        Fraction of surface waterbody, Unit: [-]
    precipitation : float
        Daily precipitation, Unit: [km/day]
    openwater_pot_evap : float
        Daily open water potential evaporation, Unit: [km/day]
    aridity : int
        Integer which differentiates arid(aridity=1) from
        humid(aridity=0) regions taken from  [1]_ , Units: [-]
    drainage_direction : int
        Drainage direction taken from  [1]_ , Units: [-]
    inflow_to_swb : float
        Inflow into selected surface waterbody, Unit: [km3/day]
    swb_outflow_coeff: float
        Surface water outflow coefficient (=0.01) Eqn 27 [1]_, Unit: [1/day]
    groundwater_recharge_constant: float
        Groundwater recharge constant below lakes, reserviors & wetlands (=0.01)
        Eqn 26 [1]_, Unit: [m/day]
    reduction_exponent_lakewet: float
        Reduction exponent (= 3.32193) taken from Eqn 24 and 25 [1]_ , Units: [-].
    areal_corr_factor: float
        Areal correction factor
    max_storage: float
        Maximum storage of surface waterbody storage, Unit: [km3]
    max_area: float,
        Maximum area of surface waterbody, Unit: km2.
        Note!!! Global lake area has absolute lake area (including that of
        riparian cells) in the outflow cell. Hence, the outflow cell is used for
        waterbalance calulation.
    lake_outflow_exp: float
        Lake outflow exponent(=1.5) taken from Eqn 27 [1]_, Units: [-].
    wetland_outflow_exp: float
        Wetland outflow exponent(=2.5) taken from Eqn 27 [1]_, Units: [-].
    reservoir_area: float
        Reservoir Area (required to split water demand 50%  between reservoir
        and global lake), Unit: [km2]
    accumulated_unsatisfied_potential_netabs_sw:
        Accumulated unsatified potential net abstraction from surafce water,
        Unit: [km^3/day]

    References.

    .. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                The global water resources and use model WaterGAP v2.2d:
                model description and evaluation. Geoscientific Model
                Development, 14(2), 1037–1079.
                https://doi.org/10.5194/gmd-14-1037-2021


    Returns
    -------
    storage :  float
        Updated daily surface waterbody storage, Unit: [km3]
    outflow :  float
        Daily surface waterbody outflow, Unit: [km3/day]
    gwr_lakewet :  float
        Daily groundwater recharge from surface water body outflow
        (arid region only), Unit: [km3/day]
    lake_wet_newfraction: float
        Updated local lake area fraction(to adapt landarea fraction), Unit:[-].
    accumulated_unsatisfied_potential_netabs_glolake: float
        Accumulated unsatified potential net abstraction after global lake
        satisfaction, Unit: [km^3/day]
    actual_use_sw: float
        Actual net abstraction from lakes and wetlands, Unit: [km^3/day]
    """
    # Index (x,y) to  print out varibales of interest
    # e.g.  if x==65 and y==137: print(prev_gw_storage)

    # =========================================================================
    #     Parameters for respective surface waterbody.
    # =========================================================================
    if choose_swb == "local lake" or choose_swb == "global lake":
        exp_factor = lake_outflow_exp
    else:
        exp_factor = wetland_outflow_exp

    # =========================================================================

    #                  ======================================
    #                  ||  lake and wetland waterbalance    ||
    #                  ======================================
    # Note components of the waterbalance in Equation 22 of Müller Schmied et
    # al. (2021)) is calulated as follows.

    storage_prevstep = storage

    # =========================================================================
    # Computing Reduction factor (km2/day) for
    # local and global lakes and wetlands. Equation 24 & 25 in
    # (Müller Schmied et al. (2021).
    # =========================================================================
    redfactor = \
        rf.swb_redfactor(storage_prevstep, max_storage,
                         reduction_exponent_lakewet, choose_swb)

    # For global lake, reduction factor is only used for reducing evaporation
    # and not area since global lake area is assumed not to be dynamic.
    # This would prevent continuous decline of global lake levels in some cases
    # i.e. ((semi)arid regions)
    if choose_swb == "global lake":
        evapo_redfactor = redfactor
        lake_wet_area = max_area
    else:
        # Dynamic area of swb except global lake
        # Eqn 23 in Müller Schmied et al. (2021).
        lake_wet_area = redfactor * max_area

    # =========================================================================
    # Computing lake or wetland corrected evaporation
    # (openwater_evapo_cor[km3/day])
    # =========================================================================
    # /////////////////////////////////////////////////////////////////////////
    # Areal correction factor (CFA) approach for correcting
    # open water evaporation.

    # Water balance of surface waterbodies (lakes,wetlands and reservoir)
    # except rivers is given as: See Eqn. 22 in Müller Schmied et al. (2021).
    # dS/dt = A(P - PET) + Qin - NAs - gwr_swb - Qout

    # (P - PET) is considered (crudely) as the runoff from the respective SWB.
    # Therefore, CFA is applied as a correction factor on  only (P - PET)
    # and only P and PET are taken into account to compute corrected PET.

    # Approach to compute PET_corrected:
    # equation 1) P - PET = Runoff

    # equation 2) P - PET_corr = Runoff * CFA
    # 		      Runoff = (P - PET_corr)/CFA
    #
    # 	equation 2) in equation 1):
    # 	P - PET = (P - PET_corr)/CFA
    # 	(P - PET) * CFA = P - PET_corr
    #
    # 	CFA*P - CFA * PET = P - PET_corr
    # 	PET_corr = P - CFA*P + CFA * PET
    #
    #   Final equation for corrected PET
    #   PET_corr = (1 - CFA) * P + CFA * PET
    #
    # /////////////////////////////////////////////////////////////////////////

    if choose_swb == "global lake":
        # Reducing potential evaporation for global lake using reduction factor
        openwater_pet = openwater_pot_evap * evapo_redfactor
    else:  # local lakes and global and local wetlands
        openwater_pet = openwater_pot_evap

    openwater_evapo_cor = (1 - areal_corr_factor) * precipitation + \
        (areal_corr_factor * openwater_pet)

    openwater_evapo_cor = np.where(openwater_evapo_cor < 0, 0,
                                   openwater_evapo_cor)  # km/day

    # =========================================================================
    # Calculating lake or wetland  groundwater recharge[gwr_lakewet (km3/day)]
    # See Eqn. 26 in Müller Schmied et al. (2021).
    # =========================================================================
    # Point_source_recharge is only computed for (semi)arid surafce water
    # bodies but not for  inlank sink or humid regions
    # convert m to km
    m_to_km = 0.001
    if choose_swb == "global lake":
        # Since global lake area is assumed not be dynamic, recharge needs to
        # be reduced else more water will recharge the ground
        gwr_lakewet = np.where((aridity == 1) & (drainage_direction >= 0),
                               groundwater_recharge_constant * m_to_km *
                               lake_wet_area * evapo_redfactor, 0)

    else:  # local lakes and global and local wetlands
        gwr_lakewet = np.where((aridity == 1) & (drainage_direction >= 0),
                               groundwater_recharge_constant * m_to_km *
                               lake_wet_area, 0)

    # =========================================================================
    # Combine inflow and open water precipitation total_inflow (km3/day)
    # =========================================================================
    total_inflow = inflow_to_swb + precipitation * lake_wet_area

    # =========================================================================
    # Combine openwater PET, potential net abstraction from surface water
    # and point source recharge into petgwr_netabs_sw(km3/day).
    # =========================================================================
    # Incase of global lake, If reservoirs are found in the same outflow cell.
    # The potential net abstraction is shared equally(50%) between.

    if choose_swb == "global lake":
        if reservoir_area > 0:
            accumulated_unsatisfied_potential_netabs_glolake = \
                accumulated_unsatisfied_potential_netabs_sw * 0.5
        else:
            accumulated_unsatisfied_potential_netabs_glolake = \
                accumulated_unsatisfied_potential_netabs_sw
    else:
        accumulated_unsatisfied_potential_netabs_glolake = 0

    # Needed To compute daily actual use
    acc_unsatisfied_potnetabs_glolake_start = \
        accumulated_unsatisfied_potential_netabs_glolake

    # Note abstraction from local lake is done after that of river.
    # For global and local wetlands there are no absractions
    # See abstraction priority diagram Fig.2 in Müller Schmied et al. (2021).
    petgwr_netabs_sw = openwater_evapo_cor * lake_wet_area + gwr_lakewet + \
        accumulated_unsatisfied_potential_netabs_glolake

    # Computing  petgwr_netabs_sw_max.
    # This is the maximum amount of petgwr_netabs_sw to ensure
    # that lake (wetland) storage does not fall below  -max_storage (0):.
    # Note!! lake (wetland) storage goes from -max_storage (0) to max_storage

    if choose_swb == "local lake" or choose_swb == "global lake":
        petgwr_netabs_sw_max = storage_prevstep + max_storage + total_inflow
    else:  # local and global wetlands
        petgwr_netabs_sw_max = storage_prevstep + total_inflow

    # =========================================================================
    #    Computing current storage for surface waterbody
    # =========================================================================
    # Note waterbalance equation 22 in Müller Schmied et al. (2021) is solved
    # analytically for global lake and wetland  but numerically for local lake
    # and wetlands

    if choose_swb == 'global lake' or choose_swb == 'global wetland':
        # Global lake and wetland balance:
        # dS/dt = total_inflow - petgwr - NAl - k*S is solved analytically for
        # each time step of 1 day
        net_in = total_inflow - petgwr_netabs_sw

        storage = \
            (storage_prevstep * np.exp(-1 * swb_outflow_coeff)) + \
            (net_in/swb_outflow_coeff) * (1-np.exp(-1 * swb_outflow_coeff))

    else:
        # local lakes and wetland are solved numerically
        storage = storage_prevstep + total_inflow - petgwr_netabs_sw

    # =========================================================================
    # Computing outflow and updating storages
    # =========================================================================
    # Limit lake (wetland) storage to -max_storage (0) when petgwr_netabs_sw >
    # petgwr_netabs_sw_max. During -max_storage(0) the lake (wetland) area is
    # reduced by 100% (no lake or wetland available). see Eqn 23 and 24 in
    # Müller Schmied et al. (2021). Reduce point source recharge, potential
    # net abstraction from surface water and open water evaporation as well
    # when petgwr_netabs_sw > petgwr_netabs_sw_max.

    if choose_swb == "local lake" or choose_swb == "global lake":
        storage_limit = -1 * max_storage
    else:
        storage_limit = 0

    if choose_swb == 'global lake':
        if petgwr_netabs_sw > petgwr_netabs_sw_max:
            outflow = 0
            storage = storage_limit

            gwr_lakewet *= (petgwr_netabs_sw_max/petgwr_netabs_sw)

            openwater_evapo_cor *= (petgwr_netabs_sw_max/petgwr_netabs_sw)

            # Reduce potential water use from global lake after partial
            # satisfaction.
            if accumulated_unsatisfied_potential_netabs_glolake > 0:
                accumulated_unsatisfied_potential_netabs_glolake -= \
                    accumulated_unsatisfied_potential_netabs_glolake * \
                    (petgwr_netabs_sw_max/petgwr_netabs_sw)
            else:
                accumulated_unsatisfied_potential_netabs_glolake = 0
        else:
            outflow = net_in + storage_prevstep - storage

            if storage > max_storage:
                outflow += (storage - max_storage)
                storage = max_storage

            # Recalculate global lake and wetland storage when lake outflow = 0
            # dS/dt = total_inflow - petgwr - NAl
            # (without k*S) -> S(t) = S(t-1) + netgw_in
            if outflow < 0:  # update outflow
                outflow = 0
                storage = net_in + storage_prevstep

            accumulated_unsatisfied_potential_netabs_glolake = 0

    elif choose_swb == 'global wetland':
        if petgwr_netabs_sw > petgwr_netabs_sw_max:
            outflow = 0
            storage = storage_limit
            gwr_lakewet *= (petgwr_netabs_sw_max/petgwr_netabs_sw)
            openwater_evapo_cor *= (petgwr_netabs_sw_max/petgwr_netabs_sw)
        else:
            outflow = net_in + storage_prevstep - storage

        if storage > max_storage:
            outflow += (storage - max_storage)
            storage = max_storage

    else:  # local lake and wetland

        if petgwr_netabs_sw > petgwr_netabs_sw_max:
            storage = storage_limit
            gwr_lakewet *= (petgwr_netabs_sw_max/petgwr_netabs_sw)
            openwater_evapo_cor *= (petgwr_netabs_sw_max/petgwr_netabs_sw)

        # choose storage type to calculate outflow (current or previous)
        # but all should be previous.
        if choose_swb == 'local lake':  # previous storage
            which_storge = storage_prevstep
        else:
            which_storge = storage  # current storage

        # Note: local lakes storage can become negative even if previous
        # storage is positive(e.g. high evaporation) hence exponential
        # expression for outflow is computed for positive storages only.
        # This means that for negatve storages, outflow is set to zero.
        # See Eqn 27 in Müller Schmied et al. (2021)
        if which_storge > 0:
            outflow = swb_outflow_coeff * which_storge * \
                (which_storge/max_storage)**exp_factor

            if storage <= 0:
                outflow = 0
            else:
                if outflow > storage:
                    outflow = storage

        else:
            outflow = 0

        storage -= outflow

        # update outflow
        if storage > max_storage:
            outflow += (storage - max_storage)
            # updating storage
            storage = max_storage

    new_redfactor = \
        rf.swb_redfactor(storage, max_storage,
                         reduction_exponent_lakewet, choose_swb)

    # Computing new  local lake and global and local wetland area fractions for
    # next day. see eqn. 23 in Müller Schmied et al. (2021)

    if choose_swb == 'global lake':
        lake_wet_newfraction = 0
    else:
        lake_wet_newfraction = new_redfactor * lakewet_frac

    # Daily actual net use
    actual_use_sw = acc_unsatisfied_potnetabs_glolake_start - \
        accumulated_unsatisfied_potential_netabs_glolake
    
    # convert open water evaporation for swb from km/day to km3/day (output purpose)
    openwater_evapo_cor_km3 = openwater_evapo_cor * lake_wet_area
    
    return storage, outflow, gwr_lakewet, lake_wet_newfraction,\
        accumulated_unsatisfied_potential_netabs_glolake, \
        actual_use_sw, openwater_evapo_cor_km3
