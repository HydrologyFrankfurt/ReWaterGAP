# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"River Property"

# =============================================================================
# This module computes river bottom width (km), maximum river storage (km3),
# river length corrected with continental area fraction (km) for all grid cells
# based on section 4.7.3 of (Müller Schmied et al. (2021)).
# =============================================================================

import numpy as np


class RiverProperties:
    def __init__(self, river_slope, roughness, river_length, bankfull_flow,
                 continental_fraction):
        # Units of input variables
        # River slope (-)
        # Roughness (-)
        # River length (m)
        # Bank full river flow (m3/s)
        # continental area fraction (-)

        self.river_slope = river_slope
        self.roughness = roughness

        # Reduce river length in coastal cells in proportion to continental
        # area  fraction
        self.river_length = river_length * (continental_fraction/100)

        # =====================================================================
        #     Computing river bottom width and maximum river storage
        # =====================================================================
        # River top width  and depth at bankfull flow (bf) condition is
        # approximated by Eq.8 and Eq.9 (section 2.4.2) of Verzano et al., 2012
        m_to_km = 0.001
        # Bank full river flow,  Units: m3/s
        bankfull_flow[bankfull_flow < 0.05] = 0.05

        # River top width at bank full conidtion,  Units: km
        river_top_width_bf = (2.71 * np.power(bankfull_flow, 0.557)) * m_to_km

        # River depth at bank full conidtion,  Units: km
        river_depth_bf = (0.349 * np.power(bankfull_flow, 0.341)) * m_to_km

        # River bottom width is calulated assuming a trapezoidal channel with
        # slope of 0.5 at both sides.  Units: km
        self.river_bottom_width = river_top_width_bf - 4 * river_depth_bf

        # Maximum river storage is calulated from (Eq.33) of
        # (Müller Schmied et al. (2021), Units: km3

        self.max_river_storage = 0.5 * self.river_length * (river_depth_bf) * \
            (self.river_bottom_width + river_top_width_bf)
