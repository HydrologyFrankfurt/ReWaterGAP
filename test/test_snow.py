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
    # creating fixtures
    def setUp(self):
        # swe daily maximum  is 1000 in a sub cell(see,
        # https://gmd.copernicus.org/articles/14/1037/2021/#section4)
        # hence max swe in a 0.5 could be 1000mm
        self.snow_water_storage_max = 1000  # mm
        self.snow_water_storage_min = 0  # mm
        self.size = (360, 720)
        self.temperature = np.random.uniform(273.15, 303.15, size=self.size)  # K
        self.precipitation = np.random.uniform(0, 90, size=self.size)  # mm/day
        self.throughfall = np.random.uniform(0, 88.5, size=self.size)  # mm/day
        self.pet_to_soil = np.random.uniform(0, 15, size=self.size)  # mm/day
        self.land_storage_change_sum = np.random.uniform(0, 1.5, size=self.size)  # mm

        # Degree day factor mm/(day * °c)  D(T-Tm) (since delta T in K or celcius is the same there
        # is no need to change anything here )
        self.degreeday = np.zeros(self.size)
        parameters_snow = pd.read_csv("./input_data/static_input/canopy_snow_parameters.csv")
        self.land_cover = xr.open_dataarray("./input_data/static_input/watergap_22e_landcover.nc4", decode_times=False)
        self.land_cover = self.land_cover[0].values
        for i in range(len(parameters_snow)):
            self.degreeday[self.land_cover[:, :] == parameters_snow.loc[i, 'Number']] = \
               parameters_snow.loc[i, 'degree-day']
 
        self.current_land_area_frac = np.random.uniform(0, 1, size=self.size)  # -
        self.prev_land_area_frac = np.random.uniform(0, 1, size=self.size)  # -
        self.landareafrac_ratio = self.prev_land_area_frac/self.current_land_area_frac # -
        self.elevation = xr.open_dataarray("./input_data/static_input/watergap_22e_elevrange.nc4", decode_times=False) # m
        self.elevation = self.elevation.values
        self.daily_storage_transfer = np.zeros(self.size) # mm

        global_parameters = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc", decode_times=False)
        self.adiabatic_lapse_rate = global_parameters.adiabatic_lapse_rate.values #K/m 
        self.snow_freeze_temp = global_parameters.snow_freeze_temp.values # K
        self.snow_melt_temp = global_parameters.snow_melt_temp.values # K
        self.minstorage_volume = 1e-15 # mm

        # Snow water storage divided into 100 subgrids based on GTOPO30 (U.S.
        # Geological Survey, 1996) land surface elevation map, Units: mm
        elev_size = self.elevation[1:].shape
        self.snow_water_storage_subgrid = np.zeros(elev_size) # mm
        self.snow_water_storage = np.zeros(self.size) # mm

    # Test if results using acceptatable range for inputs
    def test_snow_water_equiv_validity(self):
        for x in range(self.snow_water_storage.shape[0]):
            for y in range(self.snow_water_storage.shape[1]):
                test_result = swe.\
                    snow_water_balance(self.snow_water_storage[x, y],
                                       self.snow_water_storage_subgrid[:, x, y],
                                       self.temperature[x, y], self.precipitation[x, y],
                                       self.throughfall[x, y], self.pet_to_soil[x, y],
                                       self.land_storage_change_sum[x, y], self.degreeday[x, y],
                                       self.current_land_area_frac[x, y], self.landareafrac_ratio[x, y],
                                       self.elevation[:, x, y], self.daily_storage_transfer[x, y],
                                       self.adiabatic_lapse_rate[x, y],  self.snow_freeze_temp[x, y],
                                       self.snow_melt_temp[x, y], self.minstorage_volume, x, y)

                self.snow_water_storage[x, y] = test_result[0]
        self.assertTrue((np.nanmin(self.snow_water_storage) >= self.snow_water_storage_min) &
                        (np.nanmax(self.snow_water_storage) <= self.snow_water_storage_max))


