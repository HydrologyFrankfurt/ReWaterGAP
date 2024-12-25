# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test groundwater module."""

import unittest
import xarray as xr
import numpy as np
from model.lateralwaterbalance import groundwater as gw

class TestGroundwater(unittest.TestCase):
    # creating fixtures
    def setUp(self):

        # note maximum soil storage values in the link below  are monthly hence
        # daily equivalent is computed
        # https://github.com/HydrologyFrankfurt/WaterGAP-main/issues/246: 

        self.groundwater_storage_max = 0.5  # km3
        self.groundwater_storage_min = -4000  # km3 negative due to abstraction
        self.size = (360, 720)

        self.groundwater_storage = np.zeros(self.size)  # km3
        self.diffuse_gw_recharge = np.random.uniform(0, 0.02, size=self.size)  # km3/day plausible value from WaterGAP (using maximum gw recharge as bounds)

        self.potential_net_abstraction_gw = np.random.uniform(-0.01, 0.006, size=self.size)  # km3/day
        self.daily_unsatisfied_pot_nas = np.zeros(self.size)  # km3/day
        self.prev_potential_water_withdrawal_sw_irri = np.random.uniform(0, 0.02, size=self.size)  # km3/day
        self.prev_potential_consumptive_use_sw_irri = np.random.uniform(0, 0.009, size=self.size)  # km3/day
        self.frac_irri_returnflow_to_gw = xr.open_dataarray("./input_data/static_input/watergap_22e_frgi.nc4", decode_times=False)[0].values # -

        # km3/day plausible value from WaterGAP (Using eqn 26 https://gmd.copernicus.org/articles/14/1037/2021/)
        self.point_source_recharge = np.random.uniform(0, 0.03, size=self.size)  

        global_parameters = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc", decode_times=False)
        self. gw_dis_coeff = global_parameters.gw_dis_coeff.values # 1/day

    # Test if results using acceptatable range for inputs
    def test_groundwater_storage_humid_region_validity(self):
        for x in range(self.groundwater_storage.shape[0]):
            for y in range(self.groundwater_storage.shape[1]):
                test_result = gw.\
                    groundwater_balance(x, y,
                                        "humid",
                                        self.groundwater_storage[x, y],
                                        self.diffuse_gw_recharge[x, y],
                                        self.potential_net_abstraction_gw[x, y],
                                        self.daily_unsatisfied_pot_nas[x, y],
                                        self.gw_dis_coeff[x, y],
                                        self.prev_potential_water_withdrawal_sw_irri[x, y],
                                        self.prev_potential_consumptive_use_sw_irri[x, y],
                                        self.frac_irri_returnflow_to_gw[x, y])

                self.groundwater_storage[x, y] = test_result[0]
        self.assertTrue((np.nanmin(self.groundwater_storage) >= self.groundwater_storage_min) &
                        (np.nanmax(self.groundwater_storage) <= self.groundwater_storage_max))
    
    # Test if results using acceptatable range for inputs
    def test_groundwater_storage_arid_region_validity(self):
        for x in range(self.groundwater_storage.shape[0]):
            for y in range(self.groundwater_storage.shape[1]):
                test_result = gw.\
                    groundwater_balance(x, y,
                                        "arid",
                                        self.groundwater_storage[x, y],
                                        self.diffuse_gw_recharge[x, y],
                                        self.potential_net_abstraction_gw[x, y],
                                        self.daily_unsatisfied_pot_nas[x, y],
                                        self.gw_dis_coeff[x, y],
                                        self.prev_potential_water_withdrawal_sw_irri[x, y],
                                        self.prev_potential_consumptive_use_sw_irri[x, y],
                                        self.frac_irri_returnflow_to_gw[x, y], 
                                        self.point_source_recharge[x, y])

                self.groundwater_storage[x, y] = test_result[0]
        self.assertTrue((np.nanmin(self.groundwater_storage) >= self.groundwater_storage_min) &
                        (np.nanmax(self.groundwater_storage) <= self.groundwater_storage_max))

