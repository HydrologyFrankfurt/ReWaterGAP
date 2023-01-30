# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 14:37:44 2022

@author: nyenah
"""

import unittest
import xarray as xr
import numpy as np
import numpy.testing as np_test
from core.verticalwaterbalance import radiation_evapotranspiration as re
from test import climat_and_static_data as cs


class TestRadiationEvapotranspiration(unittest.TestCase):
    # creating fixtures
    def setUp(self):
        # setting up climate forcing and static data
        self.climate_forcing = cs.ClimateForcing()
        self.static_data = cs.StaticData()

        # selecting data for simulation
        self.date = np.datetime64('1901-01-01')

        # creating snow storage variable
        self.snow_water_storage = np.zeros((360, 720))

        # Benchmark data
        out_path = './output_data/'
        try:
            self.benchmark_net_radiation = \
                xr.open_dataarray(out_path + 'net_radiation.nc')

            self.benchmark_priestly_taylor = \
                xr.open_dataarray(out_path + 'pet_taylor.nc')
        except FileNotFoundError:
            print("input file not found")
        else:
            self.benchmark_net_radiation = \
                 self.benchmark_net_radiation[0].values

            self.benchmark_priestly_taylor =\
                self.benchmark_priestly_taylor[0].values

    def test_compare_radiation_reults_and_dimensions(self):
        test_result = re.\
            RadiationPotentialEvap(self.climate_forcing,
                                   self.static_data, self.date,
                                   self.snow_water_storage)

        simulated_net_radiation = test_result.net_radiation
        np_test.assert_almost_equal(simulated_net_radiation,
                                    self.benchmark_net_radiation,
                                    decimal=4)
        # checking data dimensions
        spatial_dim = simulated_net_radiation.shape
        self.assertEqual(spatial_dim, (360, 720))

    # Test if results using acceptatable range for inputs
    def test_radiation_result_validity(self):
        self.climate_forcing = cs.ClimateForcing(simulate=True)

        test_result = re.\
            RadiationPotentialEvap(self.climate_forcing,
                                   self.static_data, self.date,
                                   self.snow_water_storage)

        simulated_net_radiation = test_result.net_radiation

        # maximum and minimum range for radiation may change depending  on the
        # input range
        self.assertTrue((np.nanmax(simulated_net_radiation) >= -316) &
                        (np.nanmax(simulated_net_radiation) <= 400))

    def test_priestly_taylor_evap_and_dimensions(self):
        test_result = re.\
            RadiationPotentialEvap(self.climate_forcing,
                                   self.static_data, self.date,
                                   self.snow_water_storage)

        simulated_priestly_taylor = test_result.priestley_taylor()
        np_test.assert_almost_equal(simulated_priestly_taylor,
                                    self.benchmark_priestly_taylor,
                                    decimal=4)

        spatial_dim = simulated_priestly_taylor.shape
        self.assertEqual(spatial_dim, (360, 720))

    # Test if results using acceptatable range for inputs
    def test_priestly_taylor_evap_result_validity(self):
        self.climate_forcing = cs.ClimateForcing(simulate=True)

        test_result = re.\
            RadiationPotentialEvap(self.climate_forcing,
                                   self.static_data, self.date,
                                   self.snow_water_storage)
        simulated_priestly_taylor = test_result.priestley_taylor()

        self.assertTrue((np.nanmin(simulated_priestly_taylor) >= 0) &
                        (np.nanmax(simulated_priestly_taylor) <= 12))
