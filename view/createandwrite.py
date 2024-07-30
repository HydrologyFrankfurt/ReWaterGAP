# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"Write variables to NetCDF"

# =============================================================================
# This module creates and writes daily ouputs to  storage and flux varibales
# =============================================================================
import concurrent.futures
import platform
import numpy as np
from controller import configuration_module as cm
from view import data_output_handler as doh


#  write_to_netcdf (used together with save_netcdf_parallel function
# in CreateandWritetoVariables class)
def write_to_netcdf(args):
    """
    Write variables to NetCDF.

    Parameters
    ----------
    args : list of xrray variable, encoding and path to save data

    """
    var, encoding, path = args
    try:
        var.to_netcdf(path, format='NETCDF4_CLASSIC', encoding=encoding)
        del var
        return None  # Successful execution
    except FileNotFoundError as exc:
        return exc


class CreateandWritetoVariables:
    """Create and write daily ouputs to  storage and flux varibales."""

    def __init__(self, grid_coords):
        # output path
        self.path = cm.config_file['FilePath']['outputDir']
        # =====================================================================
        # create ouput variable
        # =====================================================================
        # Note!!! grid_coord contains latitiude, longitude and time (based on
        # simulation period )

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #         #  Vertcal Water Balance (vb)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.vb_storages = {}
        self.vb_fluxes = {}

        # Define output variables for vertical water balance
        # output variable name : name in config file
        vb_output_vars = {
            "potevap": "pot_evap",
            "netrad": "net_rad",
            "lai-total": "leaf_area_index",
            "canopystor": "canopy_storage",
            "canopy-evap": "canopy_evap",
            "throughfall": "throughfall",
            "swe": "snow_water_equiv",
            "snowfall": "snow_fall",
            "snm": "snow_melt",
            "snow-evap": "snow_evap",
            "snowcover-frac": "snowcover_frac",
            "soilmoist": "soil_moisture",
            "smax": "maximum_soil_moisture",
            "qrd": "groundwater_recharge",
            "qs": "surface_runoff"
        }

        # Initialize output variables for vertical water balance
        for var_name, cm_var in vb_output_vars.items():
            if var_name in {'canopystor', 'swe', 'soilmoist', 'smax'}:
                if cm.vb_storages.get(cm_var):
                    var = doh.OutputVariable(var_name, cm.vb_storages.get(cm_var),
                                             grid_coords)
                    self.vb_storages[var_name] = var
            else:
                if cm.vb_fluxes.get(cm_var):
                    var = doh.OutputVariable(var_name, cm.vb_fluxes.get(cm_var),
                                             grid_coords)
                    self.vb_fluxes[var_name] = var

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #         #  Lateral Water Balance (lb)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.lb_storages = {}
        self.lb_fluxes = {}

        # Lateral Water Balance Variables
        # output variable name : name in config file
        lb_output_vars = {
            "consistent-precipitation" : "consistent_precipitation",
            "groundwstor": "groundwater_storage",
            "qg": "groundwater_discharge",
            "qtot": "total_runoff", 
            "qrf": "groundwater_recharge_swb",
            "qr": "total_groundwater_recharge",
            "locallakestor": "local_lake_storage",
            "locallake-outflow": "local_lake_outflow",
            "localwetlandstor": "local_wetland_storage",
            "localwetland-outflow": "local_wetland_outflow",
            "globallakestor": "global_lake_storage",
            "globallake-outflow": "global_lake_outflow",
            "globalwetlandstor": "global_wetland_storage",
            "globalwetland-outflow": "global_wetland_outflow",
            "riverstor": "river_storage",
            "reservoirstor": "global_reservoir_storage",
            "tws": "total_water_storage",

            "dis": "streamflow",
            "dis-from-upstream": "streamflow_from_upstream",
            "dis-from-inlandsink": "streamflow_from_inland_sink",

            "atotusegw": "actual_net_abstr_groundwater",
            "atotusesw": "actual_net_abstr_surfacewater",
            "atotuse": "actual_water_consumption",
            "evap-total": "cell_aet_consuse",

            "total_demand_into_cell": "total_demand_into_cell",
            "unsat_potnetabs_sw_from_demandcell": "unsat_potnetabs_sw_from_demandcell",

            "returned_demand_from_supply_cell":
                "returned_demand_from_supply_cell",
            "prev_returned_demand_from_supply_cell":
                "prev_returned_demand_from_supply_cell",
            "total_unsatisfied_demand_ripariancell": "total_unsatisfied_demand_ripariancell",
            "accumulated_unsatisfied_potential_netabs_sw":
                "accumulated_unsatisfied_potential_netabs_sw",
            "get_neighbouring_cells_map":"get_neighbouring_cells_map",
            "total_unsatisfied_demand_from_supply_to_all_demand_cell":
                "total_unsatisfied_demand_from_supply_to_all_demand_cell",
            "ncrun":  "net_cell_runoff",
            "river-velocity": "river_velocity",
            "land-area-fraction":  "land_area_fraction",
            "pot_cell_runoff": "pot_cell_runoff"

        }

        # Initialize output variables for lateral water balance
        for var_name, cm_var in lb_output_vars.items():
            if var_name in {'groundwstor', "locallakestor", "localwetlandstor",
                            "globallakestor", "globalwetlandstor",
                            "riverstor", "reservoirstor", "tws"}:
                if cm.lb_storages.get(cm_var):
                    var = doh.OutputVariable(var_name, cm.lb_storages.get(cm_var),
                                             grid_coords)
                    self.lb_storages[var_name] = var
            else:
                if cm.lb_fluxes.get(cm_var):
                    var = doh.OutputVariable(var_name, cm.lb_fluxes.get(cm_var),
                                             grid_coords)
                    self.lb_fluxes[var_name] = var

    def verticalbalance_write_daily_var(self, value, time_step, sim_year,
                                        sim_month, sim_day):
        """
        Write values to variable for vertical water balance.

        Parameters
        ----------
        value : dict
            Dictionary of storages and fluxes for vertical water balance.
        time_step : int
            Daily timestep.
        sim_year: : int
            Simulation year
        sim_month : int
            Simulation month
        sim_day : int
            Simulation day


        Returns
        -------
        None.

        """
        # =================================================================
        # Writing daily values to variables
        # Note!!! value[0]=Storages and value[1]=Fluxes
        # =================================================================
        # Storages
        storage_var = value[0]
        for var_name, var in self.vb_storages.items():
            var.write_daily_output(storage_var[var_name], time_step, sim_year,
                                   sim_month, sim_day)

        # Fluxes
        fluxes_var = value[1]
        for var_name, var in self.vb_fluxes.items():
            var.write_daily_output(fluxes_var[var_name], time_step, sim_year,
                                   sim_month, sim_day)

    def lateralbalance_write_daily_var(self, value, time_step, sim_year,
                                       sim_month, sim_day):
        """
        Write values to variable for lateral water balance.

        Parameters
        ----------
        value : dict
            Dictionary of storages and fluxes for lateral water balance.
         time_step : int
             Daily timestep.
         sim_year: : int
             Simulation year
         sim_month : int
             Simulation month
         sim_day : int
             Simulation day
        Returns
        -------
        None.

        """
        # =================================================================
        # Writing daily values to variables
        # Note!!! value[0]=Storages and value[1]=Fluxes
        # =================================================================
        # Storages
        storage_var = value[0]
        for var_name, var in self.lb_storages.items():
            var.write_daily_output(storage_var[var_name], time_step, sim_year,
                                   sim_month, sim_day)

        # Fluxes
        fluxes_var = value[1]
        for var_name, var in self.lb_fluxes.items():
            var.write_daily_output(fluxes_var[var_name], time_step, sim_year,
                                   sim_month, sim_day)

    def base_units(self, cell_area, contfrac):
        """
        Convert units of model outputs.

        Parameters
        ----------
        cell_area : array
            Area of the grid cell,  Unit: [km^2]
        contfrac : array
            continental fraction (land and surfacewater bodies), Unit: [-]
        month_daily_aggr : string
            Specifies the aggregation method, either "month" for monthly averages 
            or "daily" for daily values.

        Returns
        -------
        None.

        """
        cell_area = cell_area.astype(np.float64)
        contfrac = contfrac.values.astype(np.float64)

        km3_to_mm = 1e6/(cell_area * (contfrac/100))
        days_to_s = 86400
        km_to_m = 1e3
        km3_to_m3 = 1e9
        ouptputs = [self.vb_storages, self.vb_fluxes, self.lb_storages,
                    self.lb_fluxes]
        for i in range(4):
            for key, value in ouptputs[i].items():
                if i == 0:
                    # already in mm or  kg m-2
                    converted_data = value.data[key].values

                elif i == 1:
                    if key in ("lai-total", "snowcover-frac"):
                        converted_data = value.data[key].values
                    else:
                        # convert from mm/day to mm/s or  kg m-2 s-1
                        converted_data = value.data[key].values / days_to_s

                elif i == 2:
                    # convert from km3 to mm or  kg m-2
                    converted_data = value.data[key].values * km3_to_mm

                elif i == 3:
                    if key in ("get_neighbouring_cells_map", "land-area-fraction"):
                        converted_data = value.data[key].values
                    # convert to m3/s  for discharge and m/s for velocity
                    elif key in ("dis", "dis_from_upstream", "dis_from_inland_sink"):
                        converted_data = (value.data[key].values * km3_to_m3) / days_to_s
                    elif key == "river_velocity":
                        converted_data = (value.data[key].values * km_to_m) / days_to_s
                    else:  # convert from km3/day to mm/s or  kg m-2 s-1
                        converted_data = (value.data[key].values * km3_to_mm) / days_to_s

                # converted and aggreagated data
                value.data[key][:] = converted_data

    def save_netcdf_parallel(self, end_date):
        """
        Save variables to netcdf.

        end_date: datetime
            Date for end of simulation

        Returns
        -------
        None.

        """
        # Create a list of tuples with arguments for writing
        write_args = []
        for var in [self.vb_storages, self.vb_fluxes,
                    self.lb_storages, self.lb_fluxes]:
            for key, value in var.items():
                path = self.path + f'{key}_{end_date}.nc'

                if key == "get_neighbouring_cells_map":
                    encoding = {key: {'chunksizes': [1, 360, 720, 2],
                                      "zlib": True,
                                      "complevel": 5}}
                else:
                    encoding = {key: {'_FillValue': 1e+20,
                                      'chunksizes': [1, 360, 720],
                                      "zlib": True, "complevel": 5}}
                write_args.append((value.data, encoding, path))

        # For saving output in parallel, Threading is used for macOS but
        # multiprocessing is used of Linux, windows, etc
        if platform.system() != 'Darwin':  # not macOS
            with concurrent.futures.ProcessPoolExecutor() as executor:
                executor.map(write_to_netcdf, write_args)
        else:
            for i in write_args:
                write_to_netcdf(i)
