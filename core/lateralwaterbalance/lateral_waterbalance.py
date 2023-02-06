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
from core.lateralwaterbalance import river_property as rvp
from core.lateralwaterbalance import rout_flow as rt


class LateralWaterBalance:
    """Compute lateral waterbalance."""

    # Getting all storages and fluxes in this dictionary container
    fluxes = {}
    storages = {}
    land_swb_fraction = {}

    def __init__(self, forcings_static, parameters):
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Initialize storages and process propteries for lateral water balance
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #                  =================================
        #                  ||     Continent properties    ||
        #                  =================================
        # Cell area , Units : km2
        self.cell_area = forcings_static.static_data.cell_area.\
            astype(np.float64)
        self.parameters = parameters
        self.arid = forcings_static.static_data.humid_arid
        self.drainage_direction = \
            forcings_static.static_data.\
            soil_static_files.drainage_direction[0].values

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
        self.loclake_frac = forcings_static.static_data.\
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

        self.locwet_frac = forcings_static.static_data.\
            land_surface_water_fraction.locwet[0].values.astype(np.float64)/100

        # Initializing local weltland storage to maximum
        max_locwet_storage = self.cell_area * self.locwet_frac * \
            self.parameters.activewetland_depth * m_to_km

        # Local wetland storage, Units : km3
        self.locwet_storage = max_locwet_storage

        #                  =================================
        #                  ||          Global lake        ||
        #                  =================================

        self.glolake_frac = forcings_static.static_data.\
            land_surface_water_fraction.glolak[0].values.astype(np.float64)/100

        # Global lake area Units : km2
        self.glolake_area = forcings_static.global_lake_area

        # Initializing global lake storage to maximum,  Units : km3
        self.glolake_storage = self.glolake_area * self.parameters.activelake_depth * \
            m_to_km

        #                  =================================
        #                  ||        Global  wetland      ||
        #                  =================================
        self.glowet_frac = forcings_static.static_data.\
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
        river_slope = forcings_static.static_data.river_static_files.\
            river_slope[0].values.astype(np.float64)
        # Roughness (-)
        roughness = \
            forcings_static.static_data.river_static_files.\
            river_bed_roughness[0].values.astype(np.float64)
        # River length (m)
        river_length = forcings_static.static_data.river_static_files.\
            river_length[0].values.astype(np.float64)
        # Bank full river flow (m3/s)
        bankfull_flow = forcings_static.static_data.river_static_files.\
            bankfull_flow[0].values.astype(np.float64)
        # continental area fraction (-)
        continental_fraction = forcings_static.static_data.\
            land_surface_water_fraction.contfrac.values.astype(np.float64)

        self.get_river_prop = rvp.RiverProperties(river_slope, roughness,
                                                  river_length, bankfull_flow,
                                                  continental_fraction)
        # Initiliase routing order and respective outflow cell
        rout_order = forcings_static.static_data.rout_order
        self.rout_order = rout_order[['Lat_index_routorder',
                                      'Lon_index_routorder']].to_numpy()

        self.outflow_cell = rout_order[['Lat_index_outflowcell',
                                       'Lon_index_outflowcell']].to_numpy()

        # Initializing river storage to maximum (River at bankfull condition),
        # Units : km3
        self.river_storage = self.get_river_prop.max_river_storage

        #                  =================================
        #                  ||    Regulated lake storage   ||
        #                  =================================
        self.reglake_frac = forcings_static.static_data.\
            land_surface_water_fraction.reglak[0].values.astype(np.float64)/100

        # Regulated lake storage, Units : km3 *****

        #                  =================================
        #                  ||    Head water cells         ||
        #                  =================================
        self.headwater = forcings_static.static_data.\
            land_surface_water_fraction.headwater_cell.values

    def calculate(self, diffuse_gw_recharge, openwater_pot_evap, precipitation,
                  surface_runoff, current_landarea_frac):
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
            current_landarea_frac

        surface_runoff = surface_runoff * self.cell_area * mm_to_km * \
            current_landarea_frac
        # print( precipitation[43,129], surface_runoff[43,129])
        # =====================================================================
        # Preparing input variables for river routing
        # =====================================================================
        # Routing is optimised for with numba which cannot work on the *self*
        # object hence a copy of the self variable is created.
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
        glowet_storage = self.glowet_storage.copy()
        river_storage = self.river_storage.copy()
        river_length = self.get_river_prop.river_length.copy()
        river_bottom_width = self.get_river_prop.river_bottom_width.copy()
        roughness = self.get_river_prop.roughness.copy()
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
                      precipitation, openwater_pot_evap, river_storage,
                      river_length, river_bottom_width, roughness,
                      river_slope, outflow_cell,
                      self.parameters.gw_dis_coeff,
                      self.parameters.swb_drainage_area_factor,
                      self.parameters.swb_outflow_coeff,
                      self.parameters.gw_recharge_constant,
                      self.parameters.reduction_exponent_lakewet,
                      self.parameters.areal_corr_factor,
                      self.parameters.lake_out_exp,
                      self.parameters.activelake_depth,
                      self.parameters.wetland_out_exp,
                      self.parameters.activewetland_depth,
                      self.parameters.stat_corr_fact)

        self.groundwater_storage = out[0]
        self.loclake_storage = out[1]
        self.locwet_storage = out[2]
        self.glolake_storage = out[3]
        self.glowet_storage = out[4]
        self.river_storage = out[5]
        updated_locallake_fraction = out[8]
        updated_localwetland_fraction = out[9]
        updated_globalwetland_fraction = out[10]
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

        # LateralWaterBalance.fluxes.\
        #    update({'groundwater_discharge': groundwater_discharge,})
        #           'locallake_outflow': loclake_outflow})
        #             'localwetland_outflow': locwet_outflow,
        #             'globallake_outflow': glolake_outflow,
        #             'globalwetland_outflow': glowet_outflow})

        # =====================================================================
        #  Get dynamic area fraction for local lakes and local and
        #  global wetlands
        # =====================================================================
        LateralWaterBalance.land_swb_fraction.update({
            "current_land_area_fraction": current_landarea_frac,
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
        Get daily  dynamic area fraction for local lakes and local and
        #  global wetlands

        Returns
        -------
        dict
          updated fractions***.

        """
        return LateralWaterBalance.land_swb_fraction
