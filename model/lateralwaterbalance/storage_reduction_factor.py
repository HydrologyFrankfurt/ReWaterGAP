# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Reduction factor for surface water bodies."""

import numpy as np
from numba import njit


# =============================================================================
# Calculating area reduction factor for dynamic area calulation based on
# Equation 24 and 25 of (Müller Schmied et al. (2021)).
# =============================================================================


@njit(cache=True)
def swb_redfactor(storage, max_storage, reduction_exponent_swb,
                  choose_swb=None):
    """
    Compute reduction factor  surface water bodies(swb).

    Thus lake, wetland,reserviour and regulated lake.

    Parameters
    ----------
    storage :float
        Daily surface waterbody storage, Unit: [km3]
    max_storage : float
        Maximum storage of surface waterbody storage, Unit: [km3]
    choose_swb : string
        select surface water body type ( global and local lakes and wetlands)
    reduction_exponent_swb: float
       Reduction exponent taken from Eqn 24 and 25 of  Müller Schmied et al.
       (2021) for respective waterbodies.,  Units: [-].

    Returns
    -------
    reductionfactor : array
        reduction factor for dynamic area (local lake and wetland)
        or evaporation (global lake, wetland,reserviour and regulated lake)

    """
    # =========================================================================
    # Computing reduction factor for surface water bodies.
    # See Equation 24 & 25 in (Müller Schmied et al. (2021).
    # n_factor is the multiplying factor in the denominator of maximum storage.
    # n_factor=2 is for global and local lakes and n_factor=1 is for global
    #  reservoirs/regulated lakes and local and global wetlands
    # =========================================================================
    if choose_swb == "local lake" or choose_swb == "global lake":
        n_factor = 2.0
    else:
        n_factor = 1.0

    reductionfactor_div =\
        np.abs(storage - max_storage)/(n_factor * max_storage)

    reductionfactor = 1.0 - (reductionfactor_div)**reduction_exponent_swb

    # # limits of the Lake reduction factor
    if reductionfactor < 0:
        reductionfactor = 0
    elif reductionfactor > 1.0:
        reductionfactor = 1.0

    return reductionfactor
