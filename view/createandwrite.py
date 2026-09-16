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
from pathlib import Path
from controller.output_options import OUTPUT_GROUPS
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
    var.to_netcdf(path, format='NETCDF4_CLASSIC', encoding=encoding)


class CreateandWritetoVariables:
    """Create and write daily ouputs to  storage and flux varibales."""

    def __init__(self, grid_coords):
        # output path
        self.path = cm.config_file['FilePath']['outputDir']
        # Forcing coordinates can extend beyond the requested simulation end.
        grid_coords = grid_coords.to_dataset().sel(time=slice(cm.start, cm.end)).coords
        self.monthly = {name: {} for name in OUTPUT_GROUPS}
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
            "qrd": "groundwater_recharge_diffuse",
            "qs": "surface_runoff"
        }

        self._create_variables(vb_output_vars, grid_coords,
                               {"canopystor", "swe", "soilmoist", "smax"},
                               "VerticalWaterBalance", self.vb_storages, self.vb_fluxes)

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


            "atotusegw": "actual_net_abstr_groundwater",
            "atotusesw": "actual_net_abstr_surfacewater",
            "atotuse": "actual_water_consumption",
            "evap-total": "cell_aet_consuse",

            "unsat_potnetabs_sw_from_demandcell": "unsat_potnetabs_sw_from_demandcell",

            "returned_demand_from_supplycell": "returned_demand_from_supplycell",
            "returned_demand_from_supplycell_nextday":
                "returned_demand_from_supplycell_nextday",
            "demand_left_excl_returned_nextday": "demand_left_excl_returned_nextday",
            "potnetabs_sw": "potnetabs_sw",

            "get_neighbouring_cells_map": "get_neighbouring_cells_map",
            "ncrun":  "net_cell_runoff",
            "river-velocity": "river_velocity",
            "land-area-fraction":  "land_area_fraction",
            "pot_cell_runoff": "pot_cell_runoff",
            "locwet_extent": "locwet_extent",
            "glowet_extent": "glowet_extent",
            "loclake_extent": "loclake_extent",
            "glores_outflow":"glores_outflow",
            "glores_inflow": "glores_inflow"

        }

        self._create_variables(lb_output_vars, grid_coords,
                               {"groundwstor", "locallakestor", "localwetlandstor",
                                "globallakestor", "globalwetlandstor", "riverstor",
                                "reservoirstor", "tws"},
                               "LateralWaterBalance", self.lb_storages, self.lb_fluxes)

    def _create_variables(self, names, grid_coords, storage_names, balance,
                          daily_storages, daily_fluxes):
        for var_name, config_name in names.items():
            storage = var_name in storage_names
            group = balance + ("Storages" if storage else "Fluxes")
            for frequency in ("Daily", "Monthly"):
                selected = cm.output_options[frequency][group].get(config_name, False)
                # Calibration consumes daily discharge/runoff directly in memory.
                if cm.run_calib:
                    if frequency == "Monthly":
                        continue
                    selected = selected or var_name in {"dis", "pot_cell_runoff"}
                if selected:
                    target = (self.monthly[group] if frequency == "Monthly" else
                              daily_storages if storage else daily_fluxes)
                    target[var_name] = doh.OutputVariable(
                        var_name, True, grid_coords, frequency=frequency)

    def _output_groups(self):
        """Yield groups in conversion order, independently for each frequency."""
        for frequency, groups in (
                ("Daily", [self.vb_storages, self.vb_fluxes,
                           self.lb_storages, self.lb_fluxes]),
                ("Monthly", [self.monthly[name] for name in
                             ("VerticalWaterBalanceStorages", "VerticalWaterBalanceFluxes",
                              "LateralWaterBalanceStorages", "LateralWaterBalanceFluxes")])):
            for index, group in enumerate(groups):
                yield frequency, index, group

    def verticalbalance_write_daily_var(self, value, sim_year,
                                        sim_month, sim_day):
        """
        Write values to variable for vertical water balance.

        Parameters
        ----------
        value : dict
            Dictionary of storages and fluxes for vertical water balance.
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
        for var_name, var in list(self.vb_storages.items()) + list(
                self.monthly["VerticalWaterBalanceStorages"].items()):
            var.write_daily_output(storage_var[var_name], sim_year,
                                   sim_month, sim_day)

        # Fluxes
        fluxes_var = value[1]
        for var_name, var in list(self.vb_fluxes.items()) + list(
                self.monthly["VerticalWaterBalanceFluxes"].items()):
            var.write_daily_output(fluxes_var[var_name], sim_year,
                                   sim_month, sim_day)

    def lateralbalance_write_daily_var(self, value, sim_year,
                                       sim_month, sim_day):
        """
        Write values to variable for lateral water balance.

        Parameters
        ----------
        value : dict
            Dictionary of storages and fluxes for lateral water balance.
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
        for var_name, var in list(self.lb_storages.items()) + list(
                self.monthly["LateralWaterBalanceStorages"].items()):
            var.write_daily_output(storage_var[var_name], sim_year,
                                   sim_month, sim_day)

        # Fluxes
        fluxes_var = value[1]
        for var_name, var in list(self.lb_fluxes.items()) + list(
                self.monthly["LateralWaterBalanceFluxes"].items()):
            var.write_daily_output(fluxes_var[var_name], sim_year,
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
        for frequency, i, group in self._output_groups():
            for key, value in group.items():
                value.finalize_month()
                # Monthly water amounts already contain the sum of daily amounts.
                time_divisor = (1 if frequency == "Monthly" and
                                value.aggregation == "sum" else days_to_s)
                if i == 0:
                    # already in mm or  kg m-2
                    converted_data = value.data[key].values

                elif i == 1:
                    if key in ("lai-total", "snowcover-frac", "netrad"):
                        converted_data = value.data[key].values
                    else:
                        # convert from mm/day to mm/s or  kg m-2 s-1
                        converted_data = value.data[key].values / time_divisor

                elif i == 2:
                    # convert from km3 to mm or  kg m-2
                    converted_data = value.data[key].values * km3_to_mm

                elif i == 3:
                    if key in ("get_neighbouring_cells_map", "land-area-fraction",
                               "locwet_extent", "glowet_extent", "loclake_extent"):
                        converted_data = value.data[key].values
                    # convert to m3/s  for discharge and m/s for velocity
                    elif key in ("dis",  "dis-from-upstream","glores_outflow", "glores_inflow"):
                        converted_data = (value.data[key].values * km3_to_m3) / days_to_s
                    elif key == "river-velocity":
                        converted_data = (value.data[key].values * km_to_m) / days_to_s
                    else:  # convert from km3/day to mm/s or  kg m-2 s-1
                        converted_data = (value.data[key].values * km3_to_mm) / time_divisor

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
        output_dir = Path(self.path)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = set()
        for frequency, _, group in self._output_groups():
            for key, value in group.items():
                suffix = end_date[:7] if frequency == "Monthly" else end_date
                path = output_dir / f'{key}_{suffix}.nc'

                if key == "get_neighbouring_cells_map":
                    encoding = {key: {'chunksizes': [1, value.data[key].shape[1], 
                                                     value.data[key].shape[2], 2],
                                      "zlib": True,
                                      "complevel": 5}}
                elif key == 'smax':
                    path = output_dir / f'{key}.nc'
                    encoding = {key: {'_FillValue': 1e+20,
                                      "zlib": True,
                                      "complevel": 5}}
                else:
                    encoding = {key: {'_FillValue': 1e+20,
                                      'chunksizes': [1, value.data[key].shape[1], 
                                                     value.data[key].shape[2]],
                                      "zlib": True, "complevel": 5}}
                if path in paths:  # smax is static and shared between frequencies.
                    continue
                paths.add(path)
                if "time_bnds" in value.data:
                    time_encoding = {"units": "days since 1900-01-01", "calendar": "noleap"}
                    encoding["time"] = time_encoding.copy()
                    encoding["time_bnds"] = time_encoding.copy()
                write_args.append((value.data, encoding, path))

        # For saving output in parallel, Threading is used for macOS but
        # multiprocessing is used of Linux, windows, etc
        if not write_args:
            return
        if platform.system() != 'Darwin':  # not macOS
            with concurrent.futures.ProcessPoolExecutor(max_workers=min(8, len(write_args))) as executor:
                # Consume results so write failures propagate to the caller.
                list(executor.map(write_to_netcdf, write_args))
        else:
            for i in write_args:
                write_to_netcdf(i)
