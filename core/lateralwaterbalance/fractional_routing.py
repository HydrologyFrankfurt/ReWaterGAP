# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"Fractional routing"

# =============================================================================
# This module routes fractions of surface runoff and groundwater discharge
# to surface surface water bodies. This fractional routing scheme is based on
#  section of 4 and figuure 2. of (Müller Schmied et al. (2021)  differs
# between (semi)arid and humid grid cells
# =============================================================================
import numpy as np
from core.verticalwaterbalance import parameters as pm


def frac_routing(surface_runoff, groundwater_discharge, loclake_frac,
                 locwet_frac, glowet_frac, glolake_frac,
                 reglake_frac, headwater_cell, drainage_direction):
    """
    Route water through storage compartment using fractional routing scheme.

    Parameters
    ----------
    surface_runoff : array
        Daily volumetric surface runoff, unit: km3/day.
    groundwater_discharge : array
        Daily volumetric groundwater discharge, unit: km3/day.
    locLake_frac : array
        Local lake area fraction, unit: (-).
    locwet_frac : array
        Local wetland area fraction, unit: (-).
    glowet_frac : array
        Global wetland area fraction, unit: (-).

    Returns
    -------
    local_runoff : array
        Routed surface runoff and groundwater discharge into surface
        water bodies, unit: km3/day.

    """

    # =========================================================================
    #  Computing fractional routing factor(fswb_catchment)
    # =========================================================================
    # fswb_catchment is a static value
    fswb_catchment = (loclake_frac + locwet_frac + glowet_frac) * pm.\
        swb_drainage_area_factor
# =============================================================================
#               Will fix this later
#     # setting reservoir fraction to zero for now.
#     # reservoir_frac = 0
#     # fswb_catchment = \
#     #     np.where(headwater_cell == 1, fswb_catchment +
#     #              (glolake_frac + reglake_frac + reservoir_frac)*pm.\
#     #    swb_drainage_area_factor,
#     #              fswb_catchment)
# =============================================================================
    fswb_catchment[fswb_catchment > 1] = 1

    # Head water cells. why is fswb_catacment calulated for head water cell?***
    # fswb_catchment_headwater = (gloLake + reglake + reservior) * 20
    # limit reserviour to 60%  of runoff..
    # =========================================================================
    #     # For antropogenic run
    # =========================================================================
    # It is assumed that the fswb_catchment cannot be less than 0.6 in
    # headwater cells with a reservoir. This means that at least 60% of
    # surface runoff should go through the reservoir in headwater cells.

    # =========================================================================
    #   Routing surface runoff and groundwater discharge into surface water
    #   bodies.
    # =========================================================================
    # Surface runoff is routed into surface water bodies for both humid and
    # arid regions
    local_runoff_swb = fswb_catchment * surface_runoff
    local_runoff_river = (1-fswb_catchment) * surface_runoff

    # Groundwater discharge is routed into surface water bodies considering
    # only humid areas.****
    local_gwrunoff_swb = fswb_catchment * groundwater_discharge
    local_gwrunoff_river = (1-fswb_catchment) * groundwater_discharge

    # =========================================================================
    #     # inland sinks
    # =========================================================================
    # Surface runoff and groundwater discharge fills an inland sink.
    # Also there are no outflows the inland sinks.
    local_runoff_river[drainage_direction < 0] = 0
    local_runoff_swb = np.where(drainage_direction < 0, surface_runoff,
                                local_runoff_swb)
    local_gwrunoff_swb = \
        np.where(drainage_direction < 0, groundwater_discharge,
                 local_gwrunoff_swb)
    local_gwrunoff_river[drainage_direction < 0] = 0

    # =========================================================================
    #   Combining routed surface runoff and groundwater discharge into
    #   local runoff.
    # =========================================================================
    local_runoff = local_runoff_swb + local_gwrunoff_swb

    # Note: In semi-arid/arid areas, all groundwater reaches the river directly

    return local_runoff
