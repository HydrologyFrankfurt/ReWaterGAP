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
import xarray as xr
import numpy as np
from model.verticalwaterbalance import soil as ss
from controller import configuration_module as cm


class TestSoil(unittest.TestCase):
    """Test soil module."""

    # creating fixtures
    def setUp(self):
        size = (360, 720)
        input_path = "./input_data/static_input/"
        self.soil_properties = {
            'soil_water_content_max': 100,  # mm  note that smax could reach 1752 
            'soil_water_content_min': 0,    # mm
            'soil_water_content': np.zeros(size),  # mm
            'texture': 
                xr.open_dataarray(input_path + "soil_storage/watergap_22e_texture.nc",
                                  decode_times=False).values,
        }
        self.precip_and_evap_data = {
            'max_temp_elev': np.random.uniform(273.15, 303.15, size=size),  # K
            "canopy_evap": np.random.uniform(0, 1.5, size=size),  # mm/day
            'pet_to_soil': np.random.uniform(0, 15, size=size),  # mm/day
            'sublimation': np.random.uniform(0, 500, size=size),  # mm/day
            'precipitation': np.random.uniform(0, 90, size=size),  # mm/day
            'effective_precipitation': np.random.uniform(0, 70, size=size), # mm/day
        }
        built_up_frac = \
            xr.open_dataarray(input_path + "soil_storage/watergap_22e_builtup_area_frac.nc4",
                              decode_times=False)
        self.immediate_runoff = (self.precip_and_evap_data['effective_precipitation'] * 0.5
                                 * built_up_frac[0].values) # mm/day
        self.precip_and_evap_data['effective_precipitation'] -= self.immediate_runoff  # mm/day

        self.land_data = {
            'current_land_area_frac': np.random.uniform(0, 1, size=size),  # -
            'landareafrac_ratio':
                np.random.uniform(0, 1, size=size)/np.random.uniform(0, 1, size=size),  # -
            'land_storage_change_sum': np.random.uniform(0, 100, size=size),  # mm
            'daily_storage_transfer': np.zeros(size)  # mm
        }

        # Load global parameters
        path_global_par = cm.global_parameter_path
        if path_global_par.startswith("model"):
            path_global_par = f"./{path_global_par}"
        global_parameters = xr.open_dataset(path_global_par,
                                            decode_times=False)
        self.global_parameters = {
            'snow_freeze_temp': global_parameters.snow_freeze_temp.values,  # K
            'gamma': global_parameters.gamma.values,  # -
            'max_daily_pet': global_parameters.max_daily_pet.values,  # mm/day
            'critcal_gw_precipitation': global_parameters.critcal_gw_precipitation.values, # mm/day
            'areal_corr_factor':global_parameters.areal_corr_factor.values # -
        }

        # Initialize static data for the model
        self.static_data = {
            # Load arid/humid classification data
            "humid_arid": xr.open_dataarray(
                input_path + "watergap_22e_aridhumid.nc4", decode_times=False
            )[0].values,

            # Load soil texture data
            "soil_texture": xr.open_dataarray(
                input_path + "soil_storage/watergap_22e_texture.nc",
                decode_times=False).values,

            # Load drainage direction data
            "drainage_direction": xr.open_dataarray(
                input_path + "soil_storage/watergap_22e_drainage_direction.nc",
                decode_times=False)[0].values,

            # Load and process maximum groundwater recharge data (convert to mm/day)
            "max_groundwater_recharge": xr.open_dataarray(
                input_path + "soil_storage/watergap_22e_max_recharge.nc4",
                decode_times=False)[0].values / 100,  # Originally in mm * 100, convert to mm/day

            # Load groundwater recharge factor
            "groundwater_recharge_factor": xr.open_dataarray(
                input_path + "soil_storage/watergap_22e_gw_factor_corr.nc4",
                decode_times=False)[0].values,

            # Load maximum soil water content
            "max_soil_water_content": xr.open_dataarray(
                "./test/smax.nc", decode_times=False).values,  # In mm

            # Define minimum storage volume
            "minstorage_volume": 1e-15  # In mm
        }

    # Test if results using acceptatable range for inputs
    def test_soil_storage_validity(self):
        """
        Test if soil storage is within a valid range.

        Returns
        -------
        None.
        """
        # Loop through the soil water content grid
        for x in range(self.soil_properties['soil_water_content'].shape[0]):
            for y in range(self.soil_properties['soil_water_content'].shape[1]):
                # Call soil_water_balance without prefixes
                test_result = ss.soil_water_balance(
                    self.soil_properties['soil_water_content'][x, y],
                    self.precip_and_evap_data['pet_to_soil'][x, y],
                    self.land_data['current_land_area_frac'][x, y],
                    self.land_data['landareafrac_ratio'][x, y],
                    self.precip_and_evap_data['max_temp_elev'][x, y],
                    self.precip_and_evap_data['canopy_evap'][x, y],
                    self.precip_and_evap_data['effective_precipitation'][x, y],
                    self.precip_and_evap_data['precipitation'][x, y],
                    self.immediate_runoff[x, y],
                    self.land_data['land_storage_change_sum'][x, y],
                    self.precip_and_evap_data['sublimation'][x, y],
                    self.land_data['daily_storage_transfer'][x, y],
                    self.global_parameters['snow_freeze_temp'][x, y],
                    self.global_parameters['gamma'][x, y],
                    self.global_parameters['max_daily_pet'][x, y],
                    self.static_data['humid_arid'][x, y],
                    self.static_data['soil_texture'][x, y],
                    self.static_data['drainage_direction'][x, y],
                    self.static_data['max_groundwater_recharge'][x, y],
                    self.static_data['groundwater_recharge_factor'][x, y],
                    self.global_parameters['critcal_gw_precipitation'][x, y],
                    self.static_data['max_soil_water_content'][x, y],
                    self.global_parameters['areal_corr_factor'][x, y],
                    self.static_data['minstorage_volume'],
                    x, y
                )

                # Update soil water content
                self.soil_properties['soil_water_content'][x, y] = test_result[0]

        # Assert that the soil water content is within the expected range
        self.assertTrue(
            (np.nanmin(self.soil_properties['soil_water_content']) >=
             self.soil_properties['soil_water_content_min']) &
            (np.nanmax(self.soil_properties['soil_water_content']) <=
             self.soil_properties['soil_water_content_max'])
        )
