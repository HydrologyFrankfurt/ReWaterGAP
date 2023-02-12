# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Daily Leaf Area Index (LAI) Function."""

# =============================================================================
# This module computes leaf area index based on section 4.2.3 of
# (Müller Schmied et al. (2021)).
# Leaf area index is computed for all grid cells in parallel using
# numpy vectorize function.vectorised functions peforms elementwise
# computations on all arrays at onces.
# See https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html
# =============================================================================

import numpy as np


def daily_leaf_area_index(temperature, growth_status, days, initial_days,
                          cum_precipitation, precipitation,
                          leaf_area_index, min_leaf_area_index,
                          max_leaf_area_index, land_cover, humid_arid):
    """
    Compute daily leaf area index per grid cells.

    Vectorization is applied to compute leaf area index in
    parallel for all grid cell.

    Parameters
    ----------
    temperature : array
        Daily temperature climate forcing.
        
        Unit: [K]
    growth_status : array
        Growth status shows, per grid cell, whether a specific land cover has not started to grow or is growing (value=0) or is fully grown (value=1).
        Initially all landcovers are not growing. This variable gets updated per time step.
    days : array
        Days since start of leaf area index profile (counter for days with
        growing conditions).
        This variable gets updated per time step.
        
        Unit: [day]
    initial_days : array
       Landcover specific initial days
    cum_precipitation : array
        Cummulative precipitation per time step.
       
        Unit: [mm/d]
    precipitation : array
        Daily precipitation climate forcing.
        Units are converted from [kg m-2 s-1] to [mm/d].
        
        Unit: [mm/d]
    leaf_area_index : array
        Temporal_leaf_area_index
    min_leaf_area_index : array
        Minimum Leaf area index  over all grid cell.
        
        Unit: [-]
    max_leaf_area_index : array
        Maximum Leaf area index  over all grid cell.
        
        Unit: [-]
    land_cover : array
        Land_cover class  based on [1]_.
        
    humid_arid : array
        Humid-arid calssification based on [1]_.

    Returns
    -------
    leaf_area_index : array
        Daily leaf area index
    days : array
        Day since start for current day.
        
        Unit: [day]
        
    cum_precipitation : array
       Cummulative precipitation for current day.
       
       Unit: [mm/d]
       
    growth_status : array
        Growth status per grid cell for current day


    Notes
    ----------
    A day is defined as part of the growing season when the daily temperature stays above 8°C for a land-cover-specific number of days (Table C1), and cumulative precipitation from the day where the growing season starts reaches at least 40 mm [1]_.

    At the beginning of the growing season, LAI increases linearly for 30 days until it reaches maximum LAI. For (semi)arid cells at least 0.5 mm of daily precipitation is required to keep the growing season ongoing. LAI then stays constant for the stated land-cover-specific number of days and when growing season conditions are not fulfilled anymore, a senescence phase is initiated and LAI linearly decreases to a minimum within the next 30 days.

    References
    ----------
    .. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                The global water resources and use model WaterGAP v2.2d: model
                description and evaluation. Geoscientific Model Development,
                14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
    """
    if land_cover != np.nan:
        # ======================
        # Growing Phase
        # ======================
        # Plant can only start growing if daily temperature is above
        # 8◦C(281.15 K) for a land-cover-specific number of initial days (See
        # Table C1 in (Müller Schmied et al. (2021)). Note that 'days' variable
        # is a counter for days with growing conditions
        # Initially growth staus is zero (landcover is not growing yet).
        if temperature > 281.15:
            if growth_status == 0:
                if days >= initial_days:

                    # Growing season starts and days is defined as part of
                    # the growing season. precipiation also accumulates
                    days = days + 1
                    cum_precipitation += precipitation

                    if cum_precipitation > 40:
                        # Landcover grows linearly  till it gets to maximum LAI
                        # (at initial + 30 days) then growth status changes.

                        if days >= initial_days + 30:
                            growth_status = 1
                            leaf_area_index = max_leaf_area_index

                        else:
                            leaf_area_index = (min_leaf_area_index +
                                               ((max_leaf_area_index -
                                                 min_leaf_area_index)/30) *
                                               (days - initial_days))

                    else:
                        # Landcover could not grow but temperature condition is
                        # reached therefore LAI is minimum. The days variable
                        # is set to landcover specific initial days till
                        # cumulative precipitation is reached (thus growing
                        # season is reached)

                        days = initial_days
                        leaf_area_index = min_leaf_area_index

                else:
                    # Landcover specific initial days is not reached but
                    # temperature specification is reached therefore LAI is
                    # minimum.

                    days = days + 1
                    cum_precipitation += precipitation
                    leaf_area_index = min_leaf_area_index

            else:
                # Leaf Area index has reached maximum (growth status is 1 ) and
                # will deacrease. When in the decreasing phase, temperature
                # specification may be reached and hence this part of the code
                # still continues the decreasing phase till 30 days is reached.

                if days <= 30:
                    days = days-1
                    # if land_cover_type is '1' or '2' we have evergreen plants
                    # and LAI will never completely degrade and hence growth
                    # status is switched at once.
                    if land_cover <= 2:
                        growth_status = 0
                    if days <= 0:
                        days = 0
                        growth_status = 0
                        cum_precipitation = 0

                    leaf_area_index = (max_leaf_area_index -
                                       ((max_leaf_area_index -
                                         min_leaf_area_index)/30) *
                                       (30 - days))

                else:
                    # Leaf area index has reached maximum (growth status is 1 )
                    # but temperature specification is met. LAI then stays
                    # constant (at maximum) for the stated land-cover-specific
                    # number of days.
                    # Also, if land is arid  and precipitation is below 0.5mm
                    # the days variable decreases

                    if humid_arid == 1 and precipitation < 0.5:
                        days = days-1
                    else:
                        # Note!! when growth status is 1, "days" only decreases
                        # when temperature is < 281.15 (see no growing phase
                        # lines from 247-257) except for arid regions with
                        # precipitation below 0.5mm which decreases whether
                        # temperature condition is met or not.

                        days = initial_days + 30

                    leaf_area_index = max_leaf_area_index

        # ======================
        # NO Growing Phase
        # ======================
        else:
            if growth_status == 0:
                if days > initial_days:
                    days = days + 1
                    cum_precipitation += precipitation

                    if cum_precipitation > 40:
                        # Here temperature is less than  281.15K but landcover
                        # is already growing.This part of the code
                        # still continues the growing  phase till landcover
                        # specific initial days + 30 is reached.

                        if days >= initial_days + 30:
                            growth_status = 1
                            leaf_area_index = max_leaf_area_index

                        else:
                            leaf_area_index = (min_leaf_area_index +
                                               ((max_leaf_area_index -
                                                 min_leaf_area_index)/30) *
                                               (days - initial_days))

                    else:
                        days = initial_days
                        leaf_area_index = min_leaf_area_index
                else:
                    cum_precipitation += precipitation
                    leaf_area_index = min_leaf_area_index
            else:
                # Leaf Area index has reached maximum (growth status = 1) and
                # will deacrease when growing season conditions are not
                # fulfilled anymore.
                # Here days variable decreases from 30 to 0 days

                if days <= 30:
                    days = days-1
                    if days <= 0:
                        days = 0
                        growth_status = 0
                        cum_precipitation = 0

                    leaf_area_index = (max_leaf_area_index -
                                       ((max_leaf_area_index -
                                         min_leaf_area_index)/30) *
                                       (30 - days))

                else:
                    # Leaf Area index has reached maximum (growth status is 1 )
                    # but temperature specification is not met. LAI then stays
                    # constant (at maximum) for the stated land-cover-specific
                    # number of days. Here the days variable decreases
                    # (note the difference from the growing pahse)

                    days = days-1
                    leaf_area_index = max_leaf_area_index

    return leaf_area_index, days, cum_precipitation, growth_status

# =========================================================================
# Note!!! np.vectorize (and hence parallel_leaf_area_index)
# computes leaf area index logic  over all grid cells


vectorized_leaf_area_index = \
    np.vectorize(daily_leaf_area_index,
                 otypes=[np.float32, int, np.float32, int])
# =========================================================================
