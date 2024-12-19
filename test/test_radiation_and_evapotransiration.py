# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 14:37:44 2022

@author: nyenah
"""

import unittest
import xarray as xr
import numpy as np
from model.verticalwaterbalance import radiation_evapotranspiration as re

class TestRadiationEvapotranspiration(unittest.TestCase):
    # creating fixtures
    def setUp(self):
        # Pet max value is taking from
        # https://ntrs.nasa.gov/api/citations/20190034158/downloads/20190034158.pdf
        # similar values are found 
        # https://github.com/HydrologyFrankfurt/WaterGAP-main/issues/246: 
        # (note that some values here are per month)

        self.pet_max = 15 # mm
        self.pet_min = 0  # mm
        self.size = (360, 720)

        self.pet = np.zeros(self.size)
        self.temperature = np.random.uniform(273.15, 303.15, size=self.size)  # K
        pt_coeff = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc", decode_times=False)
        self.pt_coeff_humid_arid = pt_coeff.pt_coeff_humid_arid.values  # -
        self.net_radiation = np.random.uniform(0, 300, size=self.size)  # Wm-2  could be negative but we set it to zero 
        self.openwater_net_radiation = np.random.uniform(0, 300, size=self.size)  # Wm-2  could be negative but we set it to zero 

    # Test if results using acceptatable range for inputs
    def test_priestly_taylor_evap_result_validity(self):
        for x in range(self.pet.shape[0]):
            for y in range(self.pet.shape[1]):
                test_result = re.priestley_taylor_pet(self.temperature[x, y], self.pt_coeff_humid_arid[x, y],
                                                      self.net_radiation[x, y], self.openwater_net_radiation[x, y],
                                                      x, y)
                self.pet[x, y] = test_result[0]
        self.assertTrue((np.nanmin(self.pet) >= self.pet_min) &
                        (np.nanmax(self.pet) <= self.pet_max))
