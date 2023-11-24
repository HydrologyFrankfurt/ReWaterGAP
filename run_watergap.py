# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Run WaterGAP."""
# =============================================================================
# This module runs WaterGAP for a user selected period by calling both
# vertical and lateral waterbalance functions
# =============================================================================

import numpy as np
from termcolor import colored
from misc.time_checker_and_ascii_image import check_time
from controller import configuration_module as cm
from controller import read_forcings_and_static as rd
from controller import wateruse_handler as wateruse
from core.verticalwaterbalance import vertical_waterbalance as vb
from core.verticalwaterbalance import parameters as pm
from core.lateralwaterbalance import lateral_waterbalance as lb
from core.utility import restart_watergap as restartwatergap
from view import createandwrite as cw


@check_time
def run():
    """
    Run WaterGAP.

    Returns
    -------
    None.

    """
    if cm.ant is True:
        print('\n' + colored('+++ Antropogenic Run +++', 'cyan'))
        if cm.reservior_opt is False:
            print(colored('Use only: Human water use without '
                          'global man-made reservoirs/regulated lakes',
                          'blue'))
        elif cm.subtract_use is False:
            print(colored('Reservoirs only: Exclude human water use'
                          ' but include global man-made'
                          ' reservoirs/regulated lakes', 'blue'))
        else:
            print(colored('Standard (ant) run: Include human water'
                          ' use and include global man-made'
                          ' reservoirs/regulated lakes', 'blue'))
        # demand satisfaction option
        if cm.delayed_use and cm.neighbouringcell:
            msg = 'Delayed water supply & Neighboring cell water supply'
        elif cm.delayed_use:
            msg = 'Delayed water supply'
        elif cm.neighbouringcell:
            msg = 'Neighboring cell water supply'

        satisfaction_option =\
            f"Riparian water supply (default) & {msg} option activated."
        print(colored('Demand satisfaction option: ' + satisfaction_option,
                      'blue'))

        print('\nPeriod:' + colored(' %s to %s' % (cm.start, cm.end), 'green'))
        print('Temporal resolution:' +
              colored(' %s' % (cm.temporal_res), 'green'))
    else:
        print('\n' + colored('+++ Naturalised Run +++', 'cyan'))
        print('Note:' + colored(' 1. Reserviors, abstraction from surface and'
                                ' groundwater are not considered.' + '\n'
                                + '      2. Regulated lakes are treated as'
                                '  global lakes ', 'blue'))
        print('\nPeriod:' + colored(' %s to %s' % (cm.start, cm.end), 'green'))
        print('Temporal resolution:' +
              colored(' %s' % (cm.temporal_res), 'green'))

    # =====================================================================
    # Initialize Restart module for possible restart of WaterGAP
    # =====================================================================
    restart_model = restartwatergap.RestartState()
    savestate_for_restart = cm.save_states
    restart = cm.restart
    # =====================================================================
    # Initialize static data, climate forcings , wateruse data
    # and get data dimensions
    # =====================================================================
    initialize_forcings_static = rd.InitializeForcingsandStaticdata()
    grid_coords = initialize_forcings_static.grid_coords
    potential_net_abstraction = wateruse.Wateruse(cm.subtract_use, grid_coords)
    parameters = pm.Parameters()

    # =====================================================================
    #  Create and write to ouput variable if selected by user
    # =====================================================================
    create_out_var = cw.CreateandWritetoVariables(grid_coords)

    # =====================================================================
    # Initialize Vertical Water Balance
    # =====================================================================
    vertical_waterbalance = \
        vb.VerticalWaterBalance(initialize_forcings_static, parameters)

    # =====================================================================
    # Initialize Lateral Water Balance
    # =====================================================================
    lateral_waterbalance = \
        lb.LateralWaterBalance(initialize_forcings_static,
                               potential_net_abstraction, parameters)

    # ====================================================================
    # Get time range for Loop
    # ====================================================================
    start_date = np.datetime64(cm.start)
    end_date = np.datetime64(cm.end)

    # check if user inputs larger time period than dataset
    if (grid_coords['time'][-1].values.astype('datetime64[D]') < end_date) or \
            (grid_coords['time'][0].values.astype('datetime64[D]') < start_date):
        raise ValueError(colored('Start or end date of simulation period '
                                 'is not included in the data. '
                                 'Please select valid period', 'red'))

    # getting time range from time input (including the first day).
    timerange_main = round((end_date - start_date + 1)/np.timedelta64(1, 'D'))
    date_main = grid_coords['time'].values

    #               #====================
    #               #   *** Spin up ***
    #               #====================

    # getting time range for spin up
    spin_up = cm.spinup_years
    end_spinup = np.datetime64(cm.start.split('-')[0]+'-12-31')
    time_range = \
        round((end_spinup - start_date + 1)/np.timedelta64(1, 'D'))

    spin_start = np.where(grid_coords['time'].values.astype('datetime64[D]') == start_date)[0].item()
    spin_end = 1 + np.where(grid_coords['time'].values.astype('datetime64[D]') == end_spinup)[0].item()

    #  if there is spinup, simulation date will start with the spinup years.
    simulation_date = grid_coords['time'].values[spin_start:spin_end]

    # *********************************************************************
    print('\n' + '++++++++++++++++++++++++++++++++++++++++++++' + '\n' +
          colored('Calculating vertical & lateral water balance', 'cyan') +
          '\n' + '++++++++++++++++++++++++++++++++++++++++++++')
    # *********************************************************************
    # =================================================================
    # Update model paramters for restart if option is selected
    # =================================================================
    if restart is True:
        previous_date = str(start_date - np.timedelta64(1, 'D'))
        restart_data = restart_model.load_restart_info(previous_date)
        print(colored('Date of previous WaterGAP run: ' +
                      str(restart_data["last_date"]), 'blue'))
        print(colored('Restart date: ' +
                      str(start_date) + '\n', 'green'))

        initialize_forcings_static.\
            update_landfrac_for_restart(restart_data["landfrac_state"])
        vertical_waterbalance.\
            update_vertbal_for_restart(restart_data["vert_bal_states"])
        lateral_waterbalance.\
            update_latbal_for_restart(restart_data["lat_bal_states"])

    #                  ====================================
    #                  ||   Main Loop for all processes  ||
    #                  ====================================
    while True:
        print('Spin up phase: ' + colored(spin_up, 'cyan'))
        if spin_up == 0:
            print(colored('Spin up phase over. Starting simulation from ' +
                          cm.start + ':' + cm.end + '\n', 'cyan'))
            time_range = timerange_main
            simulation_date = date_main
        for time_step, date in zip(range(time_range), simulation_date):
            # =================================================================
            #  Get Land area fraction and reservoirs respective years
            # =================================================================
            # Get Land area fraction
            initialize_forcings_static.\
                landareafrac_with_reservior(date, cm.reservoir_opt_years)
            # Activate reservoirs for current year
            lateral_waterbalance.\
                activate_res_area_storage_capacity(date, cm.reservoir_opt_years)

            # =================================================================
            #  Computing vertical water balance
            # =================================================================
            vertical_waterbalance.\
                calculate(date,
                          initialize_forcings_static.current_landareafrac,
                          initialize_forcings_static.landareafrac_ratio)

            # =================================================================
            #  Computing lateral water balance
            # =================================================================
            lateral_waterbalance.\
                calculate(vertical_waterbalance.fluxes['groundwater_recharge'],
                          vertical_waterbalance.fluxes['openwater_PET'],
                          vertical_waterbalance.fluxes['daily_precipitation'],
                          vertical_waterbalance.fluxes['surface_runoff'],
                          vertical_waterbalance.fluxes['daily_storage_transfer'],
                          initialize_forcings_static.current_landareafrac,
                          initialize_forcings_static.previous_landareafrac,
                          date)
            if spin_up == 0:
                # =============================================================
                # Write vertical and lateralbalacne variables to file
                # =============================================================
                # Getting daily storages and fluxes and writing to variables
                vb_storages_and_fluxes = \
                    vertical_waterbalance.get_storages_and_fluxes()

                create_out_var.\
                    verticalbalance_write_daily_var(vb_storages_and_fluxes,
                                                    time_step)

                # Getting daily storages and fluxes and writing to variables
                lb_storages_and_fluxes = \
                    lateral_waterbalance.get_storages_and_fluxes()

                create_out_var.\
                    lateralbalance_write_daily_var(lb_storages_and_fluxes,
                                                   time_step)
            # =================================================================
            #  Update Land Area Fraction
            # =================================================================
            land_swb_fraction = lateral_waterbalance.get_new_swb_fraction()
            initialize_forcings_static.update_landareafrac(land_swb_fraction)

        if end_date == date.astype('datetime64[D]') and spin_up == 0:
            print('Status:' + colored(' complete', 'cyan'))

            # =================================================================
            #  Get restart information if restart is needed.
            # =================================================================
            if savestate_for_restart is True:
                restart_model.\
                    savestate(date,
                              initialize_forcings_static.current_landareafrac,
                              initialize_forcings_static.previous_landareafrac,
                              initialize_forcings_static.landareafrac_ratio,
                              initialize_forcings_static.previous_swb_frac,
                              vertical_waterbalance.lai_days,
                              vertical_waterbalance.cum_precipitation,
                              vertical_waterbalance.growth_status,
                              vertical_waterbalance.canopy_storage,
                              vertical_waterbalance.snow_water_storage,
                              vertical_waterbalance.snow_water_storage_subgrid,
                              vertical_waterbalance.soil_water_content,
                              lateral_waterbalance.groundwater_storage,
                              lateral_waterbalance.loclake_storage,
                              lateral_waterbalance.locwet_storage,
                              lateral_waterbalance.glolake_storage,
                              lateral_waterbalance.glowet_storage,
                              lateral_waterbalance.river_storage)

            # =================================================================
            # Store ouput variable if selected by user
            # =================================================================
            create_out_var.save_to_netcdf(str(end_date))

            break
        else:
            spin_up -= 1


if __name__ == "__main__":
    run()
