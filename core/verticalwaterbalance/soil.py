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


class Soil:
    """Compute snow storage and related fluxes.

    Parameters
    ----------
    static_data : contains the following data
        max_soil_water_content : array
            Maximum soil water content, Units: [mm]
        builtup_area : array
            Urban or Builtup area fraction, Units: [-]
        drainage_direction : array
            Drainage direction taken from [1]_, Units: [-]
        max_groundwater_recharge : array
            Maximum groundwater recharge, Units: [mm/day]
        soil_texture : array
            Soil texture class based on  [1]_, Units: [-]
        groundwater_recharge_factor : array
            Groundwater recharge factor taken from [1]_, Units: [-]
        arid_gw_cell : array
            Humid-arid calssification(array) based on [1]_.

        References.

        .. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                    Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                    Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                    Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                    The global water resources and use model WaterGAP v2.2d:
                    model description and evaluation. Geoscientific Model
                    Development, 14(2), 1037–1079.
                    https://doi.org/10.5194/gmd-14-1037-2021


    Methods
    -------
    immediate_runoff:
        Compute immediate runoff.

    daily_soil_storage:
        Compute daily soil storage.
    """

    def __init__(self, static_data, parameters):
        soil_static_data = static_data.soil_static_data()
        self.pm = parameters
        # ==========================================
        #      calulating maximum soil water content
        # ===========================================
        total_avail_water_content = soil_static_data[1]
        soil_parameters = static_data.canopy_snow_soil_parameters
        land_cover = static_data.land_cover

        # Getting rooting depth for for all grids.
        rooting_depth = np.zeros(land_cover.shape) * np.nan
        for i in range(len(soil_parameters)):
            rooting_depth[land_cover[:, :] == soil_parameters.loc[i, 'Number']] = \
                soil_parameters.loc[i, 'rooting_depth']
        self.max_soil_water_content = \
            np.where(total_avail_water_content > 0,
                     total_avail_water_content * rooting_depth, np.nan)

        # ===============================================
        #         # Getting soil water balance parameters
        # ===============================================
        self.builtup_area = soil_static_data[0]
        self.drainage_direction = soil_static_data[2]
        self.max_groundwater_recharge = soil_static_data[3]
        self.soil_texture = soil_static_data[4]
        self.groundwater_recharge_factor = soil_static_data[5]
        self.arid_gw_cell = static_data.humid_arid

    def immediate_runoff(self, effective_precipitation):
        """
        Compute immediate runoff and effective precipitation.

        Parameters
        ----------
        effective_precipitation : array
            Effective precipitation based on [1]_, Units: [mm/day]

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

        immediate_runoff = \
            np.where(self.builtup_area > 0,
                     (self.pm.runoff_frac_builtup * effective_precipitation
                      * self.builtup_area), 0)

        # Reducing effective precipitation by immediate runoff since 50% is
        # left.
        effective_precipitation =\
            np.where(self.builtup_area > 0., effective_precipitation -
                     immediate_runoff, effective_precipitation)
        return effective_precipitation, immediate_runoff

    def soil_balance(self, soil_water_content, pet_to_soil,
                     current_landarea_frac, landareafrac_ratio, max_temp_elev,
                     canopy_evap, effective_precipitation, precipitation,
                     immediate_runoff, land_storage_change_sum, sublimation,
                     daily_storage_transfer, snow_freeze_temp):
        """
        Compute daily soil balance.

        Parameters
        ----------
        soil_water_content : array
            Soil water content, Units: [mm]
        pet_to_soil : array
            Remaining energy for addtional evaporation from soil, Units: [mm]
        current_landarea_frac : array
           Land area fraction of current time step,  Units: [-]
        landareafrac_ratio : array
            Ratio of land area fraction of previous to current time step,
            Units: [-]
        max_temp_elev : array
            Maximum temperature from the 1st(lowest) elevation from snow
            algorithm. , Units: [K]
        canopy_evap : array
            anopy evaporation,  Units: [mm/day]
        effective_precipitation : array
            Effective precipitation based on [1]_, Units: [mm/day]
        precipitation : array
            Daily precipitation,  Units: [mm/day]
        immediate_runoff : array
            Immediate runoff, Units: [mm/day]
        land_storage_change_sum : array
            Sum of change in vertical balance storages, Units: [mm]
        sublimation : array
            Sublimation, Units: [mm/day]
        daily_storage_transfer : array
            Storage to be transfered to runoff when land area fraction of
            current time step is zero, Units: [mm]
        snow_freeze_temp: array
            Snow freeze temperature  , Units:  [K]

        Returns
        -------
        soil_water_content : array
            Updated soil water content , Units: [mm]
        groundwater_recharge_from_soil_mm : array
            Groundwater recharge from soil, Units: [mm/day]
        actual_soil_evap : array
            Actual evapotranspiration from the soil, Units: [mm/day]
        soil_saturation : array
            Soil saturation, Units: [-]
        surface_runoff : array
            Surface runoff from land, Units: [mm/day]
        daily_storage_transfer : array
            Updated storage to be transfered to runoff when land area fraction
            of current time step is zero, Units: [mm]

        """
        # =========================================================================
        # Check if  current_landarea_frac == 0 , then add previous storage to
        # daily_storage_tranfer. This storage will then  added to runoff.
        # (e.g. island)
        # =========================================================================
        daily_storage_transfer = \
            np.where(current_landarea_frac == 0, (daily_storage_transfer +
                     soil_water_content.copy())*self.pm.areal_corr_factor, 0)

        # =====================================================================
        # Calculating soil water overflow (R2) (mm) and soil water content(mm).
        # =====================================================================
        # Adapting  soil_water_content since land area fraction is dynamic
        soil_water_content *= landareafrac_ratio

        # Initial storage to calulate change in soil storage.
        initial_storage = soil_water_content.copy()

        # Soil_water_overflow (R2): see eq.18c in H. Müller Schmied et al 2021
        # (Corrigendum). Soil_water_overflow  will be used to calulate
        # Total daily runoff (runoff + immediate runoff + soil water overflow)
        soil_water_overflow = \
            np.where(soil_water_content > self.max_soil_water_content,
                     soil_water_content - self.max_soil_water_content, 0)

        soil_water_content = \
            np.where(soil_water_content > self.max_soil_water_content,
                     self.max_soil_water_content, soil_water_content)

        # =====================================================================
        # Calculating daily soil runoff (R3) (mm/day).
        # =====================================================================
        # Runoff (R3): see eq.18d in H. Müller Schmied et al 2021 (Corrigendum)
        soil_saturation = (soil_water_content/self.max_soil_water_content)

        # gamma = Runoff coefficient (-)
        daily_runoff = \
            effective_precipitation * (soil_saturation)**self.pm.gamma

        # =====================================================================
        # Calculating actual soil evapotranspiration (mm/day) and updating
        # soil water storage (mm).
        #           Order of calculation is important!!!
        # =====================================================================
        # Equation for  actual soil evapotranspiration taken from Eq. 17 in
        # H. Müller Schmied et al 2021.
        # max_daily_pet = maximum daily potential evapotransipration (mm/day)
        actual_soil_evap = np.minimum(pet_to_soil,
                                      (self.pm.max_daily_pet - canopy_evap) *
                                      soil_saturation)

        # Updating soil water content into a helper variable
        # soil_water_content_new (eq.15 in H. Müller Schmied et al 2021)
        soil_water_content_new = \
            (soil_water_content + effective_precipitation -
             actual_soil_evap - daily_runoff)

        # minimal storage volume =1e15 (smaller volumes set to zero) to counter
        # numerical inaccuracies***
        soil_water_content_new = \
            np.where(np.abs(soil_water_content_new) <= 1e-15, 0,
                     soil_water_content_new)

# =============================================================================
# I dont know why effective prctipiatation is set to zero after addition to the
# soil water content if you won't use it for further calculations. This was
# done in the old code (c++). I just wrote it here for safety (will remove
# this soon)
#         # Set effective_precipitation = 0 after adding it soil water content
#         effective_precipitation = \
#             np.where((max_temp_elev > snow_freeze_temp) &
#                      (self.max_soil_water_content > 0),
#                      0, effective_precipitation)
# =============================================================================

        #  Note !!!  when too much water has been taken out of the
        #  soil water storage (negative soil storage), soil water content is
        #  set to zero. Daily actual soil evaporation is now corrected by
        #  reducing by the soil water content (negative soil water content)

        actual_soil_evap = np.where(soil_water_content_new < 0,
                                    actual_soil_evap + soil_water_content_new,
                                    actual_soil_evap)

        soil_water_content_new[soil_water_content_new < 0] = 0

        # Actual soil evaporation only occurs when temperature is higher than
        # snow freeze temperature and when there is water in the soil to
        # evaporate
        actual_soil_evap = \
            np.where((max_temp_elev > snow_freeze_temp) &
                     (self.max_soil_water_content > 0),
                     actual_soil_evap, 0)

        # =================================================
        # +++ Soil saturation that can be  writing out +++
        # ==================================================
        # soil_saturation only occurs under favourable temperature and also
        # when maximum soil water content is greater than zero
        soil_saturation =\
            np.where((max_temp_elev > snow_freeze_temp) &
                     (self.max_soil_water_content > 0),
                     soil_saturation, 0)

        # ==============================================================
        #  Correcting runoff and immediate runoff with areal_corr_factor
        #            (Areal correction factor-CFA (-))
        # ==============================================================
        daily_runoff *= self.pm.areal_corr_factor
        immediate_runoff *= self.pm.areal_corr_factor

        # =====================================================================
        # Calculating ground water recharge from soil(mm/day),
        # potential recharge (mm/day)
        #               Order of calculation is important!!!
        # =====================================================================
        # Note: the 'mm' at the end of  groundwater_recharge_from_soil_mm
        # means it is  vertical water balance variable.This distinguish it from
        # ground water recharge in the horizontal water balance

        # Groundwater recharge equation is calulated based on  Eq. 19 from
        # H. Müller Schmied et al 2021
        groundwater_recharge_from_soil_mm = \
            np.minimum(self.max_groundwater_recharge,
                       self.groundwater_recharge_factor * daily_runoff)

        # For (semi) arid cells groundwater recharge becomes zero when critical
        # precipitation for groundwater recharge (default = 12.5 mm/day) is not
        # exceeded.
        groundwater_recharge_from_soil_mm_arid = \
            np.where(precipitation <= self.pm.critcal_gw_precipitation, 0,
                     groundwater_recharge_from_soil_mm)

        # For (semi) arid cells, water remains in the soil when critical
        # precipitation for groundwater recharge (default = 12.5 mm/day) is not
        # exceeded. This is stored in a helper variable 'potential_gw_recharge'
        potential_gw_recharge = \
            np.where(precipitation <= self.pm.critcal_gw_precipitation,
                     groundwater_recharge_from_soil_mm, 0)

        # Note!!! If a grid cell is  (semi)arid and has coarse
        # (sandy) soil, with texture class < 21 and drainage direction value
        # >= zero, groundwater recharge will only occur if precipitation
        # exceeds a critical value (default = 12.5 mm/day).
        groundwater_recharge_from_soil_mm = \
            np.where(((self.arid_gw_cell == 1) & (self.soil_texture < 21)) &
                     (self.drainage_direction >= 0),
                     groundwater_recharge_from_soil_mm_arid,
                     groundwater_recharge_from_soil_mm)

        # Making sure there is no potential_gw_recharge for humid cells.
        potential_gw_recharge = \
            np.where(((self.arid_gw_cell == 1) & (self.soil_texture < 21)) &
                     (self.drainage_direction >= 0), potential_gw_recharge, 0)

        # Making sure groundwater_recharge_from_soil_mm is only calulated
        # when the maximum temperature is greater than snow freeze temperature.
        groundwater_recharge_from_soil_mm = \
            np.where((max_temp_elev > snow_freeze_temp) &
                     (self.max_soil_water_content > 0),
                     groundwater_recharge_from_soil_mm, 0)

        # =====================================================================
        # Updating runoff and soil water content with remaning water in
        # the soil.
        # =====================================================================
        # As potential recharge is water that remains in the soil for
        # (seimi)arid under the prior stated conditions ,
        # it is subtracted from runoff and added to storage.

        # Remove double counting of CFA as recharge is computed from
        # corrected daily runoff.
        daily_runoff -= potential_gw_recharge
        soil_water_content_new += (potential_gw_recharge /
                                   self.pm.areal_corr_factor)

        # ===================================================================
        #  Calulating  total daily (RL) runoff (mm/day).
        # Total daily run off will later be used for the Surface runoff
        # which is written out. Order of calculation is important!!!
        # ===================================================================
        # Updating soil_water_overflow into a helper variable
        # soil_water_overflow_new (R2). see eq.18c in H. Müller Schmied et al
        # 2021 (Corrigendum).
        # if the updated soil_water_content_new > maximum soil water content
        # it becomes overflow. This is to prevent the storage of the current
        # time step to exceed maximum soil storage.
        # Note: effective precipition will be always be zero if
        # (max_temp_elev > snow_freeze_temp)
        soil_water_overflow_new = \
            np.where((soil_water_content_new > self.max_soil_water_content),
                     soil_water_overflow +
                     (soil_water_content_new - self.max_soil_water_content),
                     soil_water_overflow)

        soil_water_overflow_new *= self.pm.areal_corr_factor

        # Total daily runoff (RL) is calculated as runoff + immediate runoff +
        # updated soil water overflow (soil_water_overflow_new).
        # See eq. 18a in H. Müller Schmied et al 2021 (Corrigendum)
        total_daily_runoff = \
            np.where(self.max_soil_water_content > 0,
                     daily_runoff + immediate_runoff +
                     soil_water_overflow_new, 0)

        # Note!!! Total daily runoff is only calulated with  updated soil water
        # overflow (soil_water_overflow_new) when maximum temperature is above
        # freezing temperature, else the old soil_water_overflow is used.
        # This is because if maximum temperature is below freezing temperature,
        # soil water content of previous time step can be higher than
        # maximum soil water content hence runoff can be possible.
        # Also if max_temp_elev < snow_freeze_temp, effective_precipitation=0,
        # There is no need to add it to total daily runoff.

        total_daily_runoff = \
            np.where((max_temp_elev > snow_freeze_temp), total_daily_runoff,
                     (soil_water_overflow) * self.pm.areal_corr_factor)

        # =====================================================================
        #  +++ Soil_water_overflow, immdediate runoff and daily runof
        #  that can be wrrirten out ++++++
        # =====================================================================
        soil_water_overflow =\
            np.where((max_temp_elev > snow_freeze_temp) &
                     (self.max_soil_water_content > 0),
                     soil_water_overflow_new,
                     soil_water_overflow * self.pm.areal_corr_factor)

        # Immediate runoff is only corrected when conditions to calculate
        # total daily runoff is satified
        immediate_runoff =\
            np.where((max_temp_elev > snow_freeze_temp) &
                     (self.max_soil_water_content > 0),
                     immediate_runoff,
                     (immediate_runoff / self.pm.areal_corr_factor))

        daily_runoff =\
            np.where((max_temp_elev > snow_freeze_temp) &
                     (self.max_soil_water_content > 0),
                     daily_runoff, 0)

        # =====================================================================
        #         Updating soil_water_content
        # =====================================================================
        # if  updated soil_water_content_new exceeds maximum soil storage,
        # limit it to the maximum soil
        soil_water_content_new =\
            np.where(soil_water_content_new > self.max_soil_water_content,
                     self.max_soil_water_content, soil_water_content_new)

        # When maxumium temperature > snow freeze temperature,
        # snow_water_content becomes the updated soil_water_content_new
        soil_water_content = \
            np.where((max_temp_elev > snow_freeze_temp) &
                     (self.max_soil_water_content > 0),
                     soil_water_content_new, soil_water_content)

        # Adapt soil water content to land area fraction
        soil_water_content = np.where(current_landarea_frac <= 0, 0,
                                      soil_water_content)

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
            land_storage_change_sum * (self.pm.areal_corr_factor - 1.0) - \
            precipitation * (self.pm.areal_corr_factor - 1.0) + \
            (actual_soil_evap + canopy_evap + sublimation) * \
            self.pm.areal_corr_factor

        # Avoid negative values for corrected actual total evaporation for land
        # This negative values are stored in neg_land_aet
        neg_land_aet = np.where(corr_land_aet < 0, corr_land_aet, 0)
        corr_land_aet = np.where(corr_land_aet < 0, 0, corr_land_aet)

        # =====================================================================
        #                       Surface Runoff
        # =====================================================================
        # Correcting total_daily_runoff with neg_land_aet
        total_daily_runoff = np.where(neg_land_aet < 0,
                                      total_daily_runoff + neg_land_aet,
                                      total_daily_runoff)
        # Avoid negative total daily runoff  in case neg_land_aet is large.
        total_daily_runoff[total_daily_runoff < 0] = 0

        # Compute deficit surface runoff (neg_runoff) from total_daily_runoff
        # and groundwater recharge from soil after evapotranspiration
        # correction. The idea here is to reduce soil water content with
        # deficit surface runoff when groundwater recharge from soil is larger
        # than total daily runoff and limit groundwater recharge to total daily
        # runoff. surface runoff here will be zero.

        neg_runoff = \
            np.where((total_daily_runoff - groundwater_recharge_from_soil_mm)
                     < 0, (total_daily_runoff -
                           groundwater_recharge_from_soil_mm), 0)

        soil_water_content = \
            np.where((total_daily_runoff - groundwater_recharge_from_soil_mm)
                     < 0, soil_water_content + neg_runoff, soil_water_content)

        # Ensure that groundwater recharge  from soil is not greater than
        # total daily runoff
        groundwater_recharge_from_soil_mm = \
            np.where((total_daily_runoff - groundwater_recharge_from_soil_mm)
                     < 0, total_daily_runoff,
                     groundwater_recharge_from_soil_mm)

        # Finally surface runoff is calculated as follows:
        surface_runoff = total_daily_runoff - groundwater_recharge_from_soil_mm

        # =====================================================================
        # Assign zero to flux, if land area fraction is less than
        # or equal to zero
        # =====================================================================
        groundwater_recharge_from_soil_mm[current_landarea_frac <= 0] = 0
        actual_soil_evap[current_landarea_frac <= 0] = 0
        soil_saturation[current_landarea_frac <= 0] = 0
        surface_runoff[current_landarea_frac <= 0] = 0

        return soil_water_content, groundwater_recharge_from_soil_mm, \
            actual_soil_evap, soil_saturation, surface_runoff,  \
            daily_storage_transfer, total_daily_runoff, daily_runoff, \
            soil_water_overflow, immediate_runoff
