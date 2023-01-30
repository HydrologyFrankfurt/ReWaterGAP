# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Arguments for command line interface (CLI)."""

# =============================================================================
# This module is used by Configuration handler and Input handler.
# =============================================================================


import argparse


def parse_cli():
    """
    Parse command line arguments.

    Returns
    -------
    Command line argument
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('name', type=str, metavar='',
                        help='name of configuration file',)
    parser.add_argument('--debug', action="store_true",
                        help='Enable or disable TraceBack for '
                        'debugging by setting True or False ')
    args = parser.parse_args()
    return args
