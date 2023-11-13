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
def create_rout_order_dict(rout_order):
    rout_order_dict = {}
    for i in range(rout_order.shape[0]):
        lat, lon = rout_order[i, 0], rout_order[i, 1]
        rout_order_dict[(lat, lon)] = i
    return rout_order_dict

@njit(cache=True)
def neighbouring_cell(cells, river_storage, loclake_storage, glolake_storage,
                      loclake_maxstorage, glolake_maxstorage, rout_order,
                      outflowcell, x, y):
    #
    largest_storage_neighbour = 0.0
    neigbour_cell_x, neigbour_cell_y = 0, 0
    # Loop through each pair of lat and lon indices
    rout_order_dict = create_rout_order_dict(rout_order)
    """
    for i in range(0, len(cells), 2):
        cell_lat, cell_lon = cells[i], cells[i+1]

        # get outflow cell for respective neighbourcell
        index_outflowcell = np.where((rout_order[:, 0] == cell_lat) &
                                      (rout_order[:, 1] == cell_lon))
        outflowcell_lat, outflowcell_lon = outflowcell[index_outflowcell]

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Select the neighbour cell only if it's not directly upstream of the
        # current cell- This is because: 1) extracting water from an upstream
        # cell would reduce water in the downstream cell, and 2) downstream
        # cells typically have more water than upstream cells (except in rare
        # cases).

        if (outflowcell_lat == x) & (outflowcell_lon == y):
            continue

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Ignore the cells which are not neighbours
        if (cell_lat == 0) & (cell_lon == 0):
            continue

        cell_storage = river_storage[cell_lat, cell_lon] + loclake_storage[cell_lat, cell_lon] + \
            glolake_storage[cell_lat, cell_lon] #+ #loclake_maxstorage[cell_lat, cell_lon] + \
            #glolake_maxstorage[cell_lat, cell_lon]

        # if cm.res_opt is True:
        #     cell_storage += global_reservior_storage[cell_lat, cell_lon]

        if cell_storage > largest_storage_neighbour:
            largest_storage_neighbour = cell_storage
            neigbour_cell_x, neigbour_cell_y = cell_lat, cell_lon"""

    return neigbour_cell_x, neigbour_cell_y