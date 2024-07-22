# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Add project path to file for module or package import."""

import os
import sys


def setup_path():
    """
    Append path of rewatergap to system path for module or package import.

    Returns
    -------
    None.

    """
    # Determine the absolute path to the parent directory
    parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))

    # Append the parent path to the system path
    if parent_path not in sys.path:
        sys.path.append(parent_path)


# call function
setup_path()
