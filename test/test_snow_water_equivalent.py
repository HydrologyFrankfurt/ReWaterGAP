# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 14:37:44 2022.

@author: nyenah
"""

import unittest
from termcolor import colored
import xarray as xr
import numpy as np
import numpy.testing as np_test
from core.verticalwaterbalance import snow_water_equivalent as swe
from test import climat_and_static_data as cs
from test.land_water_fractions import _landfrac as lf


class TestSnowWaterEquivalent(unittest.TestCase):
    # creating fixtures
    def setUp(self):
        # setting up climate forcing and static data
        self.climate_forcing = cs.ClimateForcing()
        self.static_data = cs.StaticData()

        # initializing storage and helper varaibles
        self.snow_water_storage = np.zeros((360, 720))
        self.snow_water_storage_subgrid = np.zeros((100, 360, 720))
        self.thresh_elev = np.zeros((360, 720))
        self.thresh_elev = self.thresh_elev
        # Benchmark and intermediate data
        out_path = './output_data/'
        out_extra = './test/out_for_test/'

        try:
            # Benchmark data
            self.benchmark_snow_water_equivalent = \
                xr.open_dataarray(out_path + 'snow_water_storage.nc')

            self.throughfall = xr.open_dataarray(out_path + 'throughfall.nc')
            self.pet_to_soil = xr.open_dataarray(out_extra + 'pet_to_soil.nc')
            self.land_storage_change_sum = \
                xr.open_dataarray(out_extra + 'land_change_sum.nc')

        except FileNotFoundError:
            print("input file not found")
        else:
            self.benchmark_snow_water_equivalent = \
                  self.benchmark_snow_water_equivalent[0].values

            self.throughfall = self.throughfall[0].values
            self.pet_to_soil = self.pet_to_soil[0].values
            self.land_storage_change_sum = \
                self.land_storage_change_sum[0].values

    def test_compare_snow_water_equiv_reults_and_dimensions(self):
        precipitation = self.climate_forcing.precipitation.pr[0].values * 86400
        temperature = self.climate_forcing.temperature.tas[0].values

        test_result = swe.Snow(self.static_data, precipitation)

        simulated_result = \
            test_result.cal_snow(lf.land_area_frac, temperature,
                                 self.throughfall, self.snow_water_storage,
                                 self.pet_to_soil,
                                 self.land_storage_change_sum,
                                 self.snow_water_storage_subgrid)

        simulated_snow_water_storage = simulated_result[0]

        np_test.assert_almost_equal(simulated_snow_water_storage,
                                    self.benchmark_snow_water_equivalent,
                                    decimal=0)
        # checking data dimensions
        spatial_dim = simulated_snow_water_storage.shape
        self.assertEqual(spatial_dim, (360, 720))

    # Test if results using acceptatable range for inputs
    def test_snow_water_equiv_result_validity(self):
        self.climate_forcing = cs.ClimateForcing(simulate=True)
        precipitation = self.climate_forcing.precipitation.pr[0].values * 86400
        temperature = self.climate_forcing.temperature.tas[0].values
        throughfall = np.random.uniform(0, 90, size=(360, 720))
        pet_to_soil = np.random.uniform(0, 11.5, size=(360, 720))
        land_storage_change_sum = np.random.uniform(0, 180, size=(360, 720))

        test_result = swe.Snow(self.static_data, precipitation)

        simulated_result = \
            test_result.cal_snow(lf.land_area_frac, temperature, throughfall,
                                 self.snow_water_storage, pet_to_soil,
                                 land_storage_change_sum,
                                 self.snow_water_storage_subgrid)

        simulated_snow_water_storage = simulated_result[0]

        self.assertTrue((np.nanmin(simulated_snow_water_storage) >= 0) &
                        (np.nanmax(simulated_snow_water_storage) <= 1000))

    def test_with_negative_precipitation(self):
        self.climate_forcing = cs.ClimateForcing(simulate=True, neg_prec=True)
        precipitation = self.climate_forcing.precipitation.pr[0].values * 86400

        with self.assertRaises(ValueError) as context:
            swe.Snow(self.static_data, precipitation)

        msg = colored("There are negative values in the precipitation data.",
                      'red')
        self.assertEqual(str(context.exception), msg)
