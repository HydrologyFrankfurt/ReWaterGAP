# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 17:56:53 2022

@author: nyenah
"""
import unittest
from termcolor import colored
import xarray as xr
import numpy as np
import numpy.testing as np_test
from core.verticalwaterbalance import soil_storage as ss
from test import climat_and_static_data as cs
from test.land_water_fractions import _landfrac as lf


class TestSoil(unittest.TestCase):
    # creating fixtures
    def setUp(self):
        # setting up climate forcing and static data
        self.climate_forcing = cs.ClimateForcing()
        self.static_data = cs.StaticData()

        # initializing storage and helper varaibles
        self.soil_water_content = np.zeros((360, 720))

        # Benchmark and intermediate data
        out_path = './output_data/'
        out_extra = './test/out_for_test/'
        try:
            # Benchmark data
            self.benchmark_soil_storage = \
                xr.open_dataarray(out_path + 'soil_water_storage.nc')

            self.pet_to_soil = xr.open_dataarray(out_extra + 'pet_to_soil.nc')
            self.land_storage_change_sum = \
                xr.open_dataarray(out_extra + 'land_change_sum.nc')
            self.canopy_evap = xr.open_dataarray(out_path + 'canopy_evap.nc')
            self.max_temp_elev = \
                xr.open_dataarray(out_extra + 'max_temp_elev.nc')
            self.effective_precipitation = \
                xr.open_dataarray(out_extra + 'effective_precipitation.nc')
            self.sublimation = xr.open_dataarray(out_path + 'sublimation.nc')

        except FileNotFoundError:
            print("input file not found")
        else:
            self.benchmark_soil_storage = \
                  self.benchmark_soil_storage[0].values

            self.pet_to_soil = self.pet_to_soil[0].values
            self.land_storage_change_sum = \
                self.land_storage_change_sum[0].values

            self.canopy_evap = self.canopy_evap[0].values
            self.max_temp_elev = self.max_temp_elev[0].values
            self.effective_precipitation = \
                self.effective_precipitation[0].values
            self.sublimation = self.sublimation[0].values

    def test_compare_soil_storage_reults_and_dimensions(self):
        precipitation = self.climate_forcing.precipitation.pr[0].values * 86400

        # initialize soil storage
        initilaize_soil_storage = ss.SoilStorage(self.static_data)

        # Modified effective precipitation and immediate runoff
        modified_effective_precipitation = \
            initilaize_soil_storage.immediate_runoff(self.effective_precipitation)

        # ouputs from the  modified_effective_precipitation are
        # 0 = effective_precipitation,  1 =  immediate_runoff
        effective_precipitation_corr = modified_effective_precipitation[0]
        immediate_runoff = modified_effective_precipitation[1]

        # Running daily soil storage.
        simulated_result = initilaize_soil_storage.\
            daily_soil_storage(self.soil_water_content, self.pet_to_soil,
                               lf.land_area_frac, self.max_temp_elev,
                               self.canopy_evap, effective_precipitation_corr,
                               precipitation, immediate_runoff,
                               self.land_storage_change_sum, self.sublimation)

        simulated_soil_storage = simulated_result[0]

        np_test.assert_almost_equal(simulated_soil_storage,
                                    self.benchmark_soil_storage,
                                    decimal=0)
        # checking data dimensions
        spatial_dim = simulated_soil_storage.shape
        self.assertEqual(spatial_dim, (360, 720))

    # Test if results using acceptatable range for inputs
    def test_snow_water_equiv_result_validity(self):
        self.climate_forcing = cs.ClimateForcing(simulate=True)
        precipitation = self.climate_forcing.precipitation.pr[0].values * 86400

        # initialize soil storage
        initilaize_soil_storage = ss.SoilStorage(self.static_data)

        # Modified effective precipitation and immediate runoff
        modified_effective_precipitation = \
            initilaize_soil_storage.immediate_runoff(self.effective_precipitation)

        # ouputs from the  modified_effective_precipitation are
        # 0 = effective_precipitation,  1 =  immediate_runoff
        effective_precipitation_corr = modified_effective_precipitation[0]
        immediate_runoff = modified_effective_precipitation[1]

        # other simulated input
        pet_to_soil = np.random.uniform(0, 11.5, size=(360, 720))
        max_temp_elev = np.random.uniform(214, 310, size=(360, 720))
        canopy_evap = np.random.uniform(0, 4.78, size=(360, 720))
        land_storage_change_sum = np.random.uniform(0, 180, size=(360, 720))
        sublimation = np.random.uniform(0, 8, size=(360, 720))

        # Running daily soil storage.
        simulated_result = initilaize_soil_storage.\
            daily_soil_storage(self.soil_water_content, pet_to_soil,
                               lf.land_area_frac, max_temp_elev,
                               canopy_evap, effective_precipitation_corr,
                               precipitation, immediate_runoff,
                               land_storage_change_sum, sublimation)

        simulated_soil_storage = simulated_result[0]

        self.assertTrue((np.nanmin(simulated_soil_storage) >= 0) &
                        (np.nanmax(simulated_soil_storage) <= 1100))

    def test_with_negative_precipitation(self):
        self.climate_forcing = cs.ClimateForcing(simulate=True, neg_prec=True)
        precipitation = self.climate_forcing.precipitation.pr[0].values * 86400

        # initialize soil storage
        initilaize_soil_storage = ss.SoilStorage(self.static_data)

        # Modified effective precipitation and immediate runoff
        modified_effective_precipitation = \
            initilaize_soil_storage.immediate_runoff(self.effective_precipitation)

        # ouputs from the  modified_effective_precipitation are
        # 0 = effective_precipitation,  1 =  immediate_runoff
        effective_precipitation_corr = modified_effective_precipitation[0]
        immediate_runoff = modified_effective_precipitation[1]

        # other simulated input
        pet_to_soil = np.random.uniform(0, 11.5, size=(360, 720))
        max_temp_elev = np.random.uniform(214, 310, size=(360, 720))
        canopy_evap = np.random.uniform(0, 4.78, size=(360, 720))
        land_storage_change_sum = np.random.uniform(0, 180, size=(360, 720))
        sublimation = np.random.uniform(0, 8, size=(360, 720))

        with self.assertRaises(ValueError) as context:
            initilaize_soil_storage.\
                daily_soil_storage(self.soil_water_content, pet_to_soil,
                                   lf.land_area_frac, max_temp_elev,
                                   canopy_evap, effective_precipitation_corr,
                                   precipitation, immediate_runoff,
                                   land_storage_change_sum, sublimation)

        msg = colored("There are negative values in the precipitation data.",
                      'red')
        self.assertEqual(str(context.exception), msg)
