# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"neighbouring cell algorithm"


import numpy as np
from numba import njit


@njit(cache=True)
def neighbouring_cell(cells, Outflowcell_for_neigbourcells,
                      river_storage, loclake_storage, glolake_storage,
                      max_loclake_storage, max_glolake_storage, x, y):
    #
    largest_storage_neighbour = 0.0
    neigbour_cell_x, neigbour_cell_y = 0, 0
    # Loop through each pair of lat and lon indices

    for i in range(0, len(cells), 2):
        neighbourcell_lat, neighbourcell_lon = cells[i], cells[i+1]

        neighbourcell_outflowcell_lat, neighbourcell_outflowcell_lon = \
            Outflowcell_for_neigbourcells[i], Outflowcell_for_neigbourcells[i+1]

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Select the neighbour cell only if it's not directly upstream of the
        # current cell- This is because: 1) extracting water from an upstream
        # cell would reduce water in the downstream cell, and 2) downstream
        # cells typically have more water than upstream cells (except in rare
        # cases).

        if (neighbourcell_outflowcell_lat == x) & \
                (neighbourcell_outflowcell_lon == y):
            continue

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Ignore the cells which are not neighbours
        if (neighbourcell_lat == 0) & (neighbourcell_lon == 0):
            continue

        cell_storage = river_storage[neighbourcell_lat, neighbourcell_lon] +\
            loclake_storage[neighbourcell_lat, neighbourcell_lon] + \
            glolake_storage[neighbourcell_lat, neighbourcell_lon] + \
            max_loclake_storage[neighbourcell_lat, neighbourcell_lon] + \
            max_glolake_storage[neighbourcell_lat, neighbourcell_lon]

        # if cm.res_opt is True:
        #     cell_storage += global_reservior_storage[cell_lat, cell_lon]

        if cell_storage > largest_storage_neighbour:
            largest_storage_neighbour = cell_storage
            neigbour_cell_x, neigbour_cell_y = \
                neighbourcell_lat, neighbourcell_lon

    return neigbour_cell_x, neigbour_cell_y