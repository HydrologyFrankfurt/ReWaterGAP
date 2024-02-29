# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
""" Logo and runtime measurement."""

import time
from termcolor import colored
from misc import watergap_version


# =============================================================================
# WaterGAP Ascii Image
# =============================================================================
logo = f"""
███████████████████████████████████████████████████████████████████████████████

 /██      /██           /██                       /██████  /██████ /███████
| ██  /█ | ██          | ██                      /██__  ██/██__  █| ██__  ██
| ██ /███| ██ /██████ /██████   /██████  /██████| ██  \__| ██  \ █| ██  \ ██
| ██/██ ██ ██|____  █|_  ██_/  /██__  ██/██__  █| ██ /███| ███████| ███████/
| ████_  ████ /███████ | ██   | ███████| ██  \__| ██|_  █| ██__  █| ██____/
| ███/ \  ███/██__  ██ | ██ /█| ██_____| ██     | ██  \ █| ██  | █| ██
| ██/   \  █|  ███████ |  ████|  ██████| ██     |  ██████| ██  | █| ██
|__/     \__/\_______/  \___/  \_______|__/      \______/|__/  |__|__/

        WaterGAP ({watergap_version.__version__}) funded by DFG

        Institution: {watergap_version.__institution__}
        GitHub:  https://github.com/HydrologyFrankfurt/ReWaterGAP
        Twitter: https://twitter.com/HydroFrankfurt

███████████████████████████████████████████████████████████████████████████████
"""

print(logo)


# =============================================================================
# Timer decorator
# =============================================================================
def check_time(func):
    """
    Check simulation time.

    Parameters
    ----------
    func : function
        input function to timer

    Returns
    -------
    inner : str
        return process time

    """
    def inner(*args, **kwargs):
        """
        Compute run time.

        Parameters
        ----------
        *args : arguments
           wrapper arguments
        **kwargs : key word arguments
           wrapper key word arguments

        Returns
        -------
        None.

        """
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        output_msg = \
            'WaterGAP run completed at %.2f minute(s)' % ((end-start)/60)
        print('\n' + colored(output_msg, 'green'))
    return inner
