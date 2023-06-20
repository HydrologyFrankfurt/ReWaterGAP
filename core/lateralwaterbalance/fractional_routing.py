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
from numba import njit


@njit(cache=True)
def frac_routing(rout_order, routflow_looper,
                 surface_runoff, groundwater_discharge, loclake_frac,
                 locwet_frac, glowet_frac, glolake_frac,
                 reglake_frac, headwater_cell, drainage_direction,
                 swb_drainage_area_factor):
    """
    Route water through storage compartment using fractional routing scheme.

    Parameters
    ----------
    rout_order : array
        Routing order of cells
    routflow_looper : int
        looper that goes through the routing order.
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
    # Index to  print out varibales of interest
    # e.g  if x==65 and y==137: print(prev_gw_storage)
    x, y = rout_order[routflow_looper]
    # =========================================================================
    #  Computing fractional routing factor(fswb_catchment)
    # =========================================================================
    # fswb_catchment is calulated as 20 * (wetland and local lake fraction),
    # see section 4 of  (Müller Schmied et al. (2021)
    fswb_catchment = (loclake_frac + locwet_frac + glowet_frac) * \
        swb_drainage_area_factor

    fswb_catchment = np.where(fswb_catchment > 1, 1, fswb_catchment)

    # =========================================================================
    #   Routing surface runoff and groundwater discharge into surface water
    #   bodies.
    # =========================================================================
    # Surface runoff is routed into surface water bodies for both humid and
    # arid regions
    local_runoff_swb = fswb_catchment * surface_runoff
    local_runoff_river = (1-fswb_catchment) * surface_runoff

    # Groundwater discharge is routed into surface water bodies considering
    # only humid areas.
    local_gwrunoff_swb = fswb_catchment * groundwater_discharge
    local_gwrunoff_river = (1-fswb_catchment) * groundwater_discharge

    # =========================================================================
    #   Inland sinks
    # =========================================================================
    # Surface runoff and groundwater discharge fills an inland sink.
    # There are no outflows from the inland sinks.
    local_runoff_river = \
        np.where(drainage_direction < 0, 0, local_runoff_river)

    local_runoff_swb = np.where(drainage_direction < 0, surface_runoff,
                                local_runoff_swb)
    local_gwrunoff_swb = \
        np.where(drainage_direction < 0, groundwater_discharge,
                 local_gwrunoff_swb)
    local_gwrunoff_river = \
        np.where(drainage_direction < 0, 0, local_gwrunoff_river)

    # =========================================================================
    # Combining routed surface runoff and groundwater discharge into local
    # runoff.  Routed discharge from groundwater and remaining routed surface
    # runoff to river is combined into local river inflow
    # =========================================================================
    local_runoff = local_runoff_swb + local_gwrunoff_swb
    local_river_inflow = local_runoff_river + local_gwrunoff_river

    # Note: In semi-arid/arid areas, all groundwater reaches the river directly

    return local_runoff, local_river_inflow
