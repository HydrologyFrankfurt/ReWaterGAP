# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Distribute accumulated unstaisfied use to riparian cells."""

# =============================================================================
# This function distributes the accumulated unsatisfied potential net
# abstraction of surface water (SW) from the outflow cell of a global lake
# or reservoir to its riparian cells.
# =============================================================================

from numba import njit
import numpy as np


@njit(cache=True)
def redistritute_to_riparian(prev_accumulated_unsatisfied_potential_netabs_sw,
                             unsat_potnetabs_sw_to_supplycell,
                             accumulated_unsatisfied_potential_netabs_sw,
                             unagregrgated_potential_netabs_sw,
                             potential_netabs_sw, glwdunits, rout_order,
                             unsatisfied_potnetabs_riparian,
                             prev_returned_demand_from_supply_cell,
                             x, y):
    """
    Distribute unsatisfied demand of global lake/reservoir to riparian cells.

    Parameters
    ----------
    prev_accumulated_unsatisfied_potential_netabs_sw : float
        Previous accumulated unsatified potential net abstraction.
        Unit: [km3/day]
    unsat_potnetabs_sw_to_supplycell : float
        Unsatisfied potential net abstraction to supply cell. Unit: [km3/day]
    accumulated_unsatisfied_potential_netabs_sw : float
        Accumulated unsatified potential net abstraction after global lake or
        reservoir satisfaction. Unit: [km3/day]
    unagregrgated_potential_netabs_sw : array
        Potential net abstraction from surface water. Unit: [km3/day]
    potential_netabs_sw : float
        Potential net abstraction from surface water (outflow cells of global
        lakes and reservoirs are aggregated). Unit: [km3/day]
    glwdunits : array
        Global Lakes and Wetlands. Units: [outflow cell and riparian cell]
    rout_order : array
        Routing order
    unsatisfied_potnetabs_riparian : array
        Unsatisfied potential net abstraction from global lake or reservoir outflow cell to riparian cell. Unit: [km3/day]
    prev_returned_demand_from_supply_cell
        Retured demand from supply to demand cell. This is computed in the
        next time step by the supply cell if the supply cell water balance is
        computed before the demand cell. Unit: [km3/day]
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    accum_uns_potnetabs_after_distribution : float
       Accumulated unsatified potential net abstraction after distribution
       from global lake or reservoir outflow cell. Unit: [km3/day]
    unsatisfied_potnetabs_riparian : array
       Unsatisfied potential net abstraction from global lake or reservoir
       outflow cell to riparian cell. Unit: [km3/day]

    """
    # If the daily aggregated demand of global lake or reservoir outflow cells has not been fully satisfied, 
    # the unsatisfied demand is distributed to riparian cells (based on the percentage contribution of each riparian 
    # cell to the aggregated demand). The distributed unsatisfied demand to riparian cells is attempted to be 
    # satisfied in river or lake storage in the current or next time step based on the routing order.

                               
    # The unsatisfied demand to be distributed to the riparian cells is calculated as the difference 
    # between accumulated_unsatisfied_potential_netabs_sw (after global lake and/or reservoir storage) 
    # and the sum of previous accumulated unsatisfied potential net abstraction from surface water 
    # or prev_returned_demand_from_supply_cell (if demand is satisfied in the next time step 
    # by a neighboring cell) and the distributed demand to the supply cell if there is a 
    # neighboring cell water supply option (current cell is a supply cell). 
    # (prev_accumulated_unsatisfied_potential_netabs_sw + unsat_potnetabs_sw_to_supplycell)

    # =========================================================================
    prev_accu_supplycell_demad = unsat_potnetabs_sw_to_supplycell

    if np.nansum(np.array(prev_returned_demand_from_supply_cell)) == 0:
        prev_accu_supplycell_demad += prev_accumulated_unsatisfied_potential_netabs_sw

    else:
        # Logic: If the demand is satisfied in the next time step by neighbouring cell, use
        # returned demand from this neighbour (prev_returned_demand_from_supply_cell);
        # else use the unstatisfied demand from the previous day
        # (prev_accumulated_unsatisfied_potential_netabs_sw).
        prev_accu_supplycell_demad += np.nansum(np.array(prev_returned_demand_from_supply_cell))

    # =========================================================================
    # ------------------------------------------------------------------
    # Special condition!!!:
    # ------------------------------------------------------------------
    # If glwdunit (riparian cells) of current is 1 (the current cell itself),
    # the unsatisfied demand after global lake balance is maintained 
    # else it's distributed to various riparian cells.
    accum_uns_potnetabs_after_distribution = \
        accumulated_unsatisfied_potential_netabs_sw
    # Note that accum_uns_potnetabs_after_distribution will change if there
    # are 2 or more riparian cells (glwdunit >=2).

    # ------------------------------------------------------------------

    # Note! x,y is the index of the outflow cell of a global lake or reservoir
    for i in range(len(rout_order)):
        # Get invidividual riparian cells of global lakes or reservoirs.
        r_x, r_y = rout_order[i]
        if glwdunits[x, y] == glwdunits[r_x, r_y] and (x, y) != (r_x, r_y):

            if accumulated_unsatisfied_potential_netabs_sw - \
                    prev_accu_supplycell_demad > 0:

                # If the potential net abstraction of a global lake or reservoir
                # outflow cell itself is negative or positive,
                # the distribution to riparian cell is done separately.

                if unagregrgated_potential_netabs_sw[x, y] <= 0:
                    # If the current demand of the outflow cell itself is negative (i.e.
                    # return flow to increase storage of outflow cell), then
                    # the unsatisfied demand of the outflow cell itself is the
                    # prev_accu_supplycell_demad.

                    accum_uns_potnetabs_after_distribution = \
                        prev_accu_supplycell_demad

                    if unagregrgated_potential_netabs_sw[r_x, r_y] <= 0:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                    else:
                        # Note: If the demand of the outflowcell itself
                        # is negative, it should be subtracted from the daily
                        # aggregated demand (potential_netabs_sw) before
                        # distribution.
                        unsatisfied_potnetabs_riparian[r_x, r_y] = \
                            (unagregrgated_potential_netabs_sw[r_x, r_y] /
                             (potential_netabs_sw - unagregrgated_potential_netabs_sw[x, y])) * \
                            (accumulated_unsatisfied_potential_netabs_sw -
                             prev_accu_supplycell_demad)
                else:
                    # Note: The 'accum_uns_potnetabs_after_distribution' value
                    # for a global lake or reservoir outflowcell itself will
                    # now consist of its distributed contibution along with
                    # prev_accu_supplycell_demad.
                    accum_uns_potnetabs_after_distribution = \
                        (unagregrgated_potential_netabs_sw[x, y] / potential_netabs_sw) * \
                        (accumulated_unsatisfied_potential_netabs_sw -
                         prev_accu_supplycell_demad) + prev_accu_supplycell_demad

                    if unagregrgated_potential_netabs_sw[r_x, r_y] <= 0:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                    else:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = \
                            (unagregrgated_potential_netabs_sw[r_x, r_y] /
                             potential_netabs_sw) * \
                            (accumulated_unsatisfied_potential_netabs_sw -
                             prev_accu_supplycell_demad)

            else:
                unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                unsatisfied_potnetabs_riparian[x, y] = 0
                accum_uns_potnetabs_after_distribution = \
                    accumulated_unsatisfied_potential_netabs_sw

    return accum_uns_potnetabs_after_distribution, \
        unsatisfied_potnetabs_riparian
