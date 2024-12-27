# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test Lakes and Wetlands module."""

import unittest
import xarray as xr
import numpy as np
from model.lateralwaterbalance import lakes_wetlands as lw


class TestLakesWetlands(unittest.TestCase):
    """Test Lakes and Wetlands module."""
    # creating fixtures
    def setUp(self):

        # note maximum storages are computed based on watergap frac, cell area a
        # and activate surface waterbodies depth
        self.input_path = "./input_data/static_input/"
        self.size = (360, 720)
        self.precipitation = np.random.uniform(0, 3, size=self.size)  # km3/day
        self.openwater_pot_evap = np.random.uniform(0, 0.05, size=self.size)  # km3/day

        global_parameters = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc",
                                            decode_times=False)

        self.global_params = {
            'gw_dis_coeff': global_parameters.gw_dis_coeff.values,  # 1/day
            'swb_outflow_coeff': global_parameters.swb_outflow_coeff.values,  # 1/day
            'gw_recharge_constant': global_parameters.gw_recharge_constant.values,  # m/day
            'reduction_exponent_lakewet': global_parameters.reduction_exponent_lakewet.values,  # -
            'areal_corr_factor': global_parameters.areal_corr_factor.values,  # -
            'lake_outflow_exp': global_parameters.lake_out_exp.values,  # -
            'wetland_outflow_exp': global_parameters.wetland_out_exp.values,  # -

            # Apply maximum depth constraint for these parameters
            'activelake_depth': global_parameters.activelake_depth.values, # m
            'activewetland_depth': global_parameters.activewetland_depth.values  # m
            }

        self.static_data = {
            'aridhumid': xr.open_dataarray(self.input_path + "watergap_22e_aridhumid.nc4",
                                           decode_times=False)[0].values,
            'drainage_direction': 
                xr.open_dataarray(self.input_path +
                                  "soil_storage/watergap_22e_drainage_direction.nc",
                                  decode_times=False)[0].values,
            'cell_area': xr.open_dataarray(self.input_path + "watergap_22e_continentalarea.nc", 
                                           decode_times=False).values,  # km2
            }

    # Test if results using acceptatable range for inputs
    def test_local_lake_storage_validity(self):
        """Test if local lake storage is within a valid range."""
        # ====================================
        # local lake
        # =====================================
        loclake_storage_max = 3  # km3
        loclake_storage_min = -3  # km3
        loclake_frac = xr.open_dataarray(self.input_path +
                                         "land_water_fractions/watergap_22e_loclak.nc4", 
                                         decode_times=False)[0].values  # %

        loclake_frac = loclake_frac/100
        # Initializing local lake storage to maximum
        # Local lake area and storage,  Units : km2 & km3 respectively
        m_to_km = 0.001

        max_loclake_area = self.static_data["cell_area"] * loclake_frac

        max_loclake_storage = \
            max_loclake_area * self.global_params["activelake_depth"] * m_to_km

        loclake_storage = max_loclake_storage

        inflow_to_swb_lake = np.random.uniform(0, 1.5, size=self.size)  # km3/day plausible

        for x in range(loclake_storage.shape[0]):
            for y in range(loclake_storage.shape[1]):
                if loclake_frac[x, y] > 0:
                    test_result = lw.lake_wetland_water_balance(x, y,
                                   "local lake",
                                    loclake_storage[x, y],
                                    self.precipitation[x, y],
                                    self.openwater_pot_evap[x, y],
                                    self.static_data["aridhumid"][x, y],
                                    self.static_data["drainage_direction"][x, y],
                                    inflow_to_swb_lake[x, y],
                                    self.global_params["swb_outflow_coeff"][x, y],
                                    self.global_params["gw_recharge_constant"][x, y],
                                    self.global_params["reduction_exponent_lakewet"][x, y],
                                    self.global_params["areal_corr_factor"][x, y],
                                    max_storage=max_loclake_storage[x, y],
                                    max_area=max_loclake_area[x, y],
                                    lakewet_frac=loclake_frac[x, y],
                                    lake_outflow_exp=
                                    self.global_params["lake_outflow_exp"][x, y])

                    loclake_storage[x, y] = test_result[0]
            self.assertTrue((np.nanmin(loclake_storage) >= loclake_storage_min) &
                            (np.nanmax(loclake_storage) <= loclake_storage_max))

    # Test if results using acceptatable range for inputs
    def test_local_wetland_storage_validity(self):
        """Test if local wetland storage is within a valid range."""
        # ====================================
        # local lake
        # =====================================
        locwet_storage_max = 11.1  # km3 (numerically plausible)
        locwet_storage_min = 0  # km3
        locwet_frac = xr.open_dataarray(self.input_path +
                                        "land_water_fractions/watergap_22e_locwet.nc4",
                                        decode_times=False)[0].values  # %
        locwet_frac = locwet_frac/100
        m_to_km = 0.001

        max_locwet_area = self.static_data["cell_area"] * locwet_frac

        max_locwet_storage = \
            max_locwet_area * self.global_params["activewetland_depth"] * m_to_km

        locwet_storage = max_locwet_storage

        inflow_to_swb_wet = np.random.uniform(0, 10.5, size=self.size)  # km3/day plausible

        for x in range(locwet_storage.shape[0]):
            for y in range(locwet_storage.shape[1]):
                if locwet_frac[x, y] > 0:
                    test_result = lw.lake_wetland_water_balance(x, y,
                                   'local wetland',
                                    locwet_storage[x, y],
                                    self.precipitation[x, y],
                                    self.openwater_pot_evap[x, y],
                                    self.static_data["aridhumid"][x, y],
                                    self.static_data["drainage_direction"][x, y],
                                    inflow_to_swb_wet[x, y],
                                    self.global_params["swb_outflow_coeff"][x, y],
                                    self.global_params["gw_recharge_constant"][x, y],
                                    self.global_params["reduction_exponent_lakewet"][x, y],
                                    self.global_params["areal_corr_factor"][x, y],
                                    max_storage=max_locwet_storage[x, y],
                                    max_area=max_locwet_area[x, y],
                                    lakewet_frac=locwet_frac[x, y],
                                    wetland_outflow_exp=
                                    self.global_params["wetland_outflow_exp"][x, y])

                    locwet_storage[x, y] = test_result[0]
            self.assertTrue((np.nanmin(locwet_storage) >= locwet_storage_min) &
                            (np.nanmax(locwet_storage) <= locwet_storage_max))

    # Test if results using acceptatable range for inputs
    def test_global_lake_storage_validity(self):
        """Test if global lake storage is within a valid range."""
        # ====================================
        # local lake
        # =====================================
        glolake_storage_max = 411  # km3
        glolake_storage_min = -411 # km3
        glolake_frac = xr.open_dataarray(self.input_path +
                                         "land_water_fractions/watergap_22e_glolak.nc4",
                                         decode_times=False)[0].values  # %

        glolake_frac = glolake_frac/100
        # Initializing local lake storage to maximum
        # Local lake area and storage,  Units : km2 & km3 respectively
        m_to_km = 0.001

        max_glolake_area = \
            xr.open_dataarray(self.input_path +
                              "land_water_fractions/watergap_22e_global_lake_area.nc",
                              decode_times=False)[0].values  # km2
        glores_area = \
            xr.open_dataarray(self.input_path + "land_water_fractions/"
                              "watergap_22e_reservoir_and_regulated_lake_area.nc",
                              decode_times=False)[0].values  # km2

        max_glolake_storage = \
            max_glolake_area * self.global_params["activelake_depth"] * m_to_km

        glolake_storage = max_glolake_storage

        inflow_to_swb_lake = np.random.uniform(0, 15, size=self.size)  # km3/day plausible

        accumulated_unsatisfied_potential_netabs_sw = \
            np.random.uniform(0, 0.02, size=self.size)  # km3/day plausible

        for x in range(glolake_storage.shape[0]):
            for y in range(glolake_storage.shape[1]):
                if max_glolake_area[x, y] > 0:
                    test_result = lw.lake_wetland_water_balance(x, y,
                                "global lake",
                                glolake_storage[x, y],
                                self.precipitation[x, y],
                                self.openwater_pot_evap[x, y],
                                self.static_data["aridhumid"][x, y],
                                self.static_data["drainage_direction"][x, y],
                                inflow_to_swb_lake[x, y],
                                self.global_params["swb_outflow_coeff"][x, y],
                                self.global_params["gw_recharge_constant"][x, y],
                                self.global_params["reduction_exponent_lakewet"][x, y],
                                self.global_params["areal_corr_factor"][x, y],
                                max_storage=max_glolake_storage[x, y],
                                max_area=max_glolake_area[x, y],
                                lakewet_frac=glolake_frac[x, y],
                                lake_outflow_exp=
                                self.global_params["lake_outflow_exp"][x, y],
                                reservoir_area=glores_area[x, y],
                                accumulated_unsatisfied_potential_netabs_sw=
                                accumulated_unsatisfied_potential_netabs_sw[x, y])

                    glolake_storage[x, y] = test_result[0]

            self.assertTrue((np.nanmin(glolake_storage) >= glolake_storage_min) &
                            (np.nanmax(glolake_storage) <= glolake_storage_max))

    # Test if results using acceptatable range for inputs
    def test_global_wetland_storage_validity(self):
        """Test if global wetland storage is within a valid range."""
        # ====================================
        # local lake
        # ====================================
        glowet_storage_max = 16 # km3 (numerically plausible)
        glowet_storage_min = 0  # km3
        glowet_frac = \
            xr.open_dataarray(self.input_path +
                              "land_water_fractions/watergap_22e_glowet.nc4",
                              decode_times=False)[0].values  # %

        glowet_frac = glowet_frac/100
        m_to_km = 0.001

        max_glowet_area = self.static_data["cell_area"] * glowet_frac

        max_glowet_storage =\
            max_glowet_area * self.global_params["activewetland_depth"] * m_to_km

        glowet_storage = max_glowet_storage

        inflow_to_swb_wet = np.random.uniform(0, 10.5, size=self.size)  # km3/day plausible

        for x in range(glowet_storage.shape[0]):
            for y in range(glowet_storage.shape[1]):
                if glowet_frac[x, y] > 0:
                    test_result = lw.lake_wetland_water_balance(x, y,
                                    'global wetland',
                                    glowet_storage[x, y],
                                    self.precipitation[x, y],
                                    self.openwater_pot_evap[x, y],
                                    self.static_data["aridhumid"][x, y],
                                    self.static_data["drainage_direction"][x, y],
                                    inflow_to_swb_wet[x, y],
                                    self.global_params["swb_outflow_coeff"][x, y],
                                    self.global_params["gw_recharge_constant"][x, y],
                                    self.global_params["reduction_exponent_lakewet"][x, y],
                                    self.global_params["areal_corr_factor"][x, y],
                                    max_storage=max_glowet_storage[x, y],
                                    max_area=max_glowet_area[x, y],
                                    lakewet_frac=glowet_frac[x, y],
                                    wetland_outflow_exp=
                                    self.global_params["wetland_outflow_exp"][x, y])

                    glowet_storage[x, y] = test_result[0]
            self.assertTrue((np.nanmin(glowet_storage) >= glowet_storage_min) &
                            (np.nanmax(glowet_storage) <= glowet_storage_max))
