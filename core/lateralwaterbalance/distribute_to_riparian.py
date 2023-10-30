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
# This function redistributes the accumulated unsatisfied potential net
# abstraction of surface water (SW) from the outflow cell of a global lake
# or reservoir to its riparian cells,
# =============================================================================

from numba import njit


@njit(cache=True)
def redistritute_to_riparian(prev_accumulated_unsatisfied_potential_netabs_sw,
                             accumulated_unsatisfied_potential_netabs_sw,
                             unagregrgated_potential_netabs_sw,
                             potential_netabs_sw, glwdunits, rout_order,
                             unsatisfied_potnetabs_riparian,
                             x, y):

    # Note! x,y is index of outflow cell of a global lake or reservoir
    for i in range(len(rout_order)):
        # Get invidividual riparian cells of global lakes or reservoir.
        r_x, r_y = rout_order[i]
        if glwdunits[x, y] == glwdunits[r_x, r_y] and (x, y) != (r_x, r_y):

            # If daily aggregated demand of global lake or reservoir
            # (in outflowcell) of the current time step have not been fully
            # satisfied, distribute the unstaisfied demand to riparian
            # cells.The unsatisfied demand is calculated as the
            # difference between accumulated_unsatisfied_potential_netabs_sw
            # and prev_accumulated_unsatisfied_potential_netabs_sw

            # Note: The previous unsatisfied demand of the outflow cell itself
            # is not redistributed but is attempted to be satisfied in a river
            # or local lake storage in the current time step.

            # The redistributed unsatisfied demand to riparian cells are
            # attempted to be satisfied in river or lake storage in the next
            # time step.

            if accumulated_unsatisfied_potential_netabs_sw - \
                    prev_accumulated_unsatisfied_potential_netabs_sw > 0:

                # If the potential net abstraction of global lake or reservoir
                # outflow cell itself is negative or positive,
                # distribution to riparian cell is done separately.

                if unagregrgated_potential_netabs_sw[x, y] <= 0:
                    # if current demand of outflow cell itself is negative(i.e
                    # return flow to increase storage of outflow cell), then
                    # the unsatisfied demand of outflow cell itself is the
                    # prev_accumulated_unsatisfied_potential_netabs_sw.

                    # The unstaisfied portion of aggregated demand of current
                    # timestep is distributed to riparian cell based on
                    # percentage contribution of each riparian cell to
                    # aggregated demand in outflow cell.

                    # Note:  the negative demand of the outflow cell itself #
                    # should be substracted from the daily aggregated demand
                    # (potential_netabs_sw) before redistribution

                    accum_uns_potnetabs_after_distribution = \
                        prev_accumulated_unsatisfied_potential_netabs_sw

                    if unagregrgated_potential_netabs_sw[r_x, r_y] <= 0:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                    else:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = \
                            (unagregrgated_potential_netabs_sw[r_x, r_y] /
                             (potential_netabs_sw - unagregrgated_potential_netabs_sw[x, y])) * \
                            (accumulated_unsatisfied_potential_netabs_sw -
                             prev_accumulated_unsatisfied_potential_netabs_sw)

                else:
                    # In case of postive demand of the outflow cell itself, the
                    # the unsatisfied demand of outflow cell itself is the
                    # prev_accumulated_unsatisfied_potential_netabs_sw
                    # (previous unsatisfied demand) and its related distributed
                    # portion based on its percentage contribution

                    # Note: Here the positive demand of the outflow cell itself
                    # is not subtracted from daily aggregated use before
                    # redistribution.

                    accum_uns_potnetabs_after_distribution = \
                        (unagregrgated_potential_netabs_sw[x, y] / potential_netabs_sw) * \
                        (accumulated_unsatisfied_potential_netabs_sw -
                         prev_accumulated_unsatisfied_potential_netabs_sw) + \
                        prev_accumulated_unsatisfied_potential_netabs_sw

                    if unagregrgated_potential_netabs_sw[r_x, r_y] <= 0:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                    else:
                        unsatisfied_potnetabs_riparian[r_x, r_y] = \
                            (unagregrgated_potential_netabs_sw[r_x, r_y] /
                             potential_netabs_sw) * \
                            (accumulated_unsatisfied_potential_netabs_sw -
                             prev_accumulated_unsatisfied_potential_netabs_sw)

            else:
                unsatisfied_potnetabs_riparian[r_x, r_y] = 0
                unsatisfied_potnetabs_riparian[x, y] = 0
                accum_uns_potnetabs_after_distribution = \
                    accumulated_unsatisfied_potential_netabs_sw

    return accum_uns_potnetabs_after_distribution, \
        unsatisfied_potnetabs_riparian
