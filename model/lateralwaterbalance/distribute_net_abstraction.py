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
# or reservoir to its riparian cells,
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
        previous accumulated unsatified potential net abstraction,
        Unit: [km^3/day]
    unsat_potnetabs_sw_to_supplycell : float
        Unsatisfied potential net abstraction to supply cell, Unit: [km^3/day]
    accumulated_unsatisfied_potential_netabs_sw : float
        accumulated unsatified potential net abstraction after global lake or
        reservoir satisfaction, Unit: [km^3/day]
    unagregrgated_potential_netabs_sw : array
        potential net abstraction from surface water,  Unit: [km^3/day]
    potential_netabs_sw : float
        potential net abstraction from surface water (outflow cells of global
        lake and reservoir are aggregated),  Unit: [km^3/day]
    glwdunits : array
        Global Lakes and Wetlands units (outflow cell and riparian cell)
    rout_order : array
        routing order
    unsatisfied_potnetabs_riparian : array
        Unsatisfied potential net abstraction from global lake or reservoir
        outflow cell to riparian cell, Unit: [km^3/day]
    prev_returned_demand_from_supply_cell
        Retured demand from supply to demand cell.  This is computed in the
        next time step by supply cell if supply cell water balance is
        computed before demand cell, Unit: [km^3/day]
    x : int
        Latitude index of cell
    y : int
        Longitude index of cell

    Returns
    -------
    accum_uns_potnetabs_after_distribution : float
       accumulated unsatified potential net abstraction after distribution
       from global lake or reservoir outflow cell, [km^3/day]
    unsatisfied_potnetabs_riparian : array
       Unsatisfied potential net abstraction from global lake or reservoir
       outflow cell to riparian cell, [km^3/day]

    """
    # If daily aggregated demand of global lake or reservoir outflowcell
    # have not been fully satisfied,  the unstaisfied demand is distributed
    # riparian cells (based on percentage contribution of each riparian
    # cell to aggregated demand). The distributed unsatisfied demand to
    # riparian cells are attempted to be satisfied in river or lake storage in
    # current or next time step based on routing order.

    # The unsatisfied demand to be distributed to the riparian cells  is
    # calculated as the difference
    # between accumulated_unsatisfied_potential_netabs_sw
    # (after global lake and or reservoir storage)  and the sum of
    # previous accumulated unsatisfied potential net abstraction from
    # surface water or prev_returned_demand_from_supply_cell (if demand is
    # satisfied in next time step by neighbour cell)
    # and the distributed demand to supply cell if there is
    # neigbouring cell water supply option(current cell is suuply cell).
    # (prev_accumulated_unsatisfied_potential_netabs_sw +
    # unsat_potnetabs_sw_to_supplycell)

    # =========================================================================
    prev_accu_supplycell_demad = unsat_potnetabs_sw_to_supplycell

    if np.nansum(np.array(prev_returned_demand_from_supply_cell)) == 0:
        prev_accu_supplycell_demad += prev_accumulated_unsatisfied_potential_netabs_sw

    else:
        # logic: if demand is satisfied in next time step by neighbour cell use
        # returned demand from this neighbour (prev_returned_demand_from_supply_cell)
        # else use the unstatisfied demand from previous day
        # (prev_accumulated_unsatisfied_potential_netabs_sw)
        prev_accu_supplycell_demad += np.nansum(np.array(prev_returned_demand_from_supply_cell))

    # =========================================================================
    # ------------------------------------------------------------------
    # Special condition!!!:
    # ------------------------------------------------------------------
    # if glwdunit (riparian cells) of current is 1 (the current cell itself),
    # unsatisfied demand after global lake balance is maintained else
    # it's distributed to various riparian cell.
    accum_uns_potnetabs_after_distribution = \
        accumulated_unsatisfied_potential_netabs_sw
    # Note that accum_uns_potnetabs_after_distribution will change if there
    # are 2 or more riparian cell (glwdunit >=2)

    # ------------------------------------------------------------------

    # Note! x,y is index of outflow cell of a global lake or reservoir
    for i in range(len(rout_order)):
        # Get invidividual riparian cells of global lakes or reservoir.
        r_x, r_y = rout_order[i]
        if glwdunits[x, y] == glwdunits[r_x, r_y] and (x, y) != (r_x, r_y):

            if accumulated_unsatisfied_potential_netabs_sw - \
                    prev_accu_supplycell_demad > 0:

                # If the potential net abstraction of global lake or reservoir
                # outflow cell itself is negative or positive,
                # distribution to riparian cell is done separately.

                if unagregrgated_potential_netabs_sw[x, y] <= 0:
                    # if current demand of outflow cell itself is negative(i.e.
                    # return flow to increase storage of outflow cell), then
                    # the unsatisfied demand of outflow cell itself is the
                    # prev_accu_supplycell_demad.

                    accum_uns_potnetabs_after_distribution = \
                        prev_accu_supplycell_demad

                    if unagregrgated_potential_netabs_sw[r_x, r_y] <= 0:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                    else:
                        # Note:  if there demand of the outflowcell itself
                        # is negative, it should be substracted from the daily
                        # aggregated demand (potential_netabs_sw) before
                        # distribution
                        print("i dey hererere oooo")
                        denom = potential_netabs_sw - unagregrgated_potential_netabs_sw[x, y]
                        print(denom)
                        if denom > 0:
                            unsatisfied_potnetabs_riparian[r_x, r_y] = \
                                (unagregrgated_potential_netabs_sw[r_x, r_y] / denom) * \
                                (accumulated_unsatisfied_potential_netabs_sw -
                                 prev_accu_supplycell_demad)
                        else:
                            unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                else:
                    # Note: The 'accum_uns_potnetabs_after_distribution' value
                    # for a global lake or reservoir outflowcell itself will
                    # now consist of its distributed contibution  long with
                    # prev_accu_supplycell_demad
                    print("i gsgsgsgs  oooo")
                    print(potential_netabs_sw)
                    if potential_netabs_sw> 0:
                        accum_uns_potnetabs_after_distribution = \
                            (unagregrgated_potential_netabs_sw[x, y] / potential_netabs_sw) * \
                            (accumulated_unsatisfied_potential_netabs_sw -
                             prev_accu_supplycell_demad) + prev_accu_supplycell_demad
                    else:
                        accum_uns_potnetabs_after_distribution = prev_accu_supplycell_demad

                    if unagregrgated_potential_netabs_sw[r_x, r_y] <= 0:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                    else:
                        print("i obul  oooo")
                        if potential_netabs_sw> 0:
                            unsatisfied_potnetabs_riparian[r_x, r_y] = \
                                (unagregrgated_potential_netabs_sw[r_x, r_y] /
                                 potential_netabs_sw) * \
                                (accumulated_unsatisfied_potential_netabs_sw -
                                 prev_accu_supplycell_demad)
                        else:
                            unsatisfied_potnetabs_riparian[r_x, r_y] = 0

            else:
                unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                unsatisfied_potnetabs_riparian[x, y] = 0
                accum_uns_potnetabs_after_distribution = \
                    accumulated_unsatisfied_potential_netabs_sw

    return accum_uns_potnetabs_after_distribution, \
        unsatisfied_potnetabs_riparian
