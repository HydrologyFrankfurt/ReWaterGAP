# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"neighbouring cell water supply algorithm"

# =============================================================================
# This function selects a neighbouring cell with high water availability
# (lakes and rivers) and distributes the unsatisfied demand from demand cell
# to supply cell for satisfaction.
#  If there remains unsatisfied demand in the supply cell,
# it is returned back to the original demand cell.
# =============================================================================

from numba import njit

# =============================================================================
# Distribution of unstaified potential net abstraction to neighbouring cells
# =============================================================================
# Rationale:
# First priority: Satisfy water demand of cell[x, y] (from water storage in
# cell[x, y]).
# Second priority: Satisfy water demand allocated from neighboring cell(s)
# (from water storage in cell [x, y]).


@njit(cache=True)
def allocate_unsat_demand_to_demandcell(x, y,
                                        neighbouring_cells_map,
                                        accumulated_unsatisfied_potential_netabs_sw,
                                        unsat_potnetabs_sw_from_demandcell,
                                        unsat_potnetabs_sw_to_supplycell,
                                        total_demand_sw_noallocation,
                                        actual_net_abstraction_sw,
                                        total_unsatisfied_demand_ripariancell):
    """
    Allocate unsatisfied demand from a demand cell to neighboring supply cells.

    Parameters
    ----------
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell
    neighbouring_cells_map : array
        Mapping of neighboring cells
    accumulated_unsatisfied_potential_netabs_sw : array
        Accumulated unsatified potential net abstraction after satisfaction
        from river or local lake (if any) , Unit: [km^3/day]
    unsat_potnetabs_sw_from_demandcell : array
       Unsatisfied potential net abstraction from demand cell, Unit: [km^3/day]
    unsat_potnetabs_sw_to_supplycell : array
       Unsatisfied potential net abstraction to supply cell, Unit: [km^3/day]
    total_demand_sw_noallocation : float
        Total demand without demand allocation (include only previous
        accumulated unsatified potential net abstraction from surface water,
        Unsatisfied demand from riparian cell, current daily potential net
        abstraction from surface water), Unit: [km^3/day]
    actual_net_abstraction_sw : float
        accumulated actual net abstraction from surface water, Unit: [km^3/day]
    total_unsatisfied_demand_ripariancell : float
        Sum of daily unstaisfied ripariancell demand, Unit: [km^3/day]

    Returns
    -------
    accumulated_unsatisfied_potential_netabs_sw : array
        returned unsatisfied demand from Supplycell, Unit: [km^3/day]

    """
    if unsat_potnetabs_sw_to_supplycell[x, y] > 0:
        if accumulated_unsatisfied_potential_netabs_sw[x, y] > 0:
            if total_demand_sw_noallocation > 0:

                # unsatisfied use of the supplycell with use allocated from
                # demand cell
                unsat_potnetabs_sw_withalloc = \
                    accumulated_unsatisfied_potential_netabs_sw[x, y]

                # accumulated unsatisfied use of the supply cell without use
                # allocated from a demand cell
                accumulated_unsatisfied_potential_netabs_sw[x, y] = \
                    total_demand_sw_noallocation - actual_net_abstraction_sw -\
                    total_unsatisfied_demand_ripariancell

                # Reset accumulated unsatisfied potential net abstraction if it
                # becomes negative. This is because "actual_net_abstraction_sw"
                #  can exceed "total_demand_sw_noallocation"
                if accumulated_unsatisfied_potential_netabs_sw[x, y] < 0:
                    accumulated_unsatisfied_potential_netabs_sw[x, y] = 0.

                # unsatisfied use to be allocated to demand cell
                unsat_potnetabs_sw_supplycell_to_demandcell = \
                    unsat_potnetabs_sw_withalloc - \
                    accumulated_unsatisfied_potential_netabs_sw[x, y]

            else:
                # In this case, the accumulated_unsatisfied_potential_netabs_sw
                #  at this point only stems from the respective neighboring
                # cells.
                unsat_potnetabs_sw_supplycell_to_demandcell = \
                    accumulated_unsatisfied_potential_netabs_sw[x, y]

                # Here the unsatisfied usefrom supply cell is set to zero since
                # unsatisfied use will been returned to demand cell
                accumulated_unsatisfied_potential_netabs_sw[x, y] = 0
        else:
            unsat_potnetabs_sw_supplycell_to_demandcell = 0

        # Get demand cell for supply cell
        demandcell_lat = neighbouring_cells_map[x, y][0]
        demandcell_lon = neighbouring_cells_map[x, y][1]

        if (demandcell_lat != 0) & (demandcell_lon != 0):
            accumulated_unsatisfied_potential_netabs_sw[demandcell_lat, demandcell_lon] =\
                unsat_potnetabs_sw_supplycell_to_demandcell *\
                unsat_potnetabs_sw_from_demandcell[demandcell_lat, demandcell_lon] * \
                (1 / unsat_potnetabs_sw_to_supplycell[x, y])

    return accumulated_unsatisfied_potential_netabs_sw


# ==============================================================================
# Neigbouring cell identification
# =============================================================================
@njit(cache=True)
def get_neighbouringcell(neigbourcells_for_demandcell,
                         outflowcell_for_neigbourcells,
                         river_storage, loclake_storage, glolake_storage,
                         max_loclake_storage, max_glolake_storage,
                         accumulated_unsatisfied_potential_netabs_sw,
                         x, y):
    """
    Identify neighboring cells that could supply water to the demand cell.

    Parameters
    ----------
    neigbourcells_for_demandcell : array
       Neigbouring cells for demand cells.
    outflowcell_for_neigbourcells : array
        outflow cells for Neigbouring cells
    river_storage : float
        Daily river storage, Unit: [km^3/day]
    loclake_storage : float
        daily local lake storage, Unit: [km3]
    glolake_storage : float
        daily global lake storage, Unit: [km3]
    max_loclake_storage : float
        Maximum local lake storage, Unit: [km3]
    max_glolake_storage : float
        Maximum global lake storage, Unit: [km3]
    accumulated_unsatisfied_potential_netabs_sw : TYPE
        Accumulated unsatified potential net abstraction after satisfaction
        from river or local lake (if any) , Unit: [km^3/day]
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    neigbour_cell_x : int
        Latitude index of selected neighboiring cell
    neigbour_cell_y : int
        Longitude index of selected neighboiring cell

    """
    # index of selected neighboiring cell (intially zero)
    neigbour_cell_x, neigbour_cell_y = 0, 0
    if accumulated_unsatisfied_potential_netabs_sw > 0:
        largest_storage_neighbour = 0.0

        # Loop through each pair of lat and lon indices
        for i in range(0, len(neigbourcells_for_demandcell), 2):
            neighbourcell_lat, neighbourcell_lon = \
                neigbourcells_for_demandcell[i], neigbourcells_for_demandcell[i+1]

            neighbourcell_outflowcell_lat, neighbourcell_outflowcell_lon = \
                outflowcell_for_neigbourcells[i], outflowcell_for_neigbourcells[i+1]

            # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            # Select the neighbour cell only if it's not directly upstream of
            # the current cell. This is because: 1) extracting water from an
            # upstream cell would reduce water in the downstream cell, and 2)
            # downstream cells typically have more water than upstream cells
            # (except in rare cases).

            if (neighbourcell_outflowcell_lat == x) & \
                    (neighbourcell_outflowcell_lon == y):
                continue

            # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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
