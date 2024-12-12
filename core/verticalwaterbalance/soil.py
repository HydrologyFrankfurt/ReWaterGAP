# -*- coding: utf-8 -*-

# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Soil Storage."""

# =============================================================================
# This module computes soil water balance, including soil storage and related
# fluxes for all grid cells based on section 4.4 of
# (Müller Schmied et al. (2021)). After, interception and snow, runoff from
# urban areas or immediate runoff (R1) is computed.
# Effective precipitation (computes as throufall - snowfall + snowmelt) is
# reduced by the immediate runoff. After, runoff from soil water overflow (R2)
# is computed.Then, daily runoff (R3), Bergström (1995), is calculated by using
# soil saturation, effective precipitation and runoff coefficient.
# Actual evapotranspiration is calculated and the soil storage is
# updated. Afterwards, ground water recharge is calculated based on the
# soil runoff (R3). Then, total daily runoff from land (RL) is computed as
# ( daily runoff (R3) + immediate runoff (R1) + soil water overflow (R2) )
# (see Corrigendum equation 18a-c of Müller Schmied et al. (2021)).

# For runoff from soil water overflow (R2),  we check if previous and current
# storage exceed maximum soil water and update runoff from soil water overflow
# accordingly.

# Note: Total daily runoff (RL) is corrected with areal correction factor (CFA)
# (if gamma is not sufficeint to fit simulated discharge). To conserve water
# balance , evapotranspiration is also corrected with CFA.

# After evapotranspiration correction, soil storage, total daily runoff and
#  groundwater recharge are adjusted as well. Finally Surface runoff is then
# calculated as total daily runoff minus ground water recharge.
# =============================================================================

import numpy as np
from numba import njit

# @njit is a decorator from numba to optimised the python code for speed.


@njit(cache=True)
def immediate_runoff(effective_precipitation, runoff_frac_builtup,
                     builtup_area_frac):
    """
    Compute immediate runoff and effective precipitation.

    Parameters
    ----------
    effective_precipitation : float
        Effective precipitation based on [1]_, Units: [mm/day]
    runoff_frac_builtup:float
        Fraction of effective_precipitation that directly becomes runoff
        (specifically in urban areas) based on [1]_, Units: [-]
    builtup_area_frac: float
        Built up (Urban) area fraction, Units: [-]

    Returns
    -------
    effective_precipitation : array
        Effective precipitation based on [1]_, Units: [mm/day]
    immediate_runoff : array
        Immediate runoff, Units: [mm/day]

    References.

    .. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                The global water resources and use model WaterGAP v2.2d:
                model description and evaluation. Geoscientific Model
                Development, 14(2), 1037–1079.
                https://doi.org/10.5194/gmd-14-1037-2021

    """
    # Runoff from urban areas or immediate runoff (R1). see eq.18b in H.
    # Müller Schmied et al 2021(Corrigendum)

    # Note !!! runoff_frac_builtup = 0.5, Which is the fraction of
    # effective_precipitation that directly becomes runoff (specifically
    # in urban areas)
    if builtup_area_frac > 0:
        immediate_runoff = runoff_frac_builtup * effective_precipitation * \
            builtup_area_frac

        # Reducing effective precipitation by immediate runoff since 50% is
        # left.
        effective_precipitation -= immediate_runoff
    else:
        immediate_runoff = 0

    return effective_precipitation, immediate_runoff


