# -*- coding: utf-8 -*-
"""
Created on Sat Aug 19 14:20:24 2023.

@author: nyenah
"""

from numba import njit
from core.lateralwaterbalance import reduction_factor as rf


@njit(cache=True)
def abstract_from_local_lake(storage, max_storage, lake_frac,
                             reduction_exponent_lakewet,
                             accumulated_unsatisfied_potential_netabs_sw):
    """
    Abstraction from local lake.

    Parameters
    ----------
    storage : TYPE
        DESCRIPTION.
    area_of_cell : TYPE
        DESCRIPTION.
    lake_frac : TYPE
        DESCRIPTION.
    active_depth : TYPE
        DESCRIPTION.
    reduction_exponent_lakewet : TYPE
        DESCRIPTION.
    accumulated_unsatisfied_potential_netabs_sw : TYPE
        DESCRIPTION.

    Returns
    -------
    updated_storage : TYPE
        DESCRIPTION.
    updated_accum_unsat_potnetabs_sw : TYPE
        DESCRIPTION.
    lake_wet_newfraction : TYPE
        DESCRIPTION.

    """
    choose_swb = 'local lake'
    # Abtsract from local lake if there is accumulated unstaisfied use
    # after river abstraction.

    # To compare accumulated_unsatisfied_potential_netabs_sw (always ≥ 0)
    # and local lake storage (-max_storage ≤ storage ≤ max_storage),
    # we add max_storage to the local lake storage to make it positive.
    if accumulated_unsatisfied_potential_netabs_sw < (storage + max_storage):
        updated_storage = storage - \
            accumulated_unsatisfied_potential_netabs_sw

        updated_accum_unsat_potnetabs_sw = 0
    else:
        updated_storage = -1 * max_storage
        updated_accum_unsat_potnetabs_sw = accumulated_unsatisfied_potential_netabs_sw -\
            (storage + max_storage)

    # updating  local lake area fractions for next day after abstraction.
    update_redfactor = \
        rf.swb_redfactor(updated_storage, max_storage,
                         reduction_exponent_lakewet, choose_swb)

    lake_wet_newfraction = update_redfactor * lake_frac
    return updated_storage, updated_accum_unsat_potnetabs_sw, \
        lake_wet_newfraction
