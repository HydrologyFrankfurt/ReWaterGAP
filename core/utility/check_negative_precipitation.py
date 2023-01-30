# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 08:12:56 2022.

@author: nyenah
"""
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
        precipitation

    Returns
    -------
    warning message.

    """
    if np.any(precipitation < 0):
        msg = colored("There are negative values in the precipitation data.",
                      'red')
        raise ValueError(msg)
