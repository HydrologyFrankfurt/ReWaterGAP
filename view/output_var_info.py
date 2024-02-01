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
    "demand_satisfied_by_cell": {"long": "demand satisfied by cell", 
                                 "unit": "km3/day"},
    "total_demand": {"long": "total demand", "unit": "km3/day"},

    "unsat_potnetabs_sw_from_demandcell": {"long": "unsatisfied potential"
                                           "demand from demandcell in surfacewater", 
                                           "unit": "km3/day"},
    "unsat_potnetabs_sw_to_supplycell": {"long": "unsatisfied potential"
                                           "demand to supplycell in surfacewater", 
                                           "unit": "km3/day"},
    
    "returned_demand_from_supply_cell": {"long": "returned demand from supply cell", "unit": "km3/day"},
    "prev_returned_demand_from_supply_cell": {"long": "returned demand from supply cell previous time step", "unit": "km3/day"},
    
    "unsatisfied_potential_netabs_riparian": {"long": "unsatisfied potential"
                                           "demand to ripariancell in surfacewater", "unit": "km3/day"},
    
    "accumulated_unsatisfied_potential_netabs_sw":
        {"long": "accumulated unsatisfied potential net abstraction from surfacewater",  "unit": "km3/day"},
    "get_neighbouring_cells_map": {"long": "neighbouring cells map", "unit": "-"},
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
    "riverstor": {"long": "River storage",  "unit": "km3"},
    "glores_stor": {"long": "Global reservoir storage",  "unit": "km3"}
}
