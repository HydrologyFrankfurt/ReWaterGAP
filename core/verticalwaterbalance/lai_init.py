# -*- coding: utf-8 -*-

# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Leaf Area Index Class."""

# =============================================================================
# This module computes leaf area index for each grid cell in parallell
# by calling a vectorised leaf  area index function from the
# parallel_leaf_area_index_module. vectorised functions peforms elementwise
# computations on all arrays at onces.
# See https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html
# Leaf area index in computed based on section 4.2.3 of
# (Müller Schmied et al. (2021)).
# =============================================================================

import numpy as np


class LeafAreaIndex:
    """Distribute Leaf area parameters (per landcover) over gridcells."""

    def __init__(self, land_cover, parameters_lai):

        # =====================================================================
        # Distribute maximum and minimum Leaf area index over all grid cells
        # together with inital days per landcover to start or end with
        # growing season
        # =====================================================================
        def minimum_leaf_area_index(max_leaf_area_index, frac_decid_plant,
                                    red_factor_evergreen):
            """
            Compute minimum one-sided Leaf Area Index.

            Parameters
            ----------
            max_leaf_area_index : array
                Maximum one-sided leaf area index per landcover type.
                Units: [-]
            frac_decid_plant : aaray
                Fraction of deciduous plants per landcover type. Units: [-]
            red_factor_evergreen : TYPE
                Reduction factor for evergreen plants per landcover type.
                Units: [-]

            Returns
            -------
            min_leaf_area_index : array
                Minimum one-sided leaf area index per landcover type.
                Units: (-)

            """
            # See Eq. 5 in Müller Schmied et al 2021. for minimum one-sided
            # leaf area equation
            min_leaf_area_index = 0.1 * frac_decid_plant + (1 - frac_decid_plant) * \
                red_factor_evergreen * max_leaf_area_index
            return min_leaf_area_index

        for i in range(len(parameters_lai)):
            parameters_lai.loc[i, 'min_leaf_area_index'] = \
                minimum_leaf_area_index(
                    parameters_lai.loc[i, 'max_leaf_area_index'],
                    parameters_lai.loc[i, 'frac_decid_plant'],
                    parameters_lai.loc[i, 'red_factor_evergreen'])

        # Distribute initial days per landcover (to start or end with growing
        # season) over all grid cell, Units: day
        self.initial_days = np.zeros((land_cover.shape))
        self.initial_days.fill(np.nan)
        for i in range(len(parameters_lai)):
            self.initial_days[land_cover[:, :] == parameters_lai.loc[i, 'Number']] = \
                parameters_lai.loc[i, 'initial_days']

        # Maximum Leaf area index per landcover over all grid cell,  Units: (-)
        self.max_leaf_area_index = np.zeros((land_cover.shape))
        self.max_leaf_area_index.fill(np.nan)
        for i in range(len(parameters_lai)):
            self.max_leaf_area_index[land_cover[:, :] == parameters_lai.loc[i, 'Number']] = \
                parameters_lai.loc[i, 'max_leaf_area_index']

        # Minimum Leaf area index per landcover over all grid cell, Units: (-)
        self.min_leaf_area_index = np.zeros((land_cover.shape))
        self.min_leaf_area_index.fill(np.nan)
        for i in range(len(parameters_lai)):
            self.min_leaf_area_index[land_cover[:, :] == parameters_lai.loc[i, 'Number']] = \
                parameters_lai.loc[i, 'min_leaf_area_index']
