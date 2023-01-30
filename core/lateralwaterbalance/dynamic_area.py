# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

import numpy as np
from core.verticalwaterbalance import parameters as pm

# =============================================================================
# Calculating area reduction factor for dynamic area calulation based on
# Equation 24 and 25 of (Müller Schmied et al. (2021)).
# =============================================================================


def loclake_and_wetlands_dynamic_area(storage, max_storage, cell_area,
                                      lakewet_frac, choose_swb):
    """
    Computes dynamic global or local lake or wetland area.

    Parameters
    ----------
    storage : TYPE
        DESCRIPTION.
    max_storage : TYPE
        DESCRIPTION.
    cell_area : TYPE
        DESCRIPTION.
    lakewet_frac : TYPE
        DESCRIPTION.

    Returns
    -------
    lakewet_area : TYPE
        DESCRIPTION.
    area_reductionfactor : TYPE
        DESCRIPTION.

    """
    # =========================================================================
    # Computing reduction factor for surface water bodies.
    # n_factor is the multiplying factor in the denominator of maximum storage.
    # n_factor=2 is for global and local lakes and n_factor=1 is for global
    #  reservoirs/regulated lakes and local and global wetlands
    # =========================================================================
    if choose_swb == 'local lake':
        n_factor = 2
    else:
        n_factor = 1

    reductionfactor_div = \
        np.divide(np.abs(storage - max_storage), (n_factor * max_storage),
                  out=np.zeros_like(max_storage), where=max_storage != 0)

    area_reductionfactor = \
        1-(reductionfactor_div)**pm.reduction_exponent_lakewet

    # limits of the Lake reduction factor
    area_reductionfactor[area_reductionfactor < 0] = 0
    area_reductionfactor[area_reductionfactor > 1] = 1

    # Maximum area
    max_area = cell_area * lakewet_frac

    # Dynamic lake or wetland area based on area reduction factor
    lakewet_area = area_reductionfactor * max_area
    return lakewet_area, area_reductionfactor
