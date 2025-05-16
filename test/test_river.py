# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test River module."""


import unittest
import xarray as xr
import numpy as np
from model.lateralwaterbalance import river_init
from model.lateralwaterbalance import river
from controller import configuration_module as cm


class TestRiver(unittest.TestCase):
    """Test river module."""
    # creating fixtures
    def setUp(self):
        # River storage can be bigger than max river since we dont bound it
        # to the max , i dont know why yet
        self.river_storage_max = 20  # km3
        self.river_storage_min = 0  # km3

        size = (360, 720)
        self.river_inflow = np.random.uniform(0, 10, size=size)  # km3/day plausible

        self.accumulated_unsatisfied_potential_netabs_sw = \
            np.random.uniform(0, 0.02, size=size)  # km3/day plausible

        input_path = "./input_data/static_input/river_static_data/"
        # River slope (-),
        river_slope = xr.open_dataarray(input_path + "watergap_22e_river_slope.nc4",
                                        decode_times=False)[0].values

        # Roughness (-)
        roughness = xr.open_dataarray(input_path + "watergap_22e_river_bed_roughness.nc4",
                                      decode_times=False)[0].values

        # Roughness multiplier (-)
        # Load global parameters
        path_global_par = cm.global_parameter_path
        if path_global_par.startswith("model"):
            path_global_par = f"./{path_global_par}"
        global_parameters = xr.open_dataset(path_global_par, decode_times=False)
        self.roughness_multiplier = \
            global_parameters.river_roughness_coeff_mult.values.astype(np.float64)
        self.stat_corr_fact = global_parameters.stat_corr_fact.values.astype(np.float64)

        # River length  with uncorrected length in coastal cells (km).
        # Note: River length is later corrected with continental cell fraction
        # (see RiverProperties function in river_property.py module)
        river_length = xr.open_dataarray(input_path + "watergap_22e_river_length.nc4",
                                         decode_times=False)[0].values

        # Bank full river flow (m3/s)
        bankfull_flow = xr.open_dataarray(input_path + "watergap_22e_bankfull_flow.nc4",
                                          decode_times=False)[0].values

        # continental area fraction (-)
        continental_fraction = \
            xr.open_dataarray("./input_data/static_input/land_water_fractions"
                              "/watergap_22e_contfrac_global.nc",
                              decode_times=False).values

        self.get_river_prop = \
            river_init.RiverProperties(river_slope, roughness,
                                       river_length, bankfull_flow,
                                       continental_fraction)

    def test_river_storage_validity(self):
        """
        Test if river lake storage is within a valid range.

        Returns
        -------
        None.

        """
        river_storage = self.get_river_prop.max_river_storage
        minstorage_volume = 1e-15  # km3
        for x in range(river_storage.shape[0]):
            for y in range(river_storage.shape[1]):
                # ==========================
                # 1. Compute river velocity
                # ==========================
                # Output of "velocity_and_outflowconst" are
                # 0 = velocity (km/day),  1 =  outflow contstant (1/day)
                velocity_and_outflowconst = \
                    river.river_velocity(x, y,
                                         river_storage[x, y],
                                         self.get_river_prop.river_length[x, y],
                                         self.get_river_prop.river_bottom_width[x, y],
                                         self.get_river_prop.roughness[x, y],
                                         self.roughness_multiplier[x, y],
                                         self.get_river_prop.river_slope[x, y])

                velocity_outflow_constant = velocity_and_outflowconst
                # ================================================
                # 2. Compute storage(km3) and streamflow(km3/day)
                # ================================================
                # river_start_use= accumulated_unsatisfied_potential_netabs_sw[x, y]
                test_result = river.river_water_balance(x, y,
                                river_storage[x, y],
                                self.river_inflow[x, y],
                                velocity_outflow_constant[1],
                                self.stat_corr_fact[x, y],
                                self.accumulated_unsatisfied_potential_netabs_sw[x, y],
                                minstorage_volume)
                river_storage[x, y] = test_result[0]
        self.assertTrue((np.nanmin(river_storage) >= self.river_storage_min) &
                        (np.nanmax(river_storage) <= self.river_storage_max))
