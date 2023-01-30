# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Local lakes and wetland storages."""

# =============================================================================
# This module computes water balance for global and local lakes and wetlands,
# including storage and related fluxes for all grid cells based on section 4.6
#  of (Müller Schmied et al. (2021)).
# =============================================================================

import numpy as np
from core.verticalwaterbalance import parameters as pm
from core.lateralwaterbalance import reduction_factor as rf


def lake_and_wetlands_balance(choose_swb, storage, lakewet_frac, precipitation,
                              openwater_pot_evap, aridity, drainage_direction,
                              inflow_to_swb, cell_area=None):
    """
    Compute water balance for global and local lakes and wetlands including
    storage and related fluxes.

    Parameters
    ----------
    choose_swb : string
        Select surface waterbody (global and local lakes and wetlands)
    storage : array
        Daily surface waterbody storage, Unit: km3
    lakewet_frac : array
        Fraction of surface waterbody, Unit: %
    precipitation : array
        Daily precipitation, Unit: km/day
    openwater_pot_evap : array
        Daily open water potential evaporation, Unit: km/day
    aridity : array
        Array which differentiates arid(aridity=1) from
        humid(aridity=0) regions taken from  [1]_ , Units: (-)
    drainage_direction : array
        Drainage direction taken from  [1]_ , Units: (-)
    inflow_to_swb : array
        Inflow into selected surface waterbody, Unit: km3/day
    cell_area : array, optional
        Area of grid cell, Unit: km2.
        Note!!! local lakes and global and local wetlands uses area fractions
       and hence cell area is required to compute respective absolute areas.
       Global lake area is already absolute so no cell_area is required.

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
    storage : TYPE
        Updated daily surface waterbody storage, Unit: km3
    outflow : TYPE
        Daily surface waterbody outflow, Unit: km3/day
    gwr_lakewet : TYPE
        Daily groundwater recharge from surface water body outflow
        (arid region only), Unit: km3/day

    """

    # =========================================================================
    #     Parameters for respective surface waterbody.
    # =========================================================================
    # Note!!!: Active depth is the same for both local and global
    # lakes.
    if choose_swb == 'local lake' or choose_swb == 'global lake':
        exp_factor = pm.lake_out_exp
        active_depth = pm.activelake_depth
    else:
        # Local and global wetland paramters (Active depth is the same as well)
        exp_factor = pm.wet_out_exp
        active_depth = pm.activewetland_depth

    # =========================================================================

    storage_prevstep = storage.copy()

    # =========================================================================
    # Computing reduction factor (km2/day) and maximum storage(km3/day) for
    # local and global lakes and wetlands. Equation 24 & 25 in
    # (Müller Schmied et al. (2021)) .
    # Outputs from lake_and_wetlands_redufactor function is reduction factor
    # =========================================================================
    # convert m to km
    m_to_km = 0.001

    # Note!!! Global lake area has absolute lake area in the outflow cell.
    # hence the outflow cell is used for waterbalance calulation
    # since global lake area is absolute, lakewet_frac = aboslute lake area
    # The rest (local lakes and global and local wetlands) uses area fractions

    if choose_swb == 'global lake':
        max_area = lakewet_frac
    else:  # local lakes and global and local wetlands
        max_area = cell_area * lakewet_frac

    max_storage = max_area * active_depth * m_to_km

    redfactor = \
        rf.loclake_and_wetlands_redufactor(storage_prevstep, max_storage,
                                           choose_swb)

    # For global lake, reduction factor is only used for reducting evaporation
    # and not area since global lake area is assumed not to be dynamic.
    # This would prevent continuous decline of global lake levels in some cases
    # i.e. ((semi)arid regions)
    if choose_swb == 'global lake':
        evapo_redfactor = redfactor
        lake_wet_area = max_area
    else:
        # Dynamic area of swb except global lake
        lake_wet_area = redfactor * max_area
    # =========================================================================
    # Computing lake or wetland corrected evaporation (openwater_evapo[km/day])
    # =========================================================================
    # /////////////////////////////////////////////////////////////////////////
    # CFA correction approach for open water evaporation

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

    if choose_swb == 'global lake':
        # Reducing potential evaporation for global lake using reduction factor
        openwater_pet = openwater_pot_evap * evapo_redfactor
    else:  # local lakes and global and local wetlands
        openwater_pet = openwater_pot_evap

    openwater_evapo = (1-pm.areal_corr_factor) * precipitation + \
        (pm.areal_corr_factor * openwater_pet)

    openwater_evapo[openwater_evapo < 0] = 0

    # =========================================================================
    # Calculating lake or wetland  groundwater recharge[gwr_lakewet (km3/day)]
    # =========================================================================
    # Point source recharge is calculated for arid regions only. Except in arid
    # inland sinks.
    if choose_swb == 'global lake':
        # Recharge for global lake needs to be reduced else more water will
        # recharge the ground since global lake area is assumed not be dynamic
        gwr_lakewet = np.where((aridity == 1) & (drainage_direction >= 0),
                               pm.groundwater_recharge_constant * m_to_km *
                               lake_wet_area * evapo_redfactor, 0)
    else:  # local lakes and global and local wetlands
        gwr_lakewet = np.where((aridity == 1) & (drainage_direction >= 0),
                               pm.groundwater_recharge_constant * m_to_km *
                               lake_wet_area, 0)

    # =========================================================================
    # Total inflow is the sum of inflow and open water precipitation into the
    # waterbody(km3/day)
    # =========================================================================
    total_inflow = inflow_to_swb + precipitation * lake_wet_area

    # =========================================================================
    # Combininig  open water PET and point source recharge into petgwr(km3/day)
    # =========================================================================
    # petgwr will change for Global lake if water-use is considerd ******
    petgwr = openwater_evapo * lake_wet_area + gwr_lakewet

    # Computing  petgwr_max.
    # Note!! lake (wetland) storage goes from -max_storage (0) to max_storage
    # and hence petgwr_max is calulated to help prevent lake (wetland) storage
    # from going beyond  -max_storage(0)
    if choose_swb == 'local lake' or choose_swb == 'global lake':
        petgwr_max = storage_prevstep + max_storage + total_inflow
    else:  # local and global wetlands
        petgwr_max = storage_prevstep + total_inflow

    # if choose_swb == 'global lake':
    #     print(petgwr_max[208, 430], petgwr[208, 430])
    # =========================================================================
    # Limiting lake (wetland) storage to -max_storage (0) when
    # petgwr >  petgwr_max. During -max_storage(0) the lake (wetland) area is
    # reduced by 100% (no lake or wetland available)
    # =========================================================================
    if choose_swb == 'local lake' or choose_swb == 'global lake':
        storage_limit = -1 * max_storage
    else:
        storage_limit = 0

    # Reduce point source recharge and open water evaporation when
    # petgwr >  petgwr_max. (check for zero division)
    petgwrmax_div_petgwr = \
        np.divide(petgwr_max, petgwr, out=np.zeros_like(petgwr_max),
                  where=petgwr != 0)
    gwr_lakewet = \
        np.where(petgwr > petgwr_max, gwr_lakewet * petgwrmax_div_petgwr,
                 gwr_lakewet)

    openwater_evapo = \
        np.where(petgwr > petgwr_max, openwater_evapo * petgwrmax_div_petgwr,
                 openwater_evapo)

    # =========================================================================
    #                   Computing storage for surface waterbody
    # ==========================================================================
    if choose_swb == 'global lake' or choose_swb == 'global wetland':
        # Global lake and wetland balance:
        # dS/dt = total_inflow - petgwr - NAl - k*S is solved analytically for
        # each time step of 1 day
        net_in = total_inflow - petgwr
        storage = storage_prevstep * np.exp(-1*pm.swb_outflow_coeff) + \
            (net_in/pm.swb_outflow_coeff)*(1-np.exp(-1 * pm.swb_outflow_coeff))

    else:
        # local lakes and wetland are solved numerically
        storage = storage_prevstep + total_inflow - petgwr

    storage = np.where(petgwr > petgwr_max, storage_limit, storage)

    # =========================================================================
    # computing local lakes and wetlands outflow (km3/day) and updating storage
    # =========================================================================
    if choose_swb == 'global lake':

        outflow = np.where(petgwr > petgwr_max, 0,
                           net_in + storage_prevstep - storage)
        # temporal or helper variable to compute final global lake lake outflow
        outflow_new = np.where((petgwr <= petgwr_max) &
                               (storage > max_storage),
                               outflow + storage - max_storage,
                               outflow)
        # updating storage
        storage = np.where((petgwr <= petgwr_max) & (storage > max_storage),
                           max_storage, storage)

        # update outflow (Claudia onlly used less than**)
        outflow = np.where((petgwr <= petgwr_max) & (outflow_new < 0), 0,
                           outflow_new)

        # # Recalculate global lake abd wetland storage when lake outflow = 0
        # dS/dt = total_inflow - petgwr - NAl
        # (without k*S) -> S(t) = S(t-1) + netgw_in
        # Claudia onlly used less than**
        storage = np.where((petgwr <= petgwr_max) & (outflow_new < 0),
                           net_in + storage_prevstep, storage)

    elif choose_swb == 'global wetland':

        outflow = np.where(petgwr > petgwr_max, 0,
                           net_in + storage_prevstep - storage)

        outflow = np.where(storage > max_storage,
                           outflow + storage - max_storage,
                           outflow)
        # updating storage
        storage = np.where(storage > max_storage, max_storage, storage)

    else:  # local lake and wetland
        # choose storage type to calculate outflow (current or previous)
        # but all should be previous.
        if choose_swb == 'local lake':  # previous storage
            which_storge = storage_prevstep
        else:
            which_storge = storage  # current storage

        storage_prevstep_div_max_storage = \
            np.divide(which_storge, max_storage,
                      out=np.zeros_like(max_storage), where=max_storage != 0)

        # Note: For local lakes previous storage can become negative hence
        # exponential expression is computed for positive storages only.
        # This means that for negatve storage  outflow is set to zero
        outflow = pm.swb_outflow_coeff * which_storge * \
            np.power(storage_prevstep_div_max_storage, exp_factor,
                     out=np.zeros_like(which_storge), where=which_storge > 0)

        outflow = np.where(outflow > storage, storage, outflow)
        outflow = np.where(storage <= 0, 0, outflow)

        # updating storage
        storage = storage - outflow

        # update outflow
        outflow = np.where(storage > max_storage,
                           outflow + storage - max_storage,
                           outflow)

        # updating storage
        storage = np.where(storage > max_storage, max_storage, storage)

    return storage, outflow, gwr_lakewet
