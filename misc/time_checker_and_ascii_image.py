# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 14:05:03 2022.

@author: nyenah
"""
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
