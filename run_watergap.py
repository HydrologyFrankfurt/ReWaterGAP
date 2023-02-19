# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

# =============================================================================
# This module runs WaterGAP for a user selected period by calling both
# vertical and lateral waterbalance functions
# =============================================================================

import numpy as np
from termcolor import colored
from misc.time_checker_and_ascii_image import check_time
from controller import configuration_module as cm
from controller import read_forcings_and_static as rd
from core.verticalwaterbalance import vertical_waterbalance as vb
from core.verticalwaterbalance import parameters as pm
from core.lateralwaterbalance import lateral_waterbalance as lb
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
        pass
    else:
        print('\n' + colored('+++ WaterGAP in Natural Mode +++', 'cyan'))
        print('Period:' + colored(' %s to %s' % (cm.start, cm.end), 'green'))
        print('Temporal resolution:' +
              colored(' %s' % (cm.temporal_res), 'green'))
        # no reserviours are considered here
        # =====================================================================
        # Initialize static data, climate forcings and get data dimensions
        # =====================================================================
        initialize_forcings_static = rd.InitializeForcingsandStaticdata()
        grid_coords = initialize_forcings_static.grid_coords
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
            lb.LateralWaterBalance(initialize_forcings_static, parameters)

        # ====================================================================
        # loop through user defined time
        # ====================================================================
        start_date = np.datetime64(cm.start)
        end_date = np.datetime64(cm.end)

        # check if user inputs larger time period than dataset
        if (grid_coords['time'][-1].values < end_date) or \
                (grid_coords['time'][0].values < start_date):
            raise ValueError(colored('Start or end date of simulation period '
                                     'is not included in the data. '
                                     'Please select valid period', 'red'))

        # getting time range from time input (including the first day).
        time_range = round((end_date - start_date + 1)/np.timedelta64(1, 'D'))

        # =====================================================================
        print('\n' + '++++++++++++++++++++++++++++++++++++++++++++' + '\n' +
              colored('Calculating vertical & lateral water balance', 'cyan') +
              '\n' + '++++++++++++++++++++++++++++++++++++++++++++')
        # =====================================================================

        for time_step, date in zip(range(time_range),
                                   grid_coords['time'].values):
            # =================================================================
            #  computing vertical water balance
            # =================================================================
            vertical_waterbalance.\
                calculate(date,
                          initialize_forcings_static.current_landareafrac,
                          initialize_forcings_static.landareafrac_ratio)

            # Getting daily storages and fluxes and writing to variables
            vb_storages_and_fluxes = \
                vertical_waterbalance.get_storages_and_fluxes()

            create_out_var.\
                verticalbalance_write_daily_var(vb_storages_and_fluxes,
                                                time_step)

            # =================================================================
            #  computing vertical water balance
            # =================================================================

            lateral_waterbalance.\
                calculate(vertical_waterbalance.fluxes['groundwater_recharge'],
                          vertical_waterbalance.fluxes['openwater_PET'],
                          vertical_waterbalance.fluxes['daily_precipitation'],
                          vertical_waterbalance.fluxes['surface_runoff'],
                          vertical_waterbalance.fluxes['daily_storage_transfer'],
                          initialize_forcings_static.current_landareafrac,
                          initialize_forcings_static.previous_landareafrac)

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

        print('Status:' + colored(' complete', 'cyan'))

        # =====================================================================
        # Store ouput variable if selected by user
        # =====================================================================
        create_out_var.save_to_netcdf()


if __name__ == "__main__":
    run()
