# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================


# =============================================================================
# This module creates and writes daily ouputs to  storage and flux varibales
# =============================================================================
import concurrent.futures
import platform
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
    except Exception as exc:
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
            "canopy_evap": "canopy_evap",
            "throughfall": "throughfall",
            "swe": "snow_water_equiv",
            "snow_fall": "snow_fall",
            "snow_melt": "snow_melt",
            "snow_evap": "snow_evap",
            "soilmoist": "soil_moisture",
            "qr": "groundwater_recharge",
            "qs": "surface_runoff"
        }

        # Initialize output variables for vertical water balance
        for var_name, cm_var in vb_output_vars.items():
            if var_name in {'canopystor', 'swe', 'soilmoist'}:
                if cm.vb_storages.get(cm_var) is True:
                    var = doh.OutputVariable(var_name, cm.vb_storages.get(cm_var),
                                             grid_coords)
                    self.vb_storages[var_name] = var
            else:
                if cm.vb_fluxes.get(cm_var) is True:
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
            "groundwstor": "groundwater_storage",
            "qg": "groundwater_discharge",
            "locallakestor": "local_lake_storage",
            "locallake_outflow": "local_lake_outflow",
            "localwetlandstor": "local_wetland_storage",
            "localwetland_outflow": "local_wetland_outflow",
            "globallakestor": "global_lake_storage",
            "globallake_outflow": "global_lake_outflow",
            "globalwetlandstor": "global_wetland_storage",
            "globalwetland_outflow": "global_wetland_outflow",
            "riverstor": "river_storage",
            "glores_stor": "global_reservoir_storage",
            "dis": "streamflow",
            "actual_net_abstraction_gw": "actual_net_abstr_groundwater",
            "satisfied_demand_neigbhourcell": "satisfied_demand_neigbhourcell"
        }

        # Initialize output variables for lateral water balance
        for var_name, cm_var in lb_output_vars.items():
            if var_name in {'groundwstor', "locallakestor", "localwetlandstor",
                            "globallakestor", "globalwetlandstor",
                            "riverstor", "glores_stor"}:
                if cm.lb_storages.get(cm_var) is True:
                    var = doh.OutputVariable(var_name, cm.lb_storages.get(cm_var),
                                             grid_coords)
                    self.lb_storages[var_name] = var
            else:
                if cm.lb_fluxes.get(cm_var) is True:
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

    def save_netcdf_parallel(self, end_date):
        """
        Save variables to netcdf.

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
