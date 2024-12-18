# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Check negative precipitation values and convert forcing units."""

import numpy as np
from termcolor import colored

# =========================================================================
#     Check negative precipitation values
# =========================================================================
# This does not stop code execution but warns if there are negative values


def check_neg_precipitation(precipitation):
    """
    Warns user on negative precipitation values.

    Parameters
    ----------
    precipitation : array
        precipitation, Unit: [mm/day]

    Returns
    -------
    warning message.

    """
    if np.any(precipitation.values < 0):
        msg = colored("There are negative values in the precipitation data.",
                      'red')
        raise ValueError(msg)


def to_mm_per_day(precipitation):
    """
    Convert precipitation to mm per day.

    Parameters
    ----------
    precipitation : array
        precipitation, Unit: [kg m-2 s-1]

    Returns
    -------
    precipitation with converted units.

    """
    if precipitation.units == 'kg m-2 s-1':
        mm_per_day = 86400
        coverted = precipitation.values.astype(np.float64) * mm_per_day
    else:
        coverted = precipitation.values.astype(np.float64)
    return coverted


def to_kelvin(temperature):
    """
    Convert temperature from degree celcius to Kelvin.

    Parameters
    ----------
    temperature : array
        Temperature, Unit: [°C]

    Returns
    -------
    Temperature with converted units to Kelvin.

    """
    if temperature.units in ("K", "k"):
        converted = temperature.values.astype(np.float64)
    else:
        converted = temperature.values.astype(np.float64) + 273.15
    return converted
