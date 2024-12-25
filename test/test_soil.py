# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test soil module."""


import unittest
from termcolor import colored
import xarray as xr
import numpy as np
import numpy.testing as np_test
from model.verticalwaterbalance import soil as ss


class TestSoil(unittest.TestCase):
    # creating fixtures
    def setUp(self):

        self.soil_water_content_max = 100  # mm  note that smax could reach 1752 
        self.soil_water_content_min = 0  # mm
        self.size = (360, 720)

        self.soil_water_content = np.zeros(self.size) # mm
        self.pet_to_soil = np.random.uniform(0, 15, size=self.size)  # mm/day
        self.current_land_area_frac = np.random.uniform(0, 1, size=self.size)  # -
        self.prev_land_area_frac = np.random.uniform(0, 1, size=self.size)  # -
        self.landareafrac_ratio = self.prev_land_area_frac/self.current_land_area_frac # -
        self.max_temp_elev = np.random.uniform(273.15, 303.15, size=self.size)  # K
        self.canopy_evap = np.random.uniform(0, 1.5, size=self.size)  # mm/day
        self.precipitation = np.random.uniform(0, 90, size=self.size) # mm/day

        built_up_frac = xr.open_dataarray("./input_data/static_input/soil_storage/watergap_22e_builtup_area_frac.nc4", decode_times=False)
        self.effective_precipitation = np.random.uniform(0, 70, size=self.size) # mm/day 
        self.immediate_runoff = self.effective_precipitation * 0.5 * built_up_frac[0].values # mm/day 
    
        self.effective_precipitation -= self.immediate_runoff  # mm/day 

        self.land_storage_change_sum = np.random.uniform(0, 100, size=self.size)  # mm
        self.sublimation = np.random.uniform(0, 500, size=self.size)  # mm/day
        self.daily_storage_transfer = np.zeros(self.size)  # mm

        global_parameters = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc", decode_times=False)
        self.snow_freeze_temp = global_parameters.snow_freeze_temp.values # K
        self.gamma = global_parameters.gamma.values  # -
        self.max_daily_pet = global_parameters.max_daily_pet.values # mm/day
        self.critcal_gw_precipitation = global_parameters.critcal_gw_precipitation.values # mm/day
        self.areal_corr_factor = global_parameters.areal_corr_factor.values # -

        self.humid_arid = xr.open_dataarray("./input_data/static_input/watergap_22e_aridhumid.nc4", decode_times=False)[0].values
        self.soil_texture = xr.open_dataarray("./input_data/static_input/soil_storage/watergap_22e_texture.nc", decode_times=False).values
        self.drainage_direction = xr.open_dataarray("./input_data/static_input/soil_storage/watergap_22e_drainage_direction.nc", decode_times=False)[0].values
        self.max_groundwater_recharge = xr.open_dataarray("./input_data/static_input/soil_storage/watergap_22e_max_recharge.nc4", decode_times=False)[0].values #  mm *100
        self.max_groundwater_recharge /= 100 # mm/day
        self.groundwater_recharge_factor = xr.open_dataarray("./input_data/static_input/soil_storage/watergap_22e_gw_factor_corr.nc4", decode_times=False)[0].values
        self.max_soil_water_content = xr.open_dataarray("./test/smax.nc", decode_times=False).values # mm
        self.minstorage_volume = 1e-15 # mm

    

    # Test if results using acceptatable range for inputs
    def test_soil_storage_validity(self):
        for x in range(self.soil_water_content.shape[0]):
            for y in range(self.soil_water_content.shape[1]):
                test_result = ss.\
                    soil_water_balance(self.soil_water_content[x, y], self.pet_to_soil[x, y],
                                       self.current_land_area_frac[x, y],
                                       self.landareafrac_ratio[x, y],
                                       self.max_temp_elev[x, y], self.canopy_evap[x, y],
                                       self.effective_precipitation[x, y],
                                       self.precipitation[x, y],
                                       self.immediate_runoff[x, y],
                                       self.land_storage_change_sum[x, y],
                                       self.sublimation[x, y],
                                       self.daily_storage_transfer[x, y],
                                       self.snow_freeze_temp[x, y],
                                       self.gamma[x, y], self.max_daily_pet[x, y], self.humid_arid[x, y],
                                       self.soil_texture[x, y], self.drainage_direction[x, y],
                                       self.max_groundwater_recharge[x, y],
                                       self.groundwater_recharge_factor[x, y],
                                       self.critcal_gw_precipitation[x, y],
                                       self.max_soil_water_content[x, y],
                                       self.areal_corr_factor[x, y],
                                       self.minstorage_volume, x, y)

            self.soil_water_content[x, y] = test_result[0]

        self.assertTrue((np.nanmin(self.soil_water_content) >= self.soil_water_content_min) &
                (np.nanmax(self.soil_water_content) <= self.soil_water_content_max))