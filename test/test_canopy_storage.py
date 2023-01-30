# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 14:37:44 2022

@author: nyenah
"""
import glob
from termcolor import colored
import unittest
import numpy as np
import xarray as xr
import numpy.testing as np_test
from core.verticalwaterbalance import canopy_storage_module as cs
from test.land_water_fractions import _landfrac as lf


class TestCanopy(unittest.TestCase):
    # creating fixtures
    def setUp(self):
        # set data path
        out_path = './output_data/'
        in_path = './input_data/climate_forcing/precipitation/*.nc'
        try:
            # set benchmark data
            self.benchmark_canopy_storage =\
                xr.open_dataarray(out_path + 'canopy_storage.nc')

            # get input values
            self.daily_leaf_area_index = \
                xr.open_dataarray(out_path + 'leaf_area_index.nc')
            self.potential_evap = \
                xr.open_dataarray(out_path + 'pet_taylor.nc')
            self.precipitation = \
                xr.open_mfdataset(glob.glob(in_path), chunks={'time': 365})

        except FileNotFoundError:
            print("input file not found")
        else:
            self.benchmark_canopy_storage = \
                self.benchmark_canopy_storage[0].values
            self.daily_leaf_area_index = self.daily_leaf_area_index[0].values
            self.potential_evap = self.potential_evap[0].values
            # note 86400 is convertion factor
            self.precipitation = self.precipitation.pr[0].values * 86400

            self.canopy_storage_state = \
                np.zeros(self.benchmark_canopy_storage.shape)
            self.land_area_frac = lf.land_area_frac

    # Test if result are same as bechmark using same input as benchmark.
    def test_compare_storage_reults_and_dimensions(self):
        test_result = cs.\
            daily_canopy_storage(self.canopy_storage_state,
                                 self.daily_leaf_area_index,
                                 self.potential_evap,
                                 self.precipitation, self.land_area_frac)
        simulated_storage = test_result[0]
        np_test.assert_almost_equal(simulated_storage,
                                    self.benchmark_canopy_storage)
        # checking data dimensions
        spatial_dim = simulated_storage.shape
        self.assertEqual(spatial_dim, (360, 720))

    # Test results for acceptatable range for inputs
    def test_result_validity(self):
        # data in valid ranges
        daily_leaf_area_index = np.random.uniform(0, 4.78, size=(360, 720))
        potential_evap = np.random.uniform(0, 11, size=(360, 720))
        land_area_frac = np.random.uniform(0, 1, size=(360, 720))
        precipitation = np.random.uniform(0, 90, size=(360, 720))

        test_result = cs.\
            daily_canopy_storage(self.canopy_storage_state,
                                 daily_leaf_area_index, potential_evap,
                                 precipitation, land_area_frac)

        simulated_storage = test_result[0]
        self.assertTrue(np.all((simulated_storage >= 0) &
                               (simulated_storage <= 4.78)))

    # Test results for negative precipitation
    def test_with_negative_precipitation(self):

        daily_leaf_area_index = np.random.uniform(0, 4.78, size=(360, 720))
        potential_evap = np.random.uniform(0, 8, size=(360, 720))
        land_area_frac = np.random.uniform(0, 1, size=(360, 720))
        precipitation = np.random.uniform(-5, 90, size=(360, 720))

        with self.assertRaises(ValueError) as context:
            cs.daily_canopy_storage(self.canopy_storage_state,
                                    daily_leaf_area_index,
                                    potential_evap, precipitation,
                                    land_area_frac)
        msg = colored("There are negative values in the precipitation data.",
                      'red')
        self.assertEqual(str(context.exception), msg)
