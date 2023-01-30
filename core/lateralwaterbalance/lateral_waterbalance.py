# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Lateral waterbalance."""

import numpy as np
from core.lateralwaterbalance import groundwaterstorage as gws
from core.lateralwaterbalance import local_lakes_and_wetlands as lw
from core.lateralwaterbalance import fractional_routing as fr
from core.verticalwaterbalance import parameters as pm


class LateralWaterBalance:
    """Compute lateral waterbalance."""

    # Getting all storages and fluxes in this dictionary container
    fluxes = {}
    storages = {}

    def __init__(self, forcings_static):
        # Cell Area, unit = km2
        self.cell_area = forcings_static.static_data.cell_area

        self.arid = forcings_static.static_data.humid_arid
        self.drainage_direction = \
            forcings_static.static_data.\
            soil_static_files.drainage_direction[0].values
        self.land_area_frac = forcings_static.curent_landareafrac

        # =====================================================================
        # Groundwater Storage, Units : m3
        # =====================================================================
        self.groundwater_storage = np.zeros((forcings_static.lat_length,
                                            forcings_static.lon_length))
        self.netabs_gw = np.zeros((forcings_static.lat_length,
                                   forcings_static.lon_length))
        self.remaining_use = np.zeros((forcings_static.lat_length,
                                      forcings_static.lon_length))

        # =====================================================================
        # Local lake storage, Units : m3
        # =====================================================================
        self.loclake_frac = forcings_static.static_data.\
            land_surface_water_fraction.loclak[0].values / 100

        # Initializing local lake storage to maximum
        m_to_km = 0.001
        max_loclake_storage = self.cell_area * self.loclake_frac * \
            pm.activelake_depth * m_to_km
        self.loclake_storage = max_loclake_storage

        # =====================================================================
        # Local wetland storage, Units : m3
        # =====================================================================
        self.locwet_frac = forcings_static.static_data.\
            land_surface_water_fraction.locwet[0].values / 100

        # Initializing local weltland storage to maximum
        max_locwet_storage = self.cell_area * self.locwet_frac * \
            pm.activewetland_depth * m_to_km
        self.locwet_storage = max_locwet_storage

        # =====================================================================
        # Global lakes storage, Units : m3
        # =====================================================================
        self.glolake_frac = forcings_static.static_data.\
            land_surface_water_fraction.glolak[0].values / 100

        self.glolake_area = forcings_static.global_lake_area

        # Initializing global lake storage to maximum
        self.glolake_storage = self.glolake_area * pm.activelake_depth * \
            m_to_km
        # =====================================================================
        # Global wetland storage, Units : m3
        # =====================================================================
        self.glowet_frac = forcings_static.static_data.\
            land_surface_water_fraction.glowet[0].values / 100

        # Initializing local weltland storage to maximum
        max_glowet_storage = self.cell_area * self.glowet_frac * \
            pm.activewetland_depth * m_to_km
        self.glowet_storage = max_glowet_storage

        # =====================================================================
        # Regulated  lakes storage, Units : m3
        # =====================================================================
        self.reglake_frac = forcings_static.static_data.\
            land_surface_water_fraction.reglak[0].values / 100

        # =====================================================================
        # Head water cells.
        # =====================================================================
        self.headwater_cell = forcings_static.static_data.\
            land_surface_water_fraction.headwater_cell.values

    def calculate(self, diffuse_gw_recharge, openwater_pot_evap, precipitation,
                  surface_runoff):
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
            self.land_area_frac

        surface_runoff = surface_runoff * self.cell_area * mm_to_km * \
            self.land_area_frac

        # =====================================================================
        #               Groundwater storage, Unit : km3/day
        # =====================================================================
        # 1. Compute groundwater storage for humid cells, Unit : km3/day
        # =====================================================================
        # Groundwater storage is computed 1st for humid region (self.arid == 0)
        # Note!!!: WaterGAP assumes no groundwater discharge from arid regions
        # into surface waterbodies(local and global lakes and wetlands) except
        # rivers
        daily_groundwaterstorage_humid = \
            np.where((self.arid == 0) & (self.drainage_direction >= 0), gws.
                     compute_groundwater_storage("humid",
                                                 self.groundwater_storage,
                                                 diffuse_gw_recharge,
                                                 self.cell_area,
                                                 self.netabs_gw,
                                                 self.remaining_use,
                                                 self.land_area_frac), 0)

        # Outputs from the  daily_groundwaterstorage_humid are
        # 0 = groundwater_storage,  1 = groundwater_discharge,

        groundwater_storage = daily_groundwaterstorage_humid[0]
        groundwater_discharge = daily_groundwaterstorage_humid[1]

        # =====================================================================
        # 2. Compute goundwater storage for inland sink, Unit : km3/day
        # =====================================================================
        daily_groundwaterstorage_landsink = \
            np.where(self.drainage_direction < 0, gws.
                     compute_groundwater_storage("inland sink",
                                                 self.groundwater_storage,
                                                 diffuse_gw_recharge,
                                                 self.cell_area,
                                                 self.netabs_gw,
                                                 self.remaining_use,
                                                 self.land_area_frac), 0)

        # Groundwater storage (discharge) from humid and inland sinks are
        # combined.
        groundwater_storage = np.where(self.drainage_direction < 0,
                                       daily_groundwaterstorage_landsink[0],
                                       groundwater_storage)

        groundwater_discharge = np.where(self.drainage_direction < 0,
                                         daily_groundwaterstorage_landsink[1],
                                         groundwater_discharge)

        # =====================================================================
        # Fractional routing to get infjow to surface waterbody, Unit: km3/day
        # =====================================================================
        inflow_to_swb = fr.frac_routing(surface_runoff,
                                        groundwater_discharge,
                                        self.loclake_frac, self.locwet_frac,
                                        self.glowet_frac, self.glolake_frac,
                                        self.reglake_frac, self.headwater_cell,
                                        self.drainage_direction)

        # =====================================================================
        # Compute local lake storage, Units : km3/day
        # =====================================================================
        loclake_storage = \
            np.where(self.loclake_frac > 0,
                     lw.lake_and_wetlands_balance('local lake',
                                                  self.loclake_storage,
                                                  self.loclake_frac,
                                                  precipitation,
                                                  openwater_pot_evap,
                                                  self.arid,
                                                  self.drainage_direction,
                                                  inflow_to_swb,
                                                  self.cell_area,), np.nan)

        # Outputs from the lake_and_wetlands_balance are
        # 0 = local lake storage,  1 = local lake outflow,
        # 2 = groundwater recharge from local lake

        self.loclake_storage = loclake_storage[0]
        loclake_outflow = loclake_storage[1]
        gwr_loclake = loclake_storage[2]

        # update inflow to surface water bodies
        inflow_to_swb = np.where(self.loclake_frac > 0, loclake_outflow,
                                 inflow_to_swb)
        # =====================================================================
        # Compute local wetland storage, Units : km3/day
        # =====================================================================
        locwet_inflow = inflow_to_swb
        locwet_storage = \
            np.where(self.locwet_frac > 0,
                     lw.lake_and_wetlands_balance('local wetland',
                                                  self.locwet_storage,
                                                  self.locwet_frac,
                                                  precipitation,
                                                  openwater_pot_evap,
                                                  self.arid,
                                                  self.drainage_direction,
                                                  locwet_inflow,
                                                  self.cell_area,), np.nan)

        # Outputs from the lake_and_wetlands_balance are
        # 0 = local wetland storage,  1 = local wetland outflow,
        # 2 = groundwater recharge from local wetland

        self.locwet_storage = locwet_storage[0]
        locwet_outflow = locwet_storage[1]
        gwr_locwet = locwet_storage[2]

        # update inflow to surface water bodies
        inflow_to_swb = np.where(self.locwet_frac > 0, locwet_outflow,
                                 inflow_to_swb)

        # =====================================================================
        #   Inflow from Upstream river into global lake
        # ======================================================================
        upstream_river_inflow_swb = 0
        inflow_to_swb += upstream_river_inflow_swb

        # =====================================================================
        # Compute global lake storage, Units : km3/day
        # =====================================================================
        glolake_storage = \
            np.where(self.glolake_area > 0,
                     lw.lake_and_wetlands_balance('global lake',
                                                  self.glolake_storage,
                                                  self.glolake_area,
                                                  precipitation,
                                                  openwater_pot_evap,
                                                  self.arid,
                                                  self.drainage_direction,
                                                  inflow_to_swb), np.nan)

        # Outputs from the lake_and_wetlands_balance are
        # 0 = global lake storage,  1 = global lake outflow,
        # 2 = groundwater recharge from global lake

        self.glolake_storage = glolake_storage[0]
        glolake_outflow = glolake_storage[1]
        gwr_glolake = glolake_storage[2]

        # update inflow to surface water bodies
        inflow_to_swb = np.where(self.glolake_area > 0, glolake_outflow,
                                 inflow_to_swb)

        # =====================================================================
        # Compute global wetland storage, Units : km3/day
        # =====================================================================
        glowet_inflow = inflow_to_swb
        glowet_storage = \
            np.where(self.glowet_frac > 0,
                     lw.lake_and_wetlands_balance('global wetland',
                                                  self.glowet_storage,
                                                  self.glowet_frac,
                                                  precipitation,
                                                  openwater_pot_evap,
                                                  self.arid,
                                                  self.drainage_direction,
                                                  glowet_inflow,
                                                  self.cell_area,), np.nan)

        # Outputs from the lake_and_wetlands_balance are
        # 0 = global wetland storage,  1 = global wetland outflow,
        # 2 = groundwater recharge from global wetland

        self.glowet_storage = glowet_storage[0]
        glowet_outflow = glowet_storage[1]
        gwr_glowet = glowet_storage[2]

        # =====================================================================
        # Compute groundwater storage for arid cells, Units : km3/day
        # =====================================================================
        point_source_recharge = \
            np.nan_to_num(gwr_loclake + gwr_locwet + gwr_glolake + gwr_glowet)
        # Groundwater storage is now computed for  arid region (self.arid == 1)
        daily_groundwater_storage_arid = \
            np.where((self.arid == 1) & (self.drainage_direction >= 0), gws.
                     compute_groundwater_storage("arid",
                                                 self.groundwater_storage,
                                                 diffuse_gw_recharge,
                                                 self.cell_area,
                                                 self.netabs_gw,
                                                 self.remaining_use,
                                                 self.land_area_frac,
                                                 point_source_recharge), np.nan)

        # Outputs from the  daily_groundwater_storage_arid are
        # 0 = groundwater_storage,  1 = groundwater_discharge,

        # Groundwater storage (discharge)  from arid, humid and inland sinks
        # are combined into one data.
        self.groundwater_storage = \
            np.where((self.arid == 1) & (self.drainage_direction >= 0),
                     daily_groundwater_storage_arid[0], groundwater_storage)

        groundwater_discharge = \
            np.where((self.arid == 1) & (self.drainage_direction >= 0),
                     daily_groundwater_storage_arid[1], groundwater_discharge)

        # =====================================================================
        # Getting all storages
        # =====================================================================
        LateralWaterBalance.storages.\
            update({'groundwater_storage': self.groundwater_storage,
                    'locallake_storage': self.loclake_storage,
                    'localwetland_storage': self.locwet_storage,
                    'globallake_storage': self.glolake_storage,
                    'globalwetland_storage': self.glowet_storage})

        # =====================================================================
        # Getting all fluxes
        # =====================================================================

        LateralWaterBalance.fluxes.\
            update({'groundwater_discharge': groundwater_discharge,
                    'locallake_outflow': loclake_outflow,
                    'localwetland_outflow': locwet_outflow,
                    'globallake_outflow': glolake_outflow,
                    'globalwetland_outflow': glowet_outflow})

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
