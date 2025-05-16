# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test canopy module."""

import unittest
import xarray as xr
import numpy as np
from termcolor import colored
from model.verticalwaterbalance import canopy as cs
from model.utility import units_conveter_check_neg_precip as check_precip
from controller import configuration_module as cm

class TestCanopy(unittest.TestCase):
    """Test canopy module."""

    # creating fixtures
    def setUp(self):
        #  The maximum canopy benchmark  value is obtained from multiplying the
        # maximum canopy storage coeff (0.3 mm) and maximum  one-side leaf area
        # index (4.78)
        # (see https://gmd.copernicus.org/articles/14/1037/2021/#section4)
        self.canopy_storage_max = 1.5  # mm  # rounded
        self.canopy_storage_min = 0  # mm

        self.size = (360, 720)
        self.canopy_input_data = {
           "canopy_storage": np.zeros(self.size),  # mm (current storage)
           "precipitation": np.random.uniform(0, 90, size=self.size),  # mm/day
           "potential_evap": np.random.uniform(0, 11, size=self.size),  # mm
           "current_land_area_frac": np.random.uniform(0, 1, size=self.size),  # -
           "landareafrac_ratio": (np.random.uniform(0, 1, size=self.size) /
                                  np.random.uniform(0, 1, size=self.size)),  # -
           "daily_leaf_area_index": np.random.uniform(0, 4.78, size=self.size),  # -
           "max_storage_coefficient": np.full(self.size, 0.3),  # mm
           "minstorage_volume": 1e-15,  # mm
        }

    # Test results for acceptatable range for inputs
    def test_canopy_storage_validity(self):
        """
        check canopy storage against valid ranges.

        Returns
        -------
        None.

        """
        # Run canopy function
        for x in range(self.canopy_input_data['canopy_storage'].shape[0]):
            for y in range(self.canopy_input_data['canopy_storage'].shape[1]):
                test_result = cs.canopy_water_balance(
                    self.canopy_input_data['canopy_storage'][x, y],
                    self.canopy_input_data['daily_leaf_area_index'][x, y],
                    self.canopy_input_data['potential_evap'][x, y],
                    self.canopy_input_data['precipitation'][x, y],
                    self.canopy_input_data['current_land_area_frac'][x, y],
                    self.canopy_input_data['landareafrac_ratio'][x, y],
                    self.canopy_input_data['max_storage_coefficient'][x, y],
                    self.canopy_input_data['minstorage_volume'],
                    x, y
                )
                self.canopy_input_data['canopy_storage'][x, y] = test_result[0]

        # Assert that the canopy storage is within the expected range
        self.assertTrue(
            (np.nanmin(self.canopy_input_data['canopy_storage']) >= self.canopy_storage_min) &
            (np.nanmax(self.canopy_input_data['canopy_storage']) <= self.canopy_storage_max)
        )

    # Test results for negative precipitation
    def test_canopy_storage_negative_precipitation(self):
        """
        check if canopy modules run if precipitation values are negative.

        Returns
        -------
        None.

        """

        # Define latitude and longitude coordinates
        latitudes = np.linspace(-90, 90, self.size[0])
        longitudes = np.linspace(-180, 180, self.size[1])

        # Create an xarray DataArray
        precipitation = xr.DataArray(
            np.random.uniform(-5, 90, size=self.size),
            dims=["lat", "lon"],
            coords={"lat": latitudes, "lon": longitudes}
        )

        self.canopy_input_data['precipitation'] = precipitation
        with self.assertRaises(ValueError) as context:
            check_precip.check_neg_precipitation(precipitation)
            # Run the canopy water balance with the precipitation data
            for x in range(self.canopy_input_data['canopy_storage'].shape[0]):
                for y in range(self.canopy_input_data['canopy_storage'].shape[1]):
                    cs.canopy_water_balance(
                        self.canopy_input_data['canopy_storage'][x, y],
                        self.canopy_input_data['daily_leaf_area_index'][x, y],
                        self.canopy_input_data['potential_evap'][x, y],
                        self.canopy_input_data['precipitation'][x, y],
                        self.canopy_input_data['current_land_area_frac'][x, y],
                        self.canopy_input_data['landareafrac_ratio'][x, y],
                        self.canopy_input_data['max_storage_coefficient'][x, y],
                        self.canopy_input_data['minstorage_volume'],
                        x, y
                    )

        msg = colored("There are negative values in the precipitation data.",
                      'red')
        self.assertEqual(str(context.exception), msg)
