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
                                        total_unsatisfied_demand_ripariancell,
                                        rout_order,
                                        returned_demand_from_supplycell,
                                        current_mon_day):
    """
    Distribute unsatisfied demand from supply cell to a demand cell.

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
    unsat_potnetabs_sw_to_supplycell : float
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
    rout_order : array
        order of routing.
    returned_demand_from_supplycell : float
        Demand returned from the supply cell, Unit: [km^3/day].
    current_mon_day : array
        Array indicating the current month and day.

    Returns
    -------
    accumulated_unsatisfied_potnetabs_no_alloc : array
        Unsatisfied demand of Supplycell itself to be allocated to neigbouring cell,
        Unit: [km^3/day]

    returned_demand_from_supplycell: array
        Returned unsatisfied demand from Supplycell to respective demand cell, Unit: [km^3/day]
    unsat_potnetabs_sw_supplycell_to_demandcell: float
       Total or sum of  of all demand to be returned to respective demand cell, 
       Unit: [km^3/day]
    """
    accumulated_unsatisfied_potnetabs_no_alloc = accumulated_unsatisfied_potential_netabs_sw

    # inititialize variable
    unsat_potnetabs_sw_supplycell_to_demandcell = 0

    if unsat_potnetabs_sw_to_supplycell > 0:
        if accumulated_unsatisfied_potential_netabs_sw > 0:
            if total_demand_sw_noallocation > 0:

                # unsatisfied use of the supplycell with use allocated from
                # demand cell
                unsat_potnetabs_sw_withalloc = accumulated_unsatisfied_potential_netabs_sw

                # accumulated unsatisfied use of the supply cell without use
                # allocated from a demand cell (unsatisfied use of supply cell
                # to be allocated)
                accumulated_unsatisfied_potnetabs_no_alloc = \
                    total_demand_sw_noallocation - actual_net_abstraction_sw -\
                    total_unsatisfied_demand_ripariancell

                # Reset accumulated unsatisfied potential net abstraction if it
                # becomes negative. This is because "actual_net_abstraction_sw"
                #  can exceed "total_demand_sw_noallocation"
                if accumulated_unsatisfied_potnetabs_no_alloc < 0:
                    accumulated_unsatisfied_potnetabs_no_alloc = 0

                # unsatisfied use to be allocated to demand cell
                unsat_potnetabs_sw_supplycell_to_demandcell = \
                    unsat_potnetabs_sw_withalloc - accumulated_unsatisfied_potnetabs_no_alloc

            else:
                # In this case, the accumulated_unsatisfied_potential_netabs_sw
                #  at this point only stems from the respective neighboring
                # cells. (Note that here, daily potential net abstraction from
                # surface water is negative.)
                unsat_potnetabs_sw_supplycell_to_demandcell = \
                    accumulated_unsatisfied_potential_netabs_sw

                # Here the unsatisfied use from supply cell is set to zero since
                # unsatisfied use will been returned to demand cell
                accumulated_unsatisfied_potnetabs_no_alloc = 0
        else:
            unsat_potnetabs_sw_supplycell_to_demandcell = 0
            accumulated_unsatisfied_potnetabs_no_alloc = 0


        # Distribute unstisfied demand from supply to demmand cell**
        for i in range(len(rout_order)):
            nb_x, nb_y = rout_order[i]
            if neighbouring_cells_map[nb_x, nb_y][0] == x and\
                    neighbouring_cells_map[nb_x, nb_y][1] == y:

                returned_demand_from_supplycell[nb_x, nb_y] =\
                    unsat_potnetabs_sw_supplycell_to_demandcell *\
                    unsat_potnetabs_sw_from_demandcell[nb_x, nb_y] * \
                    (1 / unsat_potnetabs_sw_to_supplycell)

    return accumulated_unsatisfied_potnetabs_no_alloc, returned_demand_from_supplycell, \
        unsat_potnetabs_sw_supplycell_to_demandcell


# ==============================================================================
# Neigbouring cell identification
# =============================================================================
@njit(cache=True)
def get_neighbouringcell(neigbourcells_for_demandcell,
                         outflowcell_for_neigbourcells,
                         river_storage, loclake_storage, glolake_storage,
                         max_loclake_storage, max_glolake_storage,
                         accumulated_unsatisfied_potential_netabs_sw,
                         reservoir_operation, glores_storage, x, y, current_mon_day,
                         cell_calculated):
    """
    Identify neighboring cells that could supply water to the demand cell.

    Parameters
    ----------
    neigbourcells_for_demandcell : array
       Neigbouring cells for demand cells.
    outflowcell_for_neigbourcells : array
        outflow cells for Neigbouring cells
    river_storage : float
        Daily river storage, Unit: [km^3]
    loclake_storage : float
        daily local lake storage, Unit: [km^3]
    glolake_storage : float
        daily global lake storage, Unit: [km^3]
    max_loclake_storage : float
        Maximum local lake storage, Unit: [km^3]
    max_glolake_storage : float
        Maximum global lake storage, Unit: [km^3]
    accumulated_unsatisfied_potential_netabs_sw : TYPE
        Accumulated unsatified potential net abstraction after satisfaction
        from river or local lake (if any) , Unit: [km^3/day]
    reservoir_operation : boolean 
      True when reservoir are activated in simulation else false.
    glores_storage : float
        Global reservoir storage, Unit: [km^3].
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell
    current_mon_day : array
        Array indicating the current month and day.
    cell_calculated : array
        Indicator if a cell has already been calculated.
    
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

            # Ignore the cells which are not neighbours
            if (neighbourcell_lat == 0) & (neighbourcell_lon == 0):
                pass
            else:
                cell_storage = river_storage[neighbourcell_lat, neighbourcell_lon] +\
                    loclake_storage[neighbourcell_lat, neighbourcell_lon] + \
                    glolake_storage[neighbourcell_lat, neighbourcell_lon] + \
                    max_loclake_storage[neighbourcell_lat, neighbourcell_lon] + \
                    max_glolake_storage[neighbourcell_lat, neighbourcell_lon]

                if reservoir_operation:
                    cell_storage += glores_storage[neighbourcell_lat,
                                                   neighbourcell_lon]

                if cell_storage < 1e-12:  # to counter numerical inaccuracies
                    cell_storage = 0

                if cell_storage > largest_storage_neighbour:

                    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    # Select the neighbour cell only if it's not directly upstream of
                    # the current cell. This is because: 1) extracting water from an
                    # upstream cell would reduce water in the downstream cell, and 2)
                    # downstream cells typically have more water than upstream cells
                    # (except in rare cases).
                    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    if (neighbourcell_outflowcell_lat == x) & \
                            (neighbourcell_outflowcell_lon == y):
                        pass
                    else:
                        largest_storage_neighbour = cell_storage
                        neigbour_cell_x, neigbour_cell_y = \
                            neighbourcell_lat, neighbourcell_lon

        if current_mon_day[0] == 12 and current_mon_day[1] == 31:
            if cell_calculated[neigbour_cell_x, neigbour_cell_y] > cell_calculated[x, y]:
                neigbour_cell_x, neigbour_cell_y = 0, 0

    return neigbour_cell_x, neigbour_cell_y
