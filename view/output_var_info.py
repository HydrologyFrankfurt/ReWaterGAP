# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Variable Information."""

# This model returns dictionary with variable definitions.

modelvars = {
    # VerticalWaterBalanceFluxes
    "potevap": {"long": "Potential evapotranspiration", "unit": "mm/day"},
    "netrad": {"long": "Net radiation", "unit": "mm/day"},
    "lai-total": {"long": "Leaf area index", "unit": "mm/day"},
    "canopy_evap":  {"long": "Canopy evaporation", "unit": "mm/day"},
    "throughfall": {"long": "Throughfall", "unit": "mm/day"},
    "snow_fall":  {"long": "Snowfall", "unit": "mm/day"},
    "snow_melt": {"long": "Snowmelt", "unit": "mm/day"},
    "snow_evap": {"long": "Snow evaporation", "unit": "mm/day"},
    "qr": {"long": "Groundwater recharge", "unit": "mm/day"},
    "qs": {"long": "Surface runoff", "unit": "mm/day"},

    # LateralWaterBalanceFluxes
    "qg": {"long": "Groundwater discharge", "unit": "km3/day"},
    "locallake_outflow": {"long": "Locallake outflow", "unit": "km3/day"},
    "localwetland_outflow": {"long": "Localwetland outflow", "unit": "km3/day"},
    "globallake_outflow": {"long": "Globallake outflow", "unit": "km3/day"},
    "globalwetland_outflow": {"long": "Globalwetland outflow", "unit": "km3/day"},
    "dis": {"long": "Streamflow or River discharge", "unit": "km3/day"},
    "actual_net_abstraction_gw": {"long": "actual net abstraction from "
                                  "groundwater", "unit": "km3/day"},

    # VerticalWaterBalanceStorages
    "canopystor": {"long": "Canopy storage", "unit": "mm"},
    "swe": {"long": "Snow water equivalent", "unit": "mm"},
    "soilmoist": {"long": "Soil moisture", "unit": "mm"},

    # LateralWaterBalanceStorages
    "groundwstor": {"long": "Groundwater storage", "unit": "km3"},
    "locallakestor": {"long": "Locallake storage", "unit": "km3"},
    "localwetlandstor": {"long": "Localwetland storage", "unit": "km3"},
    "globallakestor": {"long": "Globallake storage", "unit": "km3"},
    "globalwetlandstor": {"long": "Globalwetland storage", "unit": "km3"},
    "riverstor": {"long": "River storage",  "unit": "km3"}
}
