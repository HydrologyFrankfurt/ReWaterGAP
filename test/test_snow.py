# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test snow module."""

import unittest
import xarray as xr
import numpy as np
import pandas as pd
from model.verticalwaterbalance import snow as swe


class TestSnow(unittest.TestCase):
    """Test snow module."""

    # creating fixtures
    def setUp(self):
        self.size = (360, 720)
        input_path = "./input_data/static_input/"
        # Snow water storage limits
        self.snow_water_storage_max = 1000  # mm
        self.snow_water_storage_min = 0  # mm

        # Initialize the input data dictionary
        self.snow_data = {
            "snow_water_storage": np.zeros(self.size),  # mm
            "current_land_area_frac": np.random.uniform(0, 1, size=self.size),  # -
            "landareafrac_ratio": (np.random.uniform(0, 1, size=self.size) /
                                   np.random.uniform(0, 1, size=self.size)),  # -
            "temperature": np.random.uniform(273.15, 303.15, size=self.size),  # K
            "precipitation": np.random.uniform(0, 90, size=self.size),  # mm/day
            "throughfall": np.random.uniform(0, 88.5, size=self.size),  # mm/day
            "pet_to_soil": np.random.uniform(0, 15, size=self.size),  # mm/day
            "land_storage_change_sum": np.random.uniform(0, 1.5, size=self.size),  # mm
            "daily_storage_transfer": np.zeros(self.size),  # mm
            "degreeday": np.zeros(self.size),  # Degree day factor
        }

        # Load external data
        parameters_snow = \
            pd.read_csv(input_path + "/canopy_snow_parameters.csv")
        land_cover = xr.open_dataarray(input_path + "/watergap_22e_landcover.nc4",
                                       decode_times=False)
        land_cover = land_cover[0].values

        # Assign degree day values based on land cover
        for i in range(len(parameters_snow)):
            self.snow_data["degreeday"][land_cover[:, :] == parameters_snow.loc[i, 'Number']] = \
                parameters_snow.loc[i, 'degree-day']

        self.elevation = xr.open_dataarray(input_path + "/watergap_22e_elevrange.nc4",
                                           decode_times=False).values

        # Snow water storage subgrid and snow water storage
        elev_size = self.elevation[1:].shape
        self.snow_data["snow_water_storage_subgrid"] = np.zeros(elev_size)  # mm

        # Load global parameters
        self.global_parameters = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc",
                                                 decode_times=False)

    # Test if results using acceptatable range for inputs
    def test_snow_water_equiv_validity(self):
        """
        check snow storage against valid ranges.

        Returns
        -------
        None.

        """
        minstorage_volume = 1e-15  # mm
        for x in range(self.snow_data["snow_water_storage"].shape[0]):
            for y in range(self.snow_data["snow_water_storage"].shape[1]):
                test_result = swe.snow_water_balance(
                    self.snow_data["snow_water_storage"][x, y],
                    self.snow_data["snow_water_storage_subgrid"][:, x, y],
                    self.snow_data["temperature"][x, y],
                    self.snow_data["precipitation"][x, y],
                    self.snow_data["throughfall"][x, y],
                    self.snow_data["pet_to_soil"][x, y],
                    self.snow_data["land_storage_change_sum"][x, y],
                    self.snow_data["degreeday"][x, y],
                    self.snow_data["current_land_area_frac"][x, y],
                    self.snow_data["landareafrac_ratio"][x, y],
                    self.elevation[:, x, y],
                    self.snow_data["daily_storage_transfer"][x, y],
                    self.global_parameters.adiabatic_lapse_rate.values[x, y],
                    self.global_parameters.snow_freeze_temp.values[x, y],
                    self.global_parameters.snow_melt_temp.values[x, y],
                    minstorage_volume,
                    x, y
                )

                # Store the result
                self.snow_data["snow_water_storage"][x, y] = test_result[0]

        # Assert that the snow water storage is within valid range
        self.assertTrue(
            (np.nanmin(self.snow_data["snow_water_storage"]) >= self.snow_water_storage_min) &
            (np.nanmax(self.snow_data["snow_water_storage"]) <= self.snow_water_storage_max)
        )
