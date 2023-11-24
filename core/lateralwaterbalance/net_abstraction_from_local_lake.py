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
    storage : float
       Local Lake storage, Unit: [km^3/day]
    lake_frac : TYPE
        Local lake area fraction, Unit: [-].
    reduction_exponent_lakewet : float
        Lake reduction exponent taken from Eqn 24 from (Müller Schmied et al.
        (2021)) , Units: [-].
    accumulated_unsatisfied_potential_netabs_sw : float
        Accumulated unsatified potential net abstraction after satisfaction
        from river, Unit: [km^3/day]

    Returns
    -------
    updated_storage : float
        Updated local Lake storage, Unit: [km^3/day]
    updated_accum_unsat_potnetabs_sw : float
        Accumulated unsatified potential net abstraction after local lake
        satisfaction, Unit: [km^3/day]
    lake_newfraction : float
        Updated local lake area fraction(to adapt landarea fraction), Unit:[-].
    actual_use_sw:float
        Accumulated actual net abstraction from surface water, Unit: [km^3/day]
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

    lake_newfraction = update_redfactor * lake_frac

    # Daily actual net use
    actual_use_sw = accumulated_unsatisfied_potential_netabs_sw - \
        updated_accum_unsat_potnetabs_sw

    return updated_storage, updated_accum_unsat_potnetabs_sw, \
        lake_newfraction, actual_use_sw
