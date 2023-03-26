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
from view import data_output_handler as do


class CreateandWritetoVariables:
    """ Create and write daily ouputs to  storage and flux varibales."""

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

        potential_evap = do.\
            OuputVariable('potevap', cm.vb_fluxes.get('potevap'), grid_coords)

        net_radiation = do.OuputVariable('netrad', cm.vb_fluxes.get('netrad'),
                                         grid_coords)
        leaf_area_index = do.OuputVariable('lai', cm.vb_fluxes.get('lai'),
                                           grid_coords)

        canopy_storage = do.OuputVariable('canopystor',
                                          cm.vb_storages.get('canopystor'),
                                          grid_coords)

        canopy_evap = do.OuputVariable('canopy_evap',
                                       cm.vb_fluxes.get('canopy_evap'),
                                       grid_coords)

        throughfall = do.OuputVariable('throughfall',
                                       cm.vb_fluxes.get('throughfall'),
                                       grid_coords)

        snow_water_storage = do.OuputVariable('swe', cm.vb_storages.get('swe'),
                                              grid_coords)

        snow_fall = do.OuputVariable('snow_fall', cm.vb_fluxes.
                                     get('snow_fall'), grid_coords)

        snow_melt = do.OuputVariable('snow_melt', cm.vb_fluxes.
                                     get('snow_melt'), grid_coords)

        sublimation = do.OuputVariable('snow_evap', cm.vb_fluxes.
                                       get('snow_evap'), grid_coords)

        soil_water_storage = do.OuputVariable('soilmoist',
                                              cm.vb_storages.get('soilmoist'),
                                              grid_coords)

        groundwater_recharge = \
            do.OuputVariable('groundwater_recharge',
                             cm.vb_fluxes.get('groundwater_recharge'),
                             grid_coords)
        surface_runoff = do.\
            OuputVariable('surface_runoff', cm.vb_fluxes.get('surface_runoff'),
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
            update({'netrad': net_radiation,
                    'potevap': potential_evap,
                    'lai': leaf_area_index,
                    'canopy_evap': canopy_evap,
                    'throughfall': throughfall,
                    'snow_fall': snow_fall,
                    'snow_melt': snow_melt,
                    'snow_evap': sublimation,
                    'groundwater_recharge': groundwater_recharge,
                    'surface_runoff': surface_runoff})

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #         #  Lateral Water Balance (lb)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.lb_storages = {}
        self.lb_fluxes = {}

        groundwater_storage = \
            do.OuputVariable('groundwater_storage',
                             cm.lb_storages.get('groundwater_storage'),
                             grid_coords)

        groundwater_discharge = \
            do.OuputVariable('groundwater_discharge',
                             cm.lb_fluxes.get('groundwater_discharge'),
                             grid_coords)

        loclake_storage = \
            do.OuputVariable('locallake_storage',
                             cm.lb_storages.get('locallake_storage'),
                             grid_coords)

        loclake_outflow = \
            do.OuputVariable('locallake_outflow',
                             cm.lb_fluxes.get('locallake_outflow'),
                             grid_coords)

        locwet_storage = \
            do.OuputVariable('localwetland_storage',
                             cm.lb_storages.get('localwetland_storage'),
                             grid_coords)
        locwet_outflow = \
            do.OuputVariable('localwetland_outflow',
                             cm.lb_fluxes.get('localwetland_outflow'),
                             grid_coords)

        glolake_storage = \
            do.OuputVariable('globallake_storage',
                             cm.lb_storages.get('globallake_storage'),
                             grid_coords)

        glolake_outflow = \
            do.OuputVariable('globallake_outflow',
                             cm.lb_fluxes.get('globallake_outflow'),
                             grid_coords)

        glowet_storage = \
            do.OuputVariable('globalwetland_storage',
                             cm.lb_storages.get('globalwetland_storage'),
                             grid_coords)

        glowet_outflow = \
            do.OuputVariable('globalwetland_outflow',
                             cm.lb_fluxes.get('globalwetland_outflow'),
                             grid_coords)
        river_storage = \
            do.OuputVariable('river_storage',
                             cm.lb_storages.get('river_storage'),
                             grid_coords)
        streamflow = \
            do.OuputVariable('streamflow',
                             cm.lb_fluxes.get('streamflow'),
                             grid_coords)
        # =====================================================================
        # Grouping all lateral water balance variables
        # =====================================================================
        # Storages
        self.lb_storages.update({'groundwater_storage': groundwater_storage,
                                 'locallake_storage': loclake_storage,
                                 'localwetland_storage': locwet_storage,
                                 'globallake_storage': glolake_storage,
                                 'globalwetland_storage': glowet_storage,
                                 'river_storage': river_storage})

        # Fluxes
        self.lb_fluxes.update({'groundwater_discharge': groundwater_discharge,
                               'locallake_outflow': loclake_outflow,
                               'localwetland_outflow': locwet_outflow,
                               'globallake_outflow': glolake_outflow,
                               'globalwetland_outflow': glowet_outflow,
                               'streamflow': streamflow})

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

        self.vb_fluxes['lai'].\
            write_daily_ouput(fluxes_var['lai'], time_step)

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

        self.vb_fluxes['groundwater_recharge'].\
            write_daily_ouput(fluxes_var['groundwater_recharge_out'],
                              time_step)

        self.vb_fluxes['surface_runoff'].\
            write_daily_ouput(fluxes_var['surface_runoff_out'], time_step)

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
        self.lb_storages['groundwater_storage'].\
            write_daily_ouput(storage_var['groundwater_storage'], time_step)

        self.lb_storages['locallake_storage'].\
            write_daily_ouput(storage_var['locallake_storage'], time_step)

        self.lb_storages['localwetland_storage'].\
            write_daily_ouput(storage_var['localwetland_storage'], time_step)

        self.lb_storages['globallake_storage'].\
            write_daily_ouput(storage_var['globallake_storage'], time_step)

        self.lb_storages['globalwetland_storage'].\
            write_daily_ouput(storage_var['globalwetland_storage'], time_step)

        self.lb_storages['river_storage'].\
            write_daily_ouput(storage_var['river_storage'], time_step)

        # Fluxes
        fluxes_var = value[1]

        self.lb_fluxes['groundwater_discharge'].\
            write_daily_ouput(fluxes_var['groundwater_discharge'], time_step)

        self.lb_fluxes['locallake_outflow'].\
            write_daily_ouput(fluxes_var['locallake_outflow'], time_step)

        self.lb_fluxes['localwetland_outflow'].\
            write_daily_ouput(fluxes_var['localwetland_outflow'], time_step)

        self.lb_fluxes['globallake_outflow'].\
            write_daily_ouput(fluxes_var['globallake_outflow'], time_step)

        self.lb_fluxes['globalwetland_outflow'].\
            write_daily_ouput(fluxes_var['globalwetland_outflow'], time_step)

        self.lb_fluxes['streamflow'].\
            write_daily_ouput(fluxes_var['streamflow'], time_step)

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
        self.lb_storages['groundwater_storage'].\
            to_netcdf('groundwater_storage_' + end_date)

        self.lb_storages['locallake_storage'].\
            to_netcdf('locallake_storage_' + end_date)

        self.lb_storages['localwetland_storage'].\
            to_netcdf('localwetland_storage_' + end_date)

        self.lb_storages['globallake_storage'].\
            to_netcdf('globallake_storage_' + end_date)
        self.lb_storages['globalwetland_storage'].\
            to_netcdf('globalwetland_storage_' + end_date)

        self.lb_storages['river_storage'].\
            to_netcdf('river_storage_' + end_date)

        # =====================================================================
        #                       Fluxes
        # =====================================================================
        # Vertical Water Balance
        self.vb_fluxes['netrad'].to_netcdf('net_radiation_' + end_date)
        self.vb_fluxes['potevap'].to_netcdf('pet_taylor_' + end_date)
        self.vb_fluxes['lai'].to_netcdf('leaf_area_index_' + end_date)
        self.vb_fluxes['canopy_evap'].to_netcdf('canopy_evap_' + end_date)
        self.vb_fluxes['throughfall'].to_netcdf('throughfall_' + end_date)
        self.vb_fluxes['snow_fall'].to_netcdf('snow_fall_' + end_date)
        self.vb_fluxes['snow_melt'].to_netcdf('snow_melt_' + end_date)
        self.vb_fluxes['snow_evap'].to_netcdf('sublimation_' + end_date)
        self.vb_fluxes['groundwater_recharge'].\
            to_netcdf('groundwater_recharge_' + end_date)
        self.vb_fluxes['surface_runoff'].\
            to_netcdf('surface_runoff_' + end_date)

        # Lateral Water Balance
        self.lb_fluxes['groundwater_discharge'].\
            to_netcdf('groundwater_discharge_' + end_date)

        self.lb_fluxes['locallake_outflow'].\
            to_netcdf('locallake_outflow_' + end_date)

        self.lb_fluxes['localwetland_outflow'].\
            to_netcdf('localwetland_outflow_' + end_date)

        self.lb_fluxes['globallake_outflow'].\
            to_netcdf('globallake_outflow_' + end_date)

        self.lb_fluxes['globalwetland_outflow'].\
            to_netcdf('globalwetland_outflow_' + end_date)

        self.lb_fluxes['streamflow'].to_netcdf('streamflow_' + end_date)