@njit(cache=True)
def soil_balance(soil_water_content, pet_to_soil,  current_landarea_frac,
                 landareafrac_ratio,  max_temp_elev, canopy_evap,
                 effective_precipitation, precipitation,
                 immediate_runoff, land_storage_change_sum, sublimation,
                 daily_storage_transfer, snow_freeze_temp, gamma,
                 max_daily_pet, humid_arid, soil_texture, drainage_direction,
                 max_groundwater_recharge, groundwater_recharge_factor,
                 critcal_gw_precipitation, max_soil_water_content,
                 areal_corr_factor, minstorage_volume, x, y):
    """
    Compute daily soil balance.

    Parameters
    ----------
    soil_water_content : float
        Soil water content, Units: [mm]
    pet_to_soil : float
        Remaining energy for addtional evaporation from soil, Units: [mm]
    current_landarea_frac : float
        Land area fraction of current time step,  Units: [-]
    landareafrac_ratio : float
        Ratio of land area fraction of previous to current time step,
           Units: [-]
    max_temp_elev : float
        Maximum temperature from the 1st(lowest) elevation from snow
        algorithm. , Units: [K]
    canopy_evap : float
       Canopy evaporation,  Units: [mm/day]
    effective_precipitation : float
        Effective precipitation based on  Müller Schmied et al 2021,
        Units: [mm/day]
    precipitation : float
        Daily precipitation,  Units: [mm/day]
    immediate_runoff : float
        Immediate runoff, Units: [mm/day]
    land_storage_change_sum : float
        Sum of change in vertical balance storages, Units: [mm]
    sublimation : float
        Sublimation, Units: [mm/day]
    daily_storage_transfer : float
        Storage to be transfered to runoff when land area fraction of
        current time step is zero, Units: [mm]
    snow_freeze_temp : float
        Snow freeze temperature  , Units:  [K]
    gamma : float
       Runoff coefficient , Units:  [-]
    max_daily_pet : float
        Maximum daily potential evapotranspiration, Units:  [mm/day]
    humid_arid : float
        Humid-arid calssification based on Müller Schmied et al. 2021
    soil_texture : float
       Soil texture classification based on Müller Schmied et al. 2021
    drainage_direction : float
        Drainage direction based on Müller Schmied et al. 2021
    max_groundwater_recharge : float
        Maximum groundwater recharge from soil, Units: [mm/day]
    groundwater_recharge_factor : float
        Groundwater recharge factor, Units:  [-]
    critcal_gw_precipitation : float
       critical precipitation for groundwater recharge, Units: [mm/day]
    max_soil_water_content : float
        Maximum soil water content , Units: [mm]
    areal_corr_factor : float
        Areal correction factor-CFA for correcting runoff,  Units:  [-]
    minstorage_volume : float
        Volume at which storage is set to zero, Units: [km3]
     x, y : Latititude and longitude indexes of grid cells.

    Returns
    -------
    soil_water_content : float
        Updated soil water content , Units: [mm]
    groundwater_recharge_from_soil_mm : float
        Groundwater recharge from soil, Units: [mm/day]
    actual_soil_evap : float
        Actual evapotranspiration from the soil, Units: [mm/day]
    soil_saturation : float
        Soil saturation, Units: [-]
    surface_runoff : float
        Surface runoff from land, Units: [mm/day]
    daily_storage_transfer : float
        Updated storage to be transfered to runoff when land area fraction
        of current time step is zero, Units: [mm]
    total_daily_runoff : float
        Total daily runoff from land (RL)
        (runoff + immediate runoff + soil water overflow), Units: [mm/day]
    daily_runoff : float
        daily runoff (R3), Bergström (1995),  Units: [mm/day]
    soil_water_overflow : float
        Soil water overflow (R2), Units: [mm/day]
    immediate_runoff : float
        runoff from urban areas or immediate runoff (R1), Units: [mm/day]

    """
    # Index (x, y) to  print out varibales of interest
    # e.g.  if x==65 and y==137: print(current_landarea_frac)

    if current_landarea_frac > 0:
        # =====================================================================
        # Calculating soil water overflow (R2) (mm) and soil water content(mm).
        # =====================================================================
        # Adapting  soil_water_content since land area fraction is dynamic
        soil_water_content *= landareafrac_ratio

        # Initial storage to calulate change in soil storage.
        initial_storage = soil_water_content

        # Soil_water_overflow (R2): see eq.18c in H. Müller Schmied et al 2021
        # (Corrigendum). Soil_water_overflow  will be used to calulate
        # Total daily runoff (runoff + immediate runoff + soil water overflow)
        soil_water_overflow = 0
        if soil_water_content > max_soil_water_content:
            soil_water_overflow = soil_water_content - max_soil_water_content
            soil_water_content = max_soil_water_content

        if max_temp_elev > snow_freeze_temp:
            if max_soil_water_content > 0:
                # =============================================================
                # Calculating daily soil runoff (R3) (mm/day).
                # =============================================================
                # Runoff (R3): see eq.18d in H. Müller Schmied et al 2021
                # (Corrigendum)
                soil_saturation = soil_water_content / max_soil_water_content

                # gamma = Runoff coefficient (-)
                daily_runoff = effective_precipitation * \
                    (soil_saturation)**gamma
                
                
                # =============================================================
                # Calculating actual soil evapotranspiration (mm/day) and
                # updating soil water storage (mm).
                # =============================================================
                # Equation for  actual soil evapotranspiration taken from
                # Eq. 17 in H. Müller Schmied et al 2021.
                # max_daily_pet = maximum daily potential evapotransipration
                # (mm/day)
                actual_soil_evap = \
                    np.minimum(pet_to_soil, (max_daily_pet - canopy_evap) *
                               soil_saturation)

                # Updating soil water content
                #  (eq.15 in H. Müller Schmied et al 2021)
                soil_water_content += (effective_precipitation -
                                       actual_soil_evap - daily_runoff)

                # minimal storage volume =1e15 (smaller volumes set to zero)
                # to counter numerical inaccuracies
                if np.abs(soil_water_content) <= minstorage_volume:
                    soil_water_content = 0

                # =============================================================
                # I dont know why effective prctipiatation is set to zero after
                # addition to the soil water content if you won't use it for
                # further calculations. This was done in the old code (c++).
                # I just wrote it here for safety (will removethis soon)
                #
                # effective_precipitation = 0
                # =============================================================

                # Note !!!  when too much water has been taken out of the
                # soil water storage (negative soil storage), soil water
                # content is set to zero. Daily actual soil evaporation is
                # now corrected by reducing with the soil water content
                # (negative soil water content)

                if soil_water_content < 0:
                    actual_soil_evap += soil_water_content
                    soil_water_content = 0

                # =============================================================
                # Correcting runoff and immediate runoff with areal_corr_factor
                #            Areal correction factor-CFA (-)
                # =============================================================
                daily_runoff *= areal_corr_factor
                immediate_runoff *= areal_corr_factor

                # =============================================================
                # Calculating ground water recharge from soil(mm/day),
                # potential recharge (mm/day)
                #               Order of calculation is important!!!
                # =============================================================
                # Note: the 'mm' at the end of
                # groundwater_recharge_from_soil_mm means it is a vertical
                # water balance variable.This distinguish it from
                # ground water recharge in the lateral water balance

                # Groundwater recharge equation is calulated based on  Eq. 19
                # from H. Müller Schmied et al 2021

                if (humid_arid == 1) & (soil_texture < 21) & \
                        (drainage_direction >= 0):
                    groundwater_recharge_from_soil_mm = \
                        np.minimum(max_groundwater_recharge,
                                   groundwater_recharge_factor * daily_runoff)

                    # For (semi) arid cells groundwater recharge becomes zero
                    # when critical precipitation for groundwater recharge
                    # (default = 12.5 mm/day) is not exceeded.
                    if precipitation <= critcal_gw_precipitation:
                        potential_gw_recharge = \
                            groundwater_recharge_from_soil_mm
                        groundwater_recharge_from_soil_mm = 0

                else:
                    potential_gw_recharge = 0
                    groundwater_recharge_from_soil_mm = \
                        np.minimum(max_groundwater_recharge,
                                   groundwater_recharge_factor * daily_runoff)

                # =============================================================
                # Updating runoff and soil water content with remaning water in
                # the soil.
                # =============================================================
                # As potential recharge is water that remains in the soil for
                # (seimi)arid under the prior stated conditions ,
                # it is subtracted from runoff and added to storage.

                # Remove double counting of CFA as recharge is computed from
                # corrected daily runoff.
                daily_runoff -= potential_gw_recharge
                soil_water_content += (potential_gw_recharge /
                                       areal_corr_factor)

                # Updating soil_water_overflow (R2) and soil water content.
                # if the updated soil_water_content > maximum, the excess
                # becomes overflow. This is to prevent the storage of the
                # current time step to exceed maximum soil storage.
                if soil_water_content > max_soil_water_content:
                    soil_water_overflow += soil_water_content - \
                        max_soil_water_content
                    soil_water_content = max_soil_water_content

                # correct runoff R2 with areal correction factor
                soil_water_overflow *= areal_corr_factor

                # Total daily runoff (RL) is calculated as runoff +
                # immediate runoff + updated soil water overflow
                # See eq. 18a in H. Müller Schmied et al 2021 (Corrigendum)
                total_daily_runoff = daily_runoff + immediate_runoff + \
                    soil_water_overflow
            else:
                total_daily_runoff = 0
                groundwater_recharge_from_soil_mm = 0
        else:
            soil_water_overflow *= areal_corr_factor
            total_daily_runoff = soil_water_overflow
            groundwater_recharge_from_soil_mm = 0
            actual_soil_evap = 0

        # computing change in soil_water_content
        soil_water_content_change = soil_water_content - initial_storage

        # Sum of change in vertical balance storages (canopy, snow, soil)
        land_storage_change_sum += soil_water_content_change

        # =====================================================================
        # Calulating corrected actual total evaporation for land (mm/day)
        # =====================================================================
        # Actual total evaporation from land is corrected such that when areal
        # correction factor is increased or reduced , actual total evaporation
        # will also be reduced or increased respectively. This is then
        # consistent with cell-corrected runoff.
        # ----------------------------------------------------------------
        # R(L) = P - AET - ds (dt=1) eqn. 1
        # R(L) * CFA  = P - AET_corr - ds (dt=1) eqn. 2
        # eqn2 into egn 1
        # P - AET_corr - ds = CFA ( P - AET - ds)
        # AET_corr = ds(CFA-1) - P(CFA-1) + AET(CFA)
        # ///////////////////////////////////////////////////////////
        # R(L): runoff from land (mm/day), P: precipitation (mm/day)
        # AET: actual total evaporation for land (mm/day)
        # ds: change in soil moisture storage (mm/day)
        # CFA: areal correction factor
        # /////////////////////////////////////////////////////////////

        corr_land_aet =\
            land_storage_change_sum * (areal_corr_factor - 1.0) - \
            precipitation * (areal_corr_factor - 1.0) + \
            (actual_soil_evap + canopy_evap + sublimation) * areal_corr_factor

        # Avoid negative values for corrected actual total evaporation for land
        # This negative values are stored in neg_land_aet
        if corr_land_aet < 0:
            neg_land_aet = corr_land_aet
            corr_land_aet = 0
    else:
        # =================================================================
        # Check if  current_landarea_frac == 0 , then add previous storage
        # to daily_storage_tranfer. This storage will then  added to runoff
        # (e.g. island)
        # =================================================================
        daily_storage_transfer += soil_water_content
        daily_storage_transfer *= areal_corr_factor
        soil_water_content = 0
        groundwater_recharge_from_soil_mm = 0
        total_daily_runoff = 0
        corr_land_aet = 0

    # =====================================================================
    #                       Surface Runoff
    # =====================================================================
    # Correcting total_daily_runoff with neg_land_aet
    if neg_land_aet < 0:
        total_daily_runoff = total_daily_runoff + neg_land_aet

    # Avoid negative total daily runoff  in case neg_land_aet is large.
    if total_daily_runoff < 0:
        total_daily_runoff = 0

    # Compute deficit surface runoff (neg_runoff) from total_daily_runoff
    # and groundwater recharge from soil [after evapotranspiration
    # correction]. The idea here is to reduce soil water content with
    # deficit surface runoff when groundwater recharge from soil is larger
    # than total daily runoff. Also groundwater recharge from soil is
    # limited to total daily runoff.
    if total_daily_runoff - groundwater_recharge_from_soil_mm < 0:
        neg_runoff = total_daily_runoff - groundwater_recharge_from_soil_mm

        # Ensure that groundwater recharge  from soil is not greater than
        # total daily runoff
        groundwater_recharge_from_soil_mm = total_daily_runoff

        soil_water_content += neg_runoff

        if soil_water_content < 0:
            soil_water_content = 0

    # Finally surface runoff is calculated as follows:
    surface_runoff = total_daily_runoff - groundwater_recharge_from_soil_mm

    return soil_water_content, groundwater_recharge_from_soil_mm, \
        actual_soil_evap, soil_saturation, surface_runoff,  \
        daily_storage_transfer, total_daily_runoff, daily_runoff, \
        soil_water_overflow, immediate_runoff, corr_land_aet
