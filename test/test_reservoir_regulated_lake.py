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
    # creating fixtures
    def setUp(self):

        self.size = (360, 720)
        self.precipitation = np.random.uniform(0, 3, size=self.size)  # km3/day
        self.openwater_pot_evap = np.random.uniform(0, 0.05, size=self.size)  # km3/day
        self.aridhumid = xr.open_dataarray("./input_data/static_input/watergap_22e_aridhumid.nc4", decode_times=False)[0].values
        self.drainage_direction = xr.open_dataarray("./input_data/static_input/soil_storage/watergap_22e_drainage_direction.nc", decode_times=False)[0].values

        global_parameters = xr.open_dataset("./model/WaterGAP_2.2e_global_parameters.nc", decode_times=False)
        self. gw_dis_coeff = global_parameters.gw_dis_coeff.values  # 1/day
        self.swb_outflow_coeff = global_parameters.swb_outflow_coeff.values  # 1/day
        self.gw_recharge_constant = global_parameters.gw_recharge_constant.values  # m/day
        self.reduction_exponent_res = global_parameters.reduction_exponent_res.values  # -
        self.areal_corr_factor = global_parameters.areal_corr_factor.values  # -
        self.activelake_depth = global_parameters.activelake_depth.values  # m


    # Test if results using acceptatable range for inputs
    def test_reservoir_regulated_lake_storage_validity(self):
        # ====================================
        resyear = 2000
        simu_start_year = resyear
        minstorage_volume = 1e-15 # km3
        m_to_km = 0.001
        year_to_s = 31536000
        m3_to_km3 = 1e9
        # ====================================
        
        glores_storage_max = 205  # km3
        glores_storage_min = 0 # km3
        all_reservoir_and_regulated_lake_area = xr.open_dataarray("./input_data/static_input/land_water_fractions/watergap_22e_reservoir_and_regulated_lake_area.nc", decode_times=False)[0].values  # km2
        inflow_to_swb_res = np.random.uniform(0, 15, size=self.size)  # km3/day plausible 
        monthly_potential_net_abstraction_sw =  np.random.uniform(0, 0.2, size=self.size)  # km3/month plausible 
        mean_annual_demand_res = xr.open_dataarray("./input_data/static_input/reservoir_regulated_lake/watergap_22e_mean_nus_1971_2000.nc4", decode_times=False)[0].values  #m3/year
        accumulated_unsatisfied_potential_netabs_sw = np.random.uniform(0, 0.02, size=self.size)  # km3/day plausible 
        accu_unsatisfied_pot_netabstr_glolake = np.random.uniform(0, 0.001, size=self.size)  # km3/day plausible 
        current_mon_day = np.array([1, 1]) #  1st day and month
        num_days_in_month = 31
        k_release = np.zeros(self.size) + 0.1 # (-)

        # ---------------------------
        # Reservoir Area and Capacity
        # ---------------------------
        glores_startyear = xr.open_dataarray("./input_data/static_input/reservoir_regulated_lake/watergap_22e_startyear.nc4", decode_times=False)[0].values  # year
        glores_startmonth = xr.open_dataarray("./input_data/static_input/reservoir_regulated_lake/watergap_22e_startmonth.nc4", decode_times=False)[0].values  # month
        glores_capacity = xr.open_dataarray("./input_data/static_input/reservoir_regulated_lake/watergap_22e_res_stor_cap.nc4", decode_times=False)[0].values  # km3
        glores_type = xr.open_dataarray("./input_data/static_input/reservoir_regulated_lake/watergap_22e_reservoir_type.nc4", decode_times=False)[0].values  # -
        # Initialize newly activated reservior area, Units : km2
        # Keep area values of already activate reservoirs
        glores_area =\
            np.where(resyear >= glores_startyear,
                     all_reservoir_and_regulated_lake_area, 0)

        # Initialize newly activated global reservior capacity,
        # Units : km3, Keep capacity values of already activate
        # reservoirs
        glores_capacity = \
            np.where(resyear >= glores_startyear,
                     glores_capacity, 0)

        # ------------------------------------------------------
        # Reservoir area is added to global lake if
        # mean_annual_inflow_res = 0. reservoir area has to be set
        #  to zero after.
        # ------------------------------------------------------
        mean_annual_inflow_res =  xr.open_dataarray("./input_data/static_input/reservoir_regulated_lake/watergap_22e_mean_inflow.nc4", decode_times=False)[0].values  # km3/month
        mean_annual_inflow_res *= (12 * 1e9 / year_to_s) # m3/s
        glolake_area = xr.open_dataarray("./input_data/static_input/land_water_fractions/watergap_22e_global_lake_area.nc", decode_times=False)[0].values  # km2

        self.mask_mean_annual_inflow = \
            ((glores_area > 0)
             & (resyear >= glores_startyear)
             & (mean_annual_inflow_res == 0))

        glolake_area =\
            np.where(self.mask_mean_annual_inflow,
                     glores_area + glolake_area,
                     glolake_area)

        glores_area[self.mask_mean_annual_inflow] = 0
        all_reservoir_and_regulated_lake_area[self.mask_mean_annual_inflow] = 0

        max_glolake_storage = glolake_area * self.activelake_depth * m_to_km

        # -----------------
        # Reservoir Storage
        # -----------------
        # # Initialize newly activated reservior storage in
        # the current year to maximum,  Units : km3
        # Keep storage values of already activate reservoirs

        glores_storage = \
            np.where(simu_start_year >= glores_startyear,
                     glores_capacity, 0)

        # -------------------------
        # Regulated Lake Storage
        # -----------------------
        regulated_lake_status = xr.open_dataarray("./input_data/static_input/land_water_fractions/watergap_22e_regulated_lake_status.nc", decode_times=False).values  # -
        # For regulated lake: if it's not yet operational
        # increase reservoir storage by multiplying the area with
        # lake depth (Treat it as a global lake)- changed by mohammed
        glores_storage =\
            np.where((simu_start_year < glores_startyear) &
                     (regulated_lake_status == 1),
                     (all_reservoir_and_regulated_lake_area *
                      self.activelake_depth * m_to_km)
                     + glores_storage,
                     glores_storage)

        reg_lake_redfactor_firstday = \
            np.where((simu_start_year < glores_startyear) &
                     (regulated_lake_status == 1), 1,
                     0)

        reg_lake_redfactor_firstday = \
            np.where((glores_storage == glores_capacity) &
                     (regulated_lake_status == 1), 0,
                     reg_lake_redfactor_firstday)

        # update initial storage of global lake if reservoir
        # becomes global lake due to mean_annual_inflow_res = 0.
        self.glolake_storage = max_glolake_storage

        # ===================================================================
        rout_order_all = pd.read_csv("./input_data/static_input/routing_order.csv")
        rout_order = rout_order_all[['Lat_index_routorder',
                                      'Lon_index_routorder']].to_numpy()

        outflow_cell = rout_order_all[['Lat_index_outflowcell',
                                       'Lon_index_outflowcell']].to_numpy()
        alloc_coeff = pd.read_csv("./input_data/static_input/alloc_coeff_by_routorder.csv")
        allocation_coeff = alloc_coeff[alloc_coeff.columns[-5:]].to_numpy()
        # ====================================================================
        for routflow_looper in range(len(rout_order)):
            # Get invidividual cells based on routing order
            x, y = rout_order[routflow_looper]
            if glores_area[x, y] > 0:
                test_result  = res_reg.\
                    reservoir_regulated_lake_water_balance(rout_order, routflow_looper,
                                                           outflow_cell,
                                                           glores_storage[x, y],
                                                           glores_capacity[x, y],
                                                           self.precipitation[x, y],
                                                           self.openwater_pot_evap[x, y],
                                                           self.aridhumid[x, y],
                                                           self.drainage_direction[x, y],
                                                           inflow_to_swb_res[x, y],
                                                           self.gw_recharge_constant[x, y],
                                                           glores_area,
                                                           self.reduction_exponent_res[x, y],
                                                           self.areal_corr_factor[x, y],
                                                           glores_startmonth[x, y],
                                                           current_mon_day,
                                                           k_release[x, y],
                                                           glores_type[x, y],
                                                           allocation_coeff,
                                                           monthly_potential_net_abstraction_sw,
                                                           mean_annual_demand_res,
                                                           mean_annual_inflow_res[x, y],
                                                           glolake_area[x, y],
                                                           accumulated_unsatisfied_potential_netabs_sw[x, y],
                                                           accu_unsatisfied_pot_netabstr_glolake[x, y],
                                                           num_days_in_month,
                                                           all_reservoir_and_regulated_lake_area,
                                                           reg_lake_redfactor_firstday[x, y],
                                                           minstorage_volume)

                glores_storage[x, y] = test_result[0]
        self.assertTrue((np.nanmin(glores_storage) >= glores_storage_min) &
                        (np.nanmax(glores_storage) <= glores_storage_max))

 
        # Check the condition: if mask_mean_annual_inflow is True, glolake_storage must be > 0
        # Hence global lake storage must be updated since  reservoir area is added to global lake if
        # mean_annual_inflow_res = 0.
        zero_indices = np.where(self.mask_mean_annual_inflow == True)
        values_at_indices = self.glolake_storage[zero_indices]

        grt_zero = np.any(values_at_indices > 0)
        self.assertTrue(grt_zero == True)




  

