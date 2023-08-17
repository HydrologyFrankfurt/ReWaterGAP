# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 10:11:18 2023

@author: nyenah
"""
import numpy as np
from numba import njit

@njit(cache=True)
def redistritute_to_riparian(prev_accumulated_unsatisfied_potential_netabs_sw,
                             accumulated_unsatisfied_potential_netabs_sw,
                             unagregrgated_potential_netabs_sw,
                             potential_netabs_sw, glwdunits,
                             x, y):


    # all use from outflow cell was satisfied 
    unsatisfied_potnetabs_riparian = np.zeros(accumulated_unsatisfied_potential_netabs_sw.shape)
    if accumulated_unsatisfied_potential_netabs_sw[x, y] > 0:
        if unagregrgated_potential_netabs_sw[x, y] < 0:
            unsatisfied_potnetabs_outflow_cell = \
                          prev_accumulated_unsatisfied_potential_netabs_sw[x, y]

            unsatisfied_potnetabs_riparian = \
                np.where((glwdunits == glwdunits[x, y]) &
                         (potential_netabs_sw == 0),
                         (unagregrgated_potential_netabs_sw
                          / (potential_netabs_sw[x, y] - unagregrgated_potential_netabs_sw[x, y]))*
                         (accumulated_unsatisfied_potential_netabs_sw[x, y] -
                          prev_accumulated_unsatisfied_potential_netabs_sw[x, y]),
                         0)
        else:
            unsatisfied_potnetabs_outflow_cell = \
                (unagregrgated_potential_netabs_sw[x, y] / potential_netabs_sw[x, y]) * \
                (accumulated_unsatisfied_potential_netabs_sw[x, y] -
                 prev_accumulated_unsatisfied_potential_netabs_sw[x, y]) + \
                prev_accumulated_unsatisfied_potential_netabs_sw[x, y]

            unsatisfied_potnetabs_riparian = \
                np.where((glwdunits == glwdunits[x, y]) &
                         (potential_netabs_sw == 0),
                         (unagregrgated_potential_netabs_sw
                          / (potential_netabs_sw[x, y]))*
                         (accumulated_unsatisfied_potential_netabs_sw[x,y] -
                          prev_accumulated_unsatisfied_potential_netabs_sw[x,y]),
                         0)
    else:
        unsatisfied_potnetabs_outflow_cell = 0


    return unsatisfied_potnetabs_outflow_cell, unsatisfied_potnetabs_riparian