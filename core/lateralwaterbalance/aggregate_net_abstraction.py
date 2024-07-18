# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Aggregate riparian potential net abstractiion to outflowcell."""

# =============================================================================
# This module aggregates riparian potential net abstractiion to outflowcell.
# =============================================================================

from numba import njit
import numpy as np


@njit(cache=True)
def aggregate_potnetabs(glwdunits, lake_area, res_area, netabs,
                        unique_glwdunits):
    """
    Aggregate riparian potential net abstractiion to outflowcell.

    Parameters
    ----------
    glwdunits : array
       Global Lakes and Wetlands. Units: [outflow cell and riparian cell]
    lake_area : TYPE
        Maximum area of global lake. Unit: [km2]
    res_area : TYPE
        Maximum area of reservoir and regulated lake. Unit: [km2]
    netabs : TYPE
        Daily potential net abstraction from surface water
    unique_glwdunits : array
        Unique values of global Lakes and Wetlands. Units [outflow cell and
        riparian cell]

    Returns
    -------
    aggregate : array
        Outflow cells of global lakes, regulated lakes and reseviors have
        aggregated potential net abstraction. Respective riparian cells have
        values of 0. The rest of the cells have respective daily potential net
        abstraction values.
    """
    aggregate = netabs  # Create a copy of net abstraction for aggregation

    for i in range(len(unique_glwdunits)):

        # Get outflow  cell of riprian cells of lakes or reservoir
        outflowcell_index = \
            np.where((glwdunits == unique_glwdunits[i]) & (lake_area > 0) |
                     (glwdunits == unique_glwdunits[i]) & (res_area > 0))

        # Get index of lakes and reservior with values in index array.
        # If there are multiple outflow cells (reservoirs or lakes), select the
        # cell with the highest index (or last reservoir or lake).
        # This avoids double counting of demand.
        if outflowcell_index[0].shape[0] != 0:
            x, y = outflowcell_index[0][-1], outflowcell_index[1][-1]

            # Get positive net abstraction values of lake or reservoir riparian
            # cells.
            pot_net_abs =\
                np.where((glwdunits == unique_glwdunits[i]) & (netabs > 0),
                         netabs, 0)

            # Set positive abstraction values of riparain cell of lake or
            # reservior to zero.
            aggregate =\
                np.where((glwdunits == unique_glwdunits[i]) & (netabs > 0),
                         np.zeros_like(aggregate), aggregate)

            # Add all riparian cells net abstraction to that of the out flow cell.
            aggregate[x, y] += pot_net_abs.sum()

    return aggregate
