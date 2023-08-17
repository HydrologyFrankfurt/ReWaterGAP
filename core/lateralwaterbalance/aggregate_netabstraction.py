# -*- coding: utf-8 -*-
"""
Created on Sun Aug 13 19:32:32 2023

@author: nyenah
"""

from numba import njit
import numpy as np


@njit(cache=True)
def aggregate_potnetabs(glwdunits, lake_area, res_area, netabs, unique_glwdunits):

    aggregate = netabs  # create a copy of net abstraction for aggregation

    for i in range(len(unique_glwdunits)):

        # get outflow  cell of riprian cells of lakes or reservoir
        outflowcell_index = \
            np.where((glwdunits == unique_glwdunits[i]) & (lake_area > 0) |
                     (glwdunits == unique_glwdunits[i]) & (res_area > 0))

        # get index of lakes and reservior with values in index array
        if outflowcell_index[0].shape[0] != 0:
            x, y = outflowcell_index[0][0], outflowcell_index[1][0]

            # get positive net abstraction values of lake or reservior riparian
            # cells
            pot_net_abs =\
                np.where((glwdunits == unique_glwdunits[i]) & (netabs > 0),
                         netabs, 0)

            # set positive abstraction value of riparain cell of lake to zero
            aggregate =\
                np.where((glwdunits == unique_glwdunits[i]) & (netabs > 0),
                         np.zeros_like(aggregate), aggregate)

            # add all ripriarian cells  net abstraction to out flow cell
            aggregate[x, y] = pot_net_abs.sum()

    return aggregate
