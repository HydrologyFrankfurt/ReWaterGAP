# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test radiation and evapotranspiration module."""

import unittest
import xarray as xr
import numpy as np
from model.verticalwaterbalance import radiation_evapotranspiration as re


class TestRadiationEvapotranspiration(unittest.TestCase):
    """Test Priestly-Talor PET function."""

    # creating fixtures
    def setUp(self):
        # Pet max value is taking from
        # https://github.com/HydrologyFrankfurt/WaterGAP-main/issues/246:
        # (note that values here are monthly hence  daily equivalent is computed )
        # similar daily values are found also here
        # https://ntrs.nasa.gov/api/citations/20190034158/downloads/20190034158.pdf

        self.pet_max = 15 # mm
        self.pet_min = 0  # mm
        size = (360, 720)

        self.pet = np.zeros(size)
        self.temperature = np.random.uniform(273.15, 303.15, size=size)  # K
        pt_coeff = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc", decode_times=False)
        self.pt_coeff_humid_arid = pt_coeff.pt_coeff_humid_arid.values  # -

        # (open water)net radiation and could be negative but we set it to zero
        self.net_radiation = np.random.uniform(0, 300, size=size)  # Wm-
        self.openwater_net_radiation = np.random.uniform(0, 300, size=size)  # Wm-2

    # Test if results using acceptatable range for inputs
    def test_priestly_taylor_evap_result_validity(self):
        """
        check Priestly-Talor PET output against valid ranges.

        Returns
        -------
        None.

        """
        for x in range(self.pet.shape[0]):
            for y in range(self.pet.shape[1]):
                test_result = re.priestley_taylor_pet(self.temperature[x, y],
                                                      self.pt_coeff_humid_arid[x, y],
                                                      self.net_radiation[x, y],
                                                      self.openwater_net_radiation[x, y],
                                                      x, y)
                self.pet[x, y] = test_result[0]
        self.assertTrue((np.nanmin(self.pet) >= self.pet_min) &
                        (np.nanmax(self.pet) <= self.pet_max))
