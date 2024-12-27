# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Test Resevoir and Regulated lake module."""


import unittest
import xarray as xr
import numpy as np
import pandas as pd
from model.lateralwaterbalance import reservoir_regulated_lakes as res_reg


class TestResevoirRegulatedLake(unittest.TestCase):
    """Test Resevoir and Regulated lake module."""

    # creating fixtures
    def setUp(self):
        input_path = "./input_data/static_input/reservoir_regulated_lake/"
        land_frac_path = "./input_data/static_input/land_water_fractions/"
        self.constants ={
            'size': (360, 720),
            'resyear': 2000,
            'minstorage_volume': 1e-15, # km3
            'm_to_km': 0.001,
            'year_to_s': 31536000,
            'm3_to_km3': 1e9,
            'num_days_in_month': 31,
            'glores_storage_max': 205, # km3
            'glores_storage_min': 0} # km3}

        self.constants['simu_start_year'] = self.constants['resyear']

        self.climate_and_static_data = {
            'precipitation': np.random.uniform(0, 3, size=self.constants['size']),  # km3/day
            'openwater_pot_evap':
                np.random.uniform(0, 0.05, size=self.constants['size']),  # km3/day
            'aridhumid': xr.open_dataarray("./input_data/static_input/watergap_22e_aridhumid.nc4",
                                           decode_times=False)[0].values,
            'drainage_direction':
                xr.open_dataarray("./input_data/static_input/soil_storage/"
                                  "watergap_22e_drainage_direction.nc", 
                                  decode_times=False)[0].values
        }

        global_parameters = \
            xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc",
                            decode_times=False)
        self.global_params = {
            'gw_dis_coeff': global_parameters.gw_dis_coeff.values,  # 1/day
            'swb_outflow_coeff': global_parameters.swb_outflow_coeff.values,  # 1/day
            'gw_recharge_constant': global_parameters.gw_recharge_constant.values,  # m/day
            'reduction_exponent_res': global_parameters.reduction_exponent_res.values,  # -
            'areal_corr_factor': global_parameters.areal_corr_factor.values,  # -
            'activelake_depth': global_parameters.activelake_depth.values  # m
        }

        self.glolake_storage = 0
        self.mask_mean_annual_inflow = 0

        self.reservoir_data = {
            'all_reservoir_and_regulated_lake_area':
                xr.open_dataarray(f"{land_frac_path}watergap_22e_reservoir_"
                                  "and_regulated_lake_area.nc",
                                  decode_times=False)[0].values,  # km2

            'inflow_to_swb_res':
                np.random.uniform(0, 15, size=self.constants['size']),  # km3/day plausible

            'monthly_potential_net_abstraction_sw':
                np.random.uniform(0, 0.2, size=self.constants['size']),  # km3/month plausible

            'mean_annual_demand_res':
                xr.open_dataarray(f"{input_path}watergap_22e_mean_nus_1971_2000.nc4",
                                  decode_times=False)[0].values,  # m3/year
            'accumulated_unsatisfied_potential_netabs_sw':
                np.random.uniform(0, 0.02, size=self.constants['size']),  # km3/day plausible
            'accu_unsatisfied_pot_netabstr_glolake':
                np.random.uniform(0, 0.001, size=self.constants['size']),  # km3/day plausible
            'current_mon_day': np.array([1, 1]),  # 1st day and month    
            'k_release': np.zeros(self.constants['size']) + 0.1,  # (-)

            # Reservoir Area and Capacity
            'glores_startyear': xr.open_dataarray(f"{input_path}watergap_22e_startyear.nc4",
                                                  decode_times=False)[0].values,  # year
            'glores_startmonth': xr.open_dataarray(f"{input_path}watergap_22e_startmonth.nc4",
                                                   decode_times=False)[0].values,  # month
            'glores_capacity': xr.open_dataarray(f"{input_path}watergap_22e_res_stor_cap.nc4",
                                                 decode_times=False)[0].values,  # km3
            'glores_type': xr.open_dataarray(f"{input_path}watergap_22e_reservoir_type.nc4",
                                             decode_times=False)[0].values,  # -
            # mean_annual_inflow_res m3/s,
            'mean_annual_inflow_res':
                xr.open_dataarray(f"{input_path}watergap_22e_mean_inflow.nc4",
                                  decode_times=False)[0].values *
                (12 * 1e9 / self.constants["year_to_s"]),


            'glolake_area': 
                xr.open_dataarray(f"{land_frac_path}watergap_22e_global_lake_area.nc",
                                  decode_times=False)[0].values,  # km2
            'regulated_lake_status':
                xr.open_dataarray(f"{land_frac_path}watergap_22e_regulated_lake_status.nc",
                                  decode_times=False).values,  # -
        }

        rout_order_all = pd.read_csv("./input_data/static_input/routing_order.csv")
        alloc_coeff = pd.read_csv("./input_data/static_input/alloc_coeff_by_routorder.csv")
        self.reservoir_data["rout_order"] = \
            rout_order_all[['Lat_index_routorder', 'Lon_index_routorder']].to_numpy()
        self.reservoir_data["outflow_cell"] =\
            rout_order_all[['Lat_index_outflowcell', 'Lon_index_outflowcell']].to_numpy()
        self.reservoir_data["allocation_coeff"] =\
            alloc_coeff[alloc_coeff.columns[-5:]].to_numpy()

    # Test if results using acceptatable range for inputs
    def test_reservoir_regulated_lake_storage_validity(self):
        """Test if reservoir & reg. lake storage is within a valid range."""

        # Initialize newly activated reservior area, Units : km2
        # Keep area values of already activate reservoirs
        glores_area = np.where(self.constants['resyear'] >=
                               self.reservoir_data['glores_startyear'],
                               self.reservoir_data['all_reservoir_and_regulated_lake_area'],
                               0)

        # Initialize newly activated global reservior capacity,
        # Units : km3, Keep capacity values of already activate
        # reservoirs
        glores_capacity = \
            np.where(self.constants['resyear'] >=
                     self.reservoir_data['glores_startyear'],
                     self.reservoir_data['glores_capacity'], 0)

        # ------------------------------------------------------
        # Reservoir area is added to global lake if
        # mean_annual_inflow_res = 0. reservoir area has to be set
        #  to zero after.
        # ------------------------------------------------------

        self.mask_mean_annual_inflow = \
            ((glores_area > 0)
             & (self.constants['resyear'] >= self.reservoir_data['glores_startyear'])
             & (self.reservoir_data['mean_annual_inflow_res'] == 0))

        glolake_area =\
            np.where(self.mask_mean_annual_inflow,
                     glores_area + self.reservoir_data['glolake_area'],
                     self.reservoir_data['glolake_area'])

        glores_area[self.mask_mean_annual_inflow] = 0
        self.reservoir_data['all_reservoir_and_regulated_lake_area']\
            [self.mask_mean_annual_inflow] = 0

        max_glolake_storage = glolake_area * self.global_params['activelake_depth'] * \
            self.constants["m_to_km"]

        # -----------------
        # Reservoir Storage
        # -----------------
        # # Initialize newly activated reservior storage in
        # the current year to maximum,  Units : km3
        # Keep storage values of already activate reservoirs

        glores_storage = \
            np.where(self.constants['simu_start_year'] >=
                     self.reservoir_data['glores_startyear'],
                     self.reservoir_data['glores_capacity'], 0)

        # -------------------------
        # Regulated Lake Storage
        # -----------------------
        # For regulated lake: if it's not yet operational
        # increase reservoir storage by multiplying the area with
        # lake depth (Treat it as a global lake)- changed by mohammed
        glores_storage =\
            np.where((self.constants['simu_start_year'] <
                      self.reservoir_data['glores_startyear']) &
                     (self.reservoir_data['regulated_lake_status'] == 1),
                     (self.reservoir_data['all_reservoir_and_regulated_lake_area'] *
                      self.global_params['activelake_depth'] *
                      self.constants["m_to_km"])
                     + glores_storage,
                     glores_storage)

        reg_lake_redfactor_firstday = \
            np.where((self.constants['simu_start_year'] <
                      self.reservoir_data['glores_startyear']) &
                     (self.reservoir_data['regulated_lake_status'] == 1), 1,
                     0)

        reg_lake_redfactor_firstday = \
            np.where((glores_storage == glores_capacity) &
                     (self.reservoir_data['regulated_lake_status'] == 1), 0,
                     reg_lake_redfactor_firstday)

        # update initial storage of global lake if reservoir
        # becomes global lake due to mean_annual_inflow_res = 0.
        self.glolake_storage = max_glolake_storage

        for routflow_looper in enumerate(self.reservoir_data["rout_order"]):
            routflow_looper = routflow_looper[0]  #  take index only
            # Get invidividual cells based on routing order
            x, y = self.reservoir_data["rout_order"][routflow_looper]

            if glores_area[x, y] > 0:
                test_result = res_reg.\
                    reservoir_regulated_lake_water_balance(
                     self.reservoir_data["rout_order"], routflow_looper,
                     self.reservoir_data["outflow_cell"],
                     glores_storage[x, y],
                     glores_capacity[x, y],
                     self.climate_and_static_data["precipitation"][x, y],
                     self.climate_and_static_data["openwater_pot_evap"][x, y],
                     self.climate_and_static_data["aridhumid"][x, y],
                     self.climate_and_static_data["drainage_direction"][x, y],
                     self.reservoir_data["inflow_to_swb_res"][x, y],
                     self.global_params["gw_recharge_constant"][x, y],
                     glores_area,
                     self.global_params["reduction_exponent_res"][x, y],
                     self.global_params["areal_corr_factor"][x, y],
                     self.reservoir_data["glores_startmonth"][x, y],
                     self.reservoir_data["current_mon_day"],
                     self.reservoir_data["k_release"][x, y],
                     self.reservoir_data["glores_type"][x, y],
                     self.reservoir_data["allocation_coeff"],
                     self.reservoir_data["monthly_potential_net_abstraction_sw"],
                     self.reservoir_data["mean_annual_demand_res"],
                     self.reservoir_data["mean_annual_inflow_res"][x, y],
                     glolake_area[x, y],
                     self.reservoir_data["accumulated_unsatisfied_potential_netabs_sw"][x, y],
                     self.reservoir_data["accu_unsatisfied_pot_netabstr_glolake"][x, y],
                     self.constants["num_days_in_month"],
                     self.reservoir_data["all_reservoir_and_regulated_lake_area"],
                     reg_lake_redfactor_firstday[x, y],
                     self.constants["minstorage_volume"])

                glores_storage[x, y] = test_result[0]
        self.assertTrue((np.nanmin(glores_storage) >= self.constants["glores_storage_min"]) &
                        (np.nanmax(glores_storage) <= self.constants["glores_storage_max"]))

        # Check the condition: if mask_mean_annual_inflow is True, glolake_storage must be > 0
        # Hence global lake storage must be updated since  reservoir area is added to global lake if
        # mean_annual_inflow_res = 0.
        zero_indices = np.where(self.mask_mean_annual_inflow == 1)

        values_at_indices = self.glolake_storage[zero_indices]

        grt_zero = np.any(values_at_indices > 0)
        self.assertTrue(grt_zero == 1)
