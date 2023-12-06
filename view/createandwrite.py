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

from controller import configuration_module as cm
from view import data_output_handler as doh
from view import output_var_info as var_info


class CreateandWritetoVariables:
    """Create and write daily ouputs to  storage and flux varibales."""

    def __init__(self, grid_coords):
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

        potential_evap = doh.OuputVariable("potevap",  cm.vb_fluxes.
                                           get('pot_evap'), grid_coords)

        net_radiation = doh.OuputVariable("netrad", cm.vb_fluxes.
                                          get('net_rad'), grid_coords)

        leaf_area_index = doh.OuputVariable("lai-total", cm.vb_fluxes.
                                            get('leaf_area_index'), grid_coords)

        canopy_storage = doh.OuputVariable("canopystor", cm.vb_storages.
                                           get('canopy_storage'), grid_coords)

        canopy_evap = doh.OuputVariable("canopy_evap",
                                        cm.vb_fluxes.get('canopy_evap'),
                                        grid_coords)

        throughfall = doh.OuputVariable("throughfall", cm.vb_fluxes.
                                        get('throughfall'), grid_coords)

        snow_water_storage = \
            doh.OuputVariable("swe", cm.vb_storages.get('snow_water_equiv'),
                              grid_coords)

        snow_fall = doh.OuputVariable("snow_fall", cm.vb_fluxes.
                                      get('snow_fall'), grid_coords)

        snow_melt = doh.OuputVariable("snow_melt", cm.vb_fluxes.
                                      get('snow_melt'), grid_coords)

        sublimation = doh.OuputVariable("snow_evap", cm.vb_fluxes.
                                        get('snow_evap'), grid_coords)

        soil_water_storage = \
            doh.OuputVariable("soilmoist", cm.vb_storages.get('soil_moisture'),
                              grid_coords)

        groundwater_recharge = \
            doh.OuputVariable("qr", cm.vb_fluxes.get('groundwater_recharge'),
                              grid_coords)

        surface_runoff = \
            doh.OuputVariable("qs", cm.vb_fluxes.get('surface_runoff'),
                              grid_coords)

        # =====================================================================
        # Grouping all vertical water balance variables
        # =====================================================================
        # Storages
        self.vb_storages.update({'canopystor': canopy_storage,
                                 'swe': snow_water_storage,
                                 'soilmoist': soil_water_storage})
        # Fluxes
        self.vb_fluxes.\
            update({"netrad": net_radiation,
                    "potevap": potential_evap,
                    "lai-total": leaf_area_index,
                    "canopy_evap": canopy_evap,
                    "throughfall": throughfall,
                    "snow_fall": snow_fall,
                    "snow_melt": snow_melt,
                    "snow_evap": sublimation,
                    "qr": groundwater_recharge,
                    "qs": surface_runoff})

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #         #  Lateral Water Balance (lb)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.lb_storages = {}
        self.lb_fluxes = {}

        groundwater_storage = \
            doh.OuputVariable("groundwstor", cm.lb_storages.
                              get('groundwater_storage'), grid_coords)

        groundwater_discharge = \
            doh.OuputVariable("qg", cm.lb_fluxes.
                              get('groundwater_discharge'), grid_coords)

        loclake_storage = \
            doh.OuputVariable("locallakestor", cm.lb_storages.
                              get('local_lake_storage'), grid_coords)

        loclake_outflow = \
            doh.OuputVariable("locallake_outflow", cm.lb_fluxes.
                              get('local_lake_outflow'),  grid_coords)

        locwet_storage = \
            doh.OuputVariable("localwetlandstor", cm.lb_storages.
                              get('local_wetland_storage'), grid_coords)
        locwet_outflow = \
            doh.OuputVariable("localwetland_outflow", cm.lb_fluxes.
                              get('local_wetland_outflow'),  grid_coords)

        glolake_storage = \
            doh.OuputVariable("globallakestor", cm.lb_storages.
                              get('global_lake_storage'), grid_coords)

        glolake_outflow = \
            doh.OuputVariable("globallake_outflow",
                              cm.lb_fluxes.get('global_lake_outflow'),
                              grid_coords)

        glowet_storage = \
            doh.OuputVariable("globalwetlandstor", cm.lb_storages.
                              get('global_wetland_storage'), grid_coords)

        glowet_outflow = \
            doh.OuputVariable("globalwetland_outflow", cm.lb_fluxes.
                              get('global_wetland_outflow'), grid_coords)

        river_storage = \
            doh.OuputVariable("riverstor", cm.lb_storages.
                              get('river_storage'), grid_coords)
        streamflow = \
            doh.OuputVariable("dis", cm.lb_fluxes.get('streamflow'),
                              grid_coords)

        actual_net_abstraction_gw = \
            doh.OuputVariable("actual_net_abstraction_gw", cm.lb_fluxes.
                              get('actual_net_abstr_groundwater'), grid_coords)
        # =====================================================================
        # Grouping all lateral water balance variables
        # =====================================================================
        # Storages
        self.lb_storages.update({"groundwstor": groundwater_storage,
                                 "locallakestor": loclake_storage,
                                 "localwetlandstor": locwet_storage,
                                 "globallakestor": glolake_storage,
                                 "globalwetlandstor": glowet_storage,
                                 "riverstor": river_storage})

        # Fluxes
        self.lb_fluxes.update({"qg": groundwater_discharge,
                               "locallake_outflow": loclake_outflow,
                               "localwetland_outflow": locwet_outflow,
                               "globallake_outflow": glolake_outflow,
                               "globalwetland_outflow": glowet_outflow,
                               "dis": streamflow,
                               "actual_net_abstraction_gw": actual_net_abstraction_gw})

    def verticalbalance_write_daily_var(self, value, time_step):
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
        self.vb_storages['canopystor'].\
            write_daily_ouput(storage_var['canopystor'], time_step)

        self.vb_storages['swe'].\
            write_daily_ouput(storage_var['swe'], time_step)

        self.vb_storages['soilmoist'].\
            write_daily_ouput(storage_var['soilmoist'], time_step)

        # Fluxes
        fluxes_var = value[1]
        self.vb_fluxes['netrad'].\
            write_daily_ouput(fluxes_var['netrad'], time_step)

        self.vb_fluxes['potevap'].\
            write_daily_ouput(fluxes_var['potevap'], time_step)

        self.vb_fluxes['lai-total'].\
            write_daily_ouput(fluxes_var['lai-total'], time_step)

        self.vb_fluxes['canopy_evap'].\
            write_daily_ouput(fluxes_var['canopy_evap'], time_step)

        self.vb_fluxes['throughfall'].\
            write_daily_ouput(fluxes_var['throughfall'], time_step)

        self.vb_fluxes['snow_fall'].\
            write_daily_ouput(fluxes_var['snow_fall'], time_step)

        self.vb_fluxes['snow_melt'].\
            write_daily_ouput(fluxes_var['snow_melt'], time_step)

        self.vb_fluxes['snow_evap'].\
            write_daily_ouput(fluxes_var['snow_evap'], time_step)

        self.vb_fluxes['qr'].write_daily_ouput(fluxes_var['qr'], time_step)

        self.vb_fluxes['qs'].write_daily_ouput(fluxes_var['qs'], time_step)

    def lateralbalance_write_daily_var(self, value, time_step):
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
        self.lb_storages['groundwstor'].\
            write_daily_ouput(storage_var['groundwstor'], time_step)

        self.lb_storages['locallakestor'].\
            write_daily_ouput(storage_var['locallakestor'], time_step)

        self.lb_storages['localwetlandstor'].\
            write_daily_ouput(storage_var['localwetlandstor'], time_step)

        self.lb_storages['globallakestor'].\
            write_daily_ouput(storage_var['globallakestor'], time_step)

        self.lb_storages['globalwetlandstor'].\
            write_daily_ouput(storage_var['globalwetlandstor'], time_step)

        self.lb_storages['riverstor'].\
            write_daily_ouput(storage_var['riverstor'], time_step)

        # Fluxes
        fluxes_var = value[1]

        self.lb_fluxes['qg'].write_daily_ouput(fluxes_var['qg'], time_step)

        self.lb_fluxes['locallake_outflow'].\
            write_daily_ouput(fluxes_var['locallake_outflow'], time_step)

        self.lb_fluxes['localwetland_outflow'].\
            write_daily_ouput(fluxes_var['localwetland_outflow'], time_step)

        self.lb_fluxes['globallake_outflow'].\
            write_daily_ouput(fluxes_var['globallake_outflow'], time_step)

        self.lb_fluxes['globalwetland_outflow'].\
            write_daily_ouput(fluxes_var['globalwetland_outflow'], time_step)

        self.lb_fluxes['dis'].write_daily_ouput(fluxes_var['dis'], time_step)

        self.lb_fluxes['actual_net_abstraction_gw'].\
            write_daily_ouput(fluxes_var['actual_net_abstraction_gw'],
                              time_step)

    def save_to_netcdf(self, end_date):
        """
        Save variables to netcdf.

        Returns
        -------
        None.

        """
        # =====================================================================
        #                       Storages
        # =====================================================================
        # Vertical Water Balance
        self.vb_storages['canopystor'].to_netcdf('canopy_storage_' + end_date)
        self.vb_storages['swe'].to_netcdf('snow_water_storage_' + end_date)
        self.vb_storages['soilmoist'].\
            to_netcdf('soil_water_storage_' + end_date)

        # Lateral Water Balance
        self.lb_storages['groundwstor'].\
            to_netcdf('groundwater_storage_' + end_date)

        self.lb_storages['locallakestor'].\
            to_netcdf('locallake_storage_' + end_date)

        self.lb_storages['localwetlandstor'].\
            to_netcdf('localwetland_storage_' + end_date)

        self.lb_storages['globallakestor'].\
            to_netcdf('globallake_storage_' + end_date)
        self.lb_storages['globalwetlandstor'].\
            to_netcdf('globalwetland_storage_' + end_date)

        self.lb_storages['riverstor'].\
            to_netcdf('river_storage_' + end_date)

        # =====================================================================
        #                       Fluxes
        # =====================================================================
        # Vertical Water Balance
        self.vb_fluxes['netrad'].to_netcdf('net_radiation_' + end_date)
        self.vb_fluxes['potevap'].to_netcdf('pet_taylor_' + end_date)
        self.vb_fluxes['lai-total'].to_netcdf('leaf_area_index_' + end_date)
        self.vb_fluxes['canopy_evap'].to_netcdf('canopy_evap_' + end_date)
        self.vb_fluxes['throughfall'].to_netcdf('throughfall_' + end_date)
        self.vb_fluxes['snow_fall'].to_netcdf('snow_fall_' + end_date)
        self.vb_fluxes['snow_melt'].to_netcdf('snow_melt_' + end_date)
        self.vb_fluxes['snow_evap'].to_netcdf('sublimation_' + end_date)
        self.vb_fluxes['qr'].\
            to_netcdf('groundwater_recharge_' + end_date)
        self.vb_fluxes['qs'].\
            to_netcdf('surface_runoff_' + end_date)

        # Lateral Water Balance
        self.lb_fluxes['qg'].to_netcdf('groundwater_discharge_' + end_date)

        self.lb_fluxes['locallake_outflow'].\
            to_netcdf('locallake_outflow_' + end_date)

        self.lb_fluxes['localwetland_outflow'].\
            to_netcdf('localwetland_outflow_' + end_date)

        self.lb_fluxes['globallake_outflow'].\
            to_netcdf('globallake_outflow_' + end_date)

        self.lb_fluxes['globalwetland_outflow'].\
            to_netcdf('globalwetland_outflow_' + end_date)

        self.lb_fluxes['dis'].to_netcdf('streamflow_' + end_date)
        self.lb_fluxes['actual_net_abstraction_gw'].\
            to_netcdf('actual_net_abstraction_gw_' + end_date)
