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
from tqdm import tqdm
import pandas as pd
from termcolor import colored
from misc.time_checker_and_ascii_image import check_time
from controller import configuration_module as cm
from controller import read_forcings_and_static as rd
from controller import wateruse_handler as wateruse
from core import parameters as pm
from core import land_surfacewater_fraction_init as lwf
from core.lateralwaterbalance import waterbalance_lateral as lb
from core.utility import restart_watergap as restartwatergap
from core.utility import get_upstream_basin as get_basin
from core.verticalwaterbalance import waterbalance_vertical_init as vb
from view import createandwrite as cw


def run(calib_station=None, watergap_basin=None, basin_id=None):
    """
    Run WaterGAP.

    Returns
    -------
    None.

    """
    if cm.ant:
        print('\n' + colored('+++ Antropogenic Run +++', 'cyan'))
        if cm.RESERVOIR_OPT is False:
            print(colored('Use only: Human water use without '
                          'global man-made reservoirs/regulated lakes',
                          'blue'))
        elif cm.SUBTRACT_USE is False:
            print(colored('Reservoirs only: Exclude human water use'
                          ' but include global man-made'
                          ' reservoirs/regulated lakes', 'blue'))
        else:
            print(colored('Standard (ant) run: Include human water'
                          ' use and include global man-made'
                          ' reservoirs/regulated lakes', 'blue'))
        # demand satisfaction option
        if cm.DELAYED_USE and cm.NEIGHBOURING_CELL:
            msg = 'Delayed water supply & Neighboring cell water supply'
        elif cm.DELAYED_USE:
            msg = 'Delayed water supply'
        elif cm.NEIGHBOURING_CELL:
            msg = 'Neighboring cell water supply'
        else:
            msg = 'none (Delayed water supply & Neighboring cell water supply)'
        satisfaction_option =\
            f"Riparian water supply (default) & {msg} option activated."
        print(colored('Demand satisfaction option: ' + satisfaction_option,
                      'blue'))

        print('\nPeriod:' + colored(f'{cm.start} to {cm.end}', 'green'))
        print('Temporal resolution:' +
              colored(f'{cm.TEMPORAL_RES}', 'green'))
        print('Run basin:' +
              colored(f'{cm.run_basin}', 'green'))
    else:
        print('\n' + colored('+++ Naturalised Run +++', 'cyan'))
        print('Note:' + colored(' 1. Reserviors, abstraction from surface and'
                                ' groundwater are not considered.' + '\n'
                                + '      2. Regulated lakes are treated as'
                                '  global lakes ', 'blue'))
        print('\nPeriod:' + colored(f'{cm.start} to {cm.end}', 'green'))
        print('Temporal resolution:' +
              colored(f'{cm.TEMPORAL_RES}', 'green'))
        print('Run basin:' +
              colored(f'{cm.run_basin}', 'green'))

    # Flag to run WaterGAP calibration
    run_calib = cm.run_calib

    # =====================================================================
    # Initialize Restart module for possible restart of WaterGAP
    # =====================================================================
    restart_model = restartwatergap.RestartState(cm.save_and_read_states_path)
    savestate_for_restart = cm.save_states
    restart = cm.restart
    # =====================================================================
    # Initialize static data, climate forcings , wateruse data
    # and get data dimensions
    # =====================================================================
    initialize_forcings_static = rd.InitializeForcingsandStaticdata(run_calib)
    grid_coords = initialize_forcings_static.grid_coords
    potential_net_abstraction = wateruse.Wateruse(cm.SUBTRACT_USE, grid_coords, run_calib)
    parameters = pm.Parameters(run_calib, basin_id)

    # initialize Land surface water Fraction
    land_water_frac = \
        lwf.LandsurfacewaterFraction(initialize_forcings_static.static_data,
                                     cm.RESERVOIR_OPT)

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
                               potential_net_abstraction, parameters,
                               land_water_frac.global_lake_area,
                               land_water_frac.glolake_frac,
                               land_water_frac.loclake_frac)

    # =====================================================================
    # Initialize selected basin or region
    # =====================================================================
    if run_calib and cm.run_basin:
        # calibration run
        pass
    else:
        # run WaterGAP is basin of choice
        streamflow_station = initialize_forcings_static.static_data.stations
        watergap_basin = get_basin.\
            SelectUpstreamBasin(cm.run_basin,
                                initialize_forcings_static.static_data.arc_id,
                                streamflow_station,
                                initialize_forcings_static.static_data.lat_lon_arcid,
                                initialize_forcings_static.static_data.upstream_cells)

    # ====================================================================
    # Get time range for Loop
    # ====================================================================
    start_date = np.datetime64(cm.start)
    end_date = np.datetime64(cm.end)

    # getting time range from time input (including the first day).
    timerange_main = round((end_date - start_date + 1)/np.timedelta64(1, 'D'))

    # format main date for simulation.
    date_main = grid_coords['time'].values.astype('datetime64[D]')

    # Get the first available day for each month (required to load in wateruse
    # data once each month)
    date_df = pd.DataFrame({'dates': pd.to_datetime(date_main)})

    # Extract the year and month to group by month
    date_df['year'] = date_df['dates'].dt.year
    date_df['month'] = date_df['dates'].dt.month
    first_day_of_month = date_df.groupby(['year', 'month']).min()
    first_day_of_month = first_day_of_month.reset_index(drop=True)
    first_day_of_month.rename(columns={'dates': 'First Day'}, inplace=True)
    first_day_of_month = \
        first_day_of_month['First Day'].values.astype('datetime64[D]')

    #               #====================
    #               #   *** Spin up ***
    #               #====================

    # getting time range for spin up
    spin_up = cm.spinup_years
    end_spinup = np.datetime64(cm.start.split('-')[0]+'-12-31')
    time_range = \
        round((end_spinup - start_date + 1)/np.timedelta64(1, 'D'))

    spin_start = np.where(date_main == start_date)[0].item()
    spin_end = 1 + np.where(date_main == end_spinup)[0].item()

    #  if there is spinup, simulation date will start with the spinup years.
    simulation_date = date_main[spin_start:spin_end]

    # *********************************************************************
    print('\n' + '++++++++++++++++++++++++++++++++++++++++++++' + '\n' +
          colored('Calculating vertical & lateral water balance', 'cyan') +
          '\n' + '++++++++++++++++++++++++++++++++++++++++++++')
    # *********************************************************************
    # =================================================================
    # Update model paramters for restart if option is selected
    # =================================================================
    if restart:
        date_before_restart = str(start_date - np.timedelta64(1, 'D'))
        restart_data = restart_model.load_restart_info(date_before_restart)
        print(colored('Date of previous WaterGAP run: ' +
                      str(restart_data["last_date"]), 'blue'))
        print(colored('Restart date: ' +
                      str(start_date) + '\n', 'green'))

        land_water_frac.\
            update_landfrac_for_restart(restart_data["landfrac_state"])
        vertical_waterbalance.\
            update_vertbal_for_restart(restart_data["vert_bal_states"])
        lateral_waterbalance.\
            update_latbal_for_restart(restart_data["lat_bal_states"])

    #                  ====================================
    #                  ||   Main Loop for all processes  ||
    #                  ====================================
    get_annual_streamflow = []  # for calibration purpose only
    get_annual_pot_cell_runoff = []  # for calibration purpose only
    end_main_loop = False
    while True:
        print('Spin up phase: ' + colored(str(spin_up), 'cyan'))
        if spin_up == 0:
            print(colored('Spin up phase over. Starting simulation from ' +
                          cm.start + ':' + cm.end + '\n', 'cyan'))
            time_range = timerange_main
            simulation_date = date_main
        for time_step, date in tqdm(zip(range(time_range), simulation_date),
                                    total=(time_range-1), desc="Processing",
                                    disable=run_calib):

            # =================================================================
            #  Get Land area fraction and reservoirs respective years
            # =================================================================
            # Activate reservoirs for current year
            lateral_waterbalance.\
                activate_res_area_storage_capacity(date, cm.RESERVOIR_OPT_YEARS,
                                                   restart)

            # Get Land area fraction
            land_water_frac.\
                landareafrac_with_reservior(date, cm.RESERVOIR_OPT_YEARS)

            # Get land and water fractions (used to calculate total PET)
            land_water_frac.get_land_and_water_freq(date)

            # Adapt global reservoir storage and land area fraction
            # due to net change in land fraction
            lateral_waterbalance.glores_storage = land_water_frac.\
                adapt_glores_storage(vertical_waterbalance.canopy_storage,
                                     vertical_waterbalance.snow_water_storage,
                                     vertical_waterbalance.soil_water_content,
                                     lateral_waterbalance.glores_area,
                                     lateral_waterbalance.glores_storage)

            # =================================================================
            #  Computing vertical water balance
            # =================================================================
            vertical_waterbalance.\
                calculate(date, land_water_frac.current_landareafrac,
                          land_water_frac.landareafrac_ratio,
                          watergap_basin.upstream_basin,
                          land_water_frac.water_freq,
                          land_water_frac.land_freq)

            # =================================================================
            #  Computing lateral water balance
            # =================================================================
            lateral_waterbalance.\
                calculate(vertical_waterbalance.fluxes['groundwater_recharge'],
                          vertical_waterbalance.fluxes['openwater_PET'],
                          vertical_waterbalance.fluxes['daily_precipitation'],
                          vertical_waterbalance.fluxes['surface_runoff'],
                          vertical_waterbalance.fluxes['daily_storage_transfer'],
                          vertical_waterbalance.fluxes['land_aet_corr'],
                          land_water_frac.current_landareafrac,
                          land_water_frac.previous_landareafrac,
                          land_water_frac.landwaterfrac_excl_glolake_res,
                          date, first_day_of_month, watergap_basin.upstream_basin,
                          vertical_waterbalance.fluxes['sum_canopy_snow_soil_storage'],
                          run_calib)

            # =================================================================
            #  Update Land Area Fraction
            # =================================================================
            land_swb_fraction = lateral_waterbalance.get_new_swb_fraction()
            land_water_frac.update_landareafrac(land_swb_fraction)

            if spin_up == 0:
                # =============================================================
                # Write vertical and lateralbalacne variables to file
                # =============================================================
                sim_month = pd.to_datetime(date).month
                sim_day = pd.to_datetime(date).day
                sim_year = pd.to_datetime(date).year
                # Getting daily storages and fluxes and writing to variables
                vb_storages_and_fluxes = \
                    vertical_waterbalance.get_storages_and_fluxes()

                create_out_var.\
                    verticalbalance_write_daily_var(vb_storages_and_fluxes,
                                                    time_step, sim_year,
                                                    sim_month, sim_day)

                # Getting daily storages and fluxes and writing to variables
                lb_storages_and_fluxes = \
                    lateral_waterbalance.get_storages_and_fluxes()

                create_out_var.\
                    lateralbalance_write_daily_var(lb_storages_and_fluxes,
                                                   time_step, sim_year,
                                                   sim_month, sim_day)

                # =============================================================
                # Store ouput variable if selected by user
                # =============================================================
                #  store data yearly or if end date of simulation period is
                # reached (eg. is data is less than a year)
                if (pd.to_datetime(date).month == 12 and
                        pd.to_datetime(date).day == 31) or end_date == \
                        date.astype('datetime64[D]'):
                    save_year = date.astype('datetime64[D]')

                    if run_calib:
                        annual_streamflow = create_out_var.lb_fluxes['dis'].data.\
                            sel(lat=calib_station["lat"].values, lon=calib_station["lon"].values)

                        # km3/year for station
                        annual_streamflow = annual_streamflow.dis.resample(time='Y').sum().values
                        get_annual_streamflow.append(annual_streamflow[0][0][0])

                        annual_pot_cell_runoff = create_out_var.lb_fluxes['pot_cell_runoff'].data
                        annual_pot_cell_runoff = annual_pot_cell_runoff.pot_cell_runoff.\
                            resample(time='Y').sum(skipna=False)
                        annual_pot_cell_runoff.attrs['units'] = "km3/year"
                        get_annual_pot_cell_runoff.append(annual_pot_cell_runoff)
                    else:
                        print(f'\nWriting data for {save_year} to NetCDF\n')

                        create_out_var.base_units(initialize_forcings_static.static_data.cell_area,
                                                  initialize_forcings_static.static_data.
                                                  land_surface_water_fraction.contfrac)

                        create_out_var.save_netcdf_parallel(str(save_year))

                # =============================================================
                #  Get restart information if restart is needed.
                # =============================================================
                if end_date == date.astype('datetime64[D]'):
                    if savestate_for_restart:
                        restart_model.\
                            savestate(date,
                                      land_water_frac.current_landareafrac,
                                      land_water_frac.previous_landareafrac,
                                      land_water_frac.landareafrac_ratio,
                                      land_water_frac.previous_swb_frac,
                                      land_water_frac.glores_frac_prevyear,
                                      land_water_frac.gloresfrac_change,
                                      land_water_frac.init_landfrac_res_flag,
                                      land_water_frac.landwaterfrac_excl_glolake_res,
                                      land_water_frac.land_and_water_freq_flag,
                                      land_water_frac.water_freq,
                                      land_water_frac.land_freq,
                                      land_water_frac.updated_loclake_frac,

                                      vertical_waterbalance.lai_days,
                                      vertical_waterbalance.cum_precipitation,
                                      vertical_waterbalance.growth_status,
                                      vertical_waterbalance.canopy_storage,
                                      vertical_waterbalance.snow_water_storage,
                                      vertical_waterbalance.snow_water_storage_subgrid,
                                      vertical_waterbalance.soil_water_content,
                                      vertical_waterbalance.daily_storage_transfer,

                                      lateral_waterbalance.groundwater_storage,
                                      lateral_waterbalance.loclake_storage,
                                      lateral_waterbalance.locwet_storage,
                                      lateral_waterbalance.glolake_storage,
                                      lateral_waterbalance.glowet_storage,
                                      lateral_waterbalance.river_storage,

                                      lateral_waterbalance.glores_storage,
                                      lateral_waterbalance.k_release,
                                      lateral_waterbalance.unsatisfied_potential_netabs_riparian,
                                      lateral_waterbalance.unsat_potnetabs_sw_from_demandcell,
                                      lateral_waterbalance.unsat_potnetabs_sw_to_supplycell,
                                      lateral_waterbalance.get_neighbouring_cells_map,
                                      lateral_waterbalance.\
                                          accumulated_unsatisfied_potential_netabs_sw,

                                      lateral_waterbalance.daily_unsatisfied_pot_nas,
                                      lateral_waterbalance.\
                                          prev_accumulated_unsatisfied_potential_netabs_sw,
                                      lateral_waterbalance.prev_potential_water_withdrawal_sw_irri,
                                      lateral_waterbalance.prev_potential_consumptive_use_sw_irri,
                                      lateral_waterbalance.set_res_storage_flag
                                      )

                if end_date == date.astype('datetime64[D]'):
                    end_main_loop = True
                    break

        if spin_up != 0:
            spin_up -= 1

        if end_main_loop:
            print('Status:' + colored(' complete', 'cyan'))
            break

    if run_calib:
        sim_data_calib = {"sim_dis": get_annual_streamflow,
                          "pot_cell_runoff": get_annual_pot_cell_runoff}
        return sim_data_calib


if __name__ == "__main__":
    run_with_time_check = check_time(run)
    run_with_time_check()
