# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 14:37:44 2022.

@author: nyenah
"""
import unittest
from test import climat_and_static_data as cs
from termcolor import colored
import xarray as xr
import numpy as np
import numpy.testing as np_test
from core.verticalwaterbalance import compute_leaf_area_index as lai


class TestLeafAreaIndex(unittest.TestCase):
    # creating fixtures
    def setUp(self):
        """setting up climate forcing and static data."""
        self.climate_forcing = cs.ClimateForcing()
        self.static_data = cs.StaticData()

        # selecting data for simulation
        self.date = np.datetime64('1901-01-01')

        # initializing days since start of leaf area index profile
        self.days = np.zeros((360, 720))

        # initializing cumulative precipitation
        self.cum_precipitation = np.zeros((360, 720))

        # Growth status per grid cell shows whether a specific land cover
        # is (not) growing (value=0) or fully grown (value=1).
        # Initially all landcovers are not growing
        self.growth_status = np.zeros((360, 720))

        # Benchmark data
        out_path = './output_data/'
        try:
            self.benchmark_leaf_area_index = \
                xr.open_dataarray(out_path + 'leaf_area_index.nc')

        except FileNotFoundError:
            print("input file not found")
        else:
            self.benchmark_leaf_area_index = \
                 self.benchmark_leaf_area_index[0].values

    def test_compare_leaf_area_index_reults_and_dimensions(self):
        """ Compare simulated leaf area index results to benchmark.

        It also checks if the dimensions of the simulated data
        match the expected dimensions.
        """
        test_result = lai.LeafAreaIndex(self.climate_forcing,
                                        self.static_data, self.date,)

        simulated_result = \
            test_result.get_daily_leaf_area_index(self.days,
                                                  self.growth_status,
                                                  self.cum_precipitation)

        simulated_leaf_area_index = simulated_result[0]

        np_test.assert_almost_equal(simulated_leaf_area_index,
                                    self.benchmark_leaf_area_index)
        # checking data dimensions
        spatial_dim = simulated_leaf_area_index.shape

        self.assertEqual(spatial_dim, (360, 720))

    # Test if results using acceptatable range for inputs
    def test_result_validity(self):
        """Test if the results are within an acceptable range."""
        self.climate_forcing = cs.ClimateForcing(simulate=True)

        test_result = lai.LeafAreaIndex(self.climate_forcing,
                                        self.static_data, self.date,)

        simulated_result = \
            test_result.get_daily_leaf_area_index(self.days,
                                                  self.growth_status,
                                                  self.cum_precipitation)

        simulated_leaf_area_index = simulated_result[0]

        self.assertTrue((np.nanmin(simulated_leaf_area_index) >= 0) &
                        (np.nanmax(simulated_leaf_area_index) <= 4.78))

    # Test results for negative precipitation
    def test_with_negative_precipitation(self):
        """Test results when there is negative precipitation."""

        self.climate_forcing = cs.ClimateForcing(simulate=True, neg_prec=True)

        test_result = lai.LeafAreaIndex(self.climate_forcing,
                                        self.static_data, self.date,)

        with self.assertRaises(ValueError) as context:
            test_result.get_daily_leaf_area_index(self.days,
                                                  self.growth_status,
                                                  self.cum_precipitation)

        msg = colored("There are negative values in the precipitation data.",
                      'red')
        self.assertEqual(str(context.exception), msg)
