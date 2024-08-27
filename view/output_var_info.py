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
    "potevap": {"long": " Total potential evapotranspiration", "unit": " kg m-2 s-1"},
    "netrad": {"long": "Net radiation", "unit": " kg m-2 s-1"},
    "lai-total": {"long": "Leaf area index", "unit": "-"},
    "canopy-evap":  {"long": "Canopy evaporation", "unit": " kg m-2 s-1"},
    "throughfall": {"long": "Throughfall", "unit": " kg m-2 s-1"},
    "snowfall":  {"long": "Snowfall", "unit": " kg m-2 s-1"},
    "snm": {"long": "Snowmelt", "unit": " kg m-2 s-1"},
    "snow-evap": {"long": "Snow evaporation", "unit": " kg m-2 s-1"},
    "snowcover-frac": {"long": "Snow cover fraction ", "unit": "-"},
    "qrd": {"long": "Diffuse groundwater recharge", "unit": " kg m-2 s-1"},
    "qs": {"long": "Surface runoff", "unit": " kg m-2 s-1"},

    # LateralWaterBalanceFluxes
    "consistent-precipitation": {"long": "modified or consistent precipitation",
                                 "unit": " kg m-2 s-1"},
    "qg": {"long": "Groundwater discharge", "unit": " kg m-2 s-1"},
    "qtot": {"long": "Total runoff (sum of surrface runoff and groundwater discharge)",
             "unit": " kg m-2 s-1"},
    "qrf": {"long": "Focussed groundwater recharge below surface water bodies",
            "unit": " kg m-2 s-1"},
    "qr": {"long": "sum of diffuse groundwater recharge + groundwater recharge"
           " from surfacewater bodies", "unit": " kg m-2 s-1"},
    "locallake-outflow": {"long": "Locallake outflow", "unit": " kg m-2 s-1"},
    "localwetland-outflow": {"long": "Localwetland outflow", "unit": " kg m-2 s-1"},
    "globallake-outflow": {"long": "Globallake outflow", "unit": " kg m-2 s-1"},
    "globalwetland-outflow": {"long": "Globalwetland outflow", "unit": " kg m-2 s-1"},
    "dis": {"long": "Streamflow or River discharge", "unit": "m3 s-1"},
    "dis-from-upstream": {"long": "Streamflow or River discharge from upstream cell",
                          "unit": "m3 s-1"},

    "atotusegw": {"long": "actual net abstraction from  groundwater", "unit": " kg m-2 s-1"},
    "atotusesw": {"long": "actual net abstraction from suurface water", "unit": " kg m-2 s-1"},
    "atotuse": {"long": "Total Actual Water Consumption (all sectors)", "unit": " kg m-2 s-1"},

    "evap-total": {"long": "Potential consumptive use(NAg+NAs) and total actual"
                   " evaporation from land", "unit": " kg m-2 s-1"},


    "unsat_potnetabs_sw_from_demandcell": {"long": "unsatisfied potential"
                                           "demand from demandcell in surfacewater",
                                           "unit": " kg m-2 s-1"},

    "returned_demand_from_supplycell": {"long": "returned demand from supply cell calculated in current timestep",
                                         "unit": " kg m-2 s-1"},

    "returned_demand_from_supplycell_nextday": {"long": "returned demand from"
                                                " supply cell calculated in next timestep",
                                                "unit": " kg m-2 s-1"},
    "demand_left_excl_returned_nextday": {"long": "demand left without riparian "
                                          "demand and return demand calculated"
                                          " in the next time step",
                                          "unit": " kg m-2 s-1"},
    "potnetabs_sw": {"long": "Daily potential net abstraction from surface water",
                     "unit": " kg m-2 s-1"},

    "get_neighbouring_cells_map": {"long": "neighbouring cells map", "unit": "-"},



    "ncrun":  {"long": "Net cell runoff (river discharge - upstream river disharge)",
               "unit": " kg m-2 s-1"},

    "river-velocity": {"long": "River velocity",  "unit": "m s-1"},
    "land-area-fraction": {"long": "Daily land area fraction",  "unit": "-"},
    "pot_cell_runoff":  {"long": "Potential runoff (sum of surrface runoff and" 
                         " groundwater discharge and runoff from surface waterbodies)",
                         "unit": " kg m-2 s-1"},

    # VerticalWaterBalanceStorages
    "canopystor": {"long": "Canopy storage", "unit": "kg m-2"},
    "swe": {"long": "Snow water equivalent", "unit": "kg m-2"},
    "soilmoist": {"long": "Soil moisture", "unit": "kg m-2"},
    "smax": {"long": "Maximum soil moisture", "unit": "kg m-2"},

    # LateralWaterBalanceStorages
    "groundwstor": {"long": "Groundwater storage", "unit": "kg m-2"},
    "locallakestor": {"long": "Locallake storage", "unit": "kg m-2"},
    "localwetlandstor": {"long": "Localwetland storage", "unit": "kg m-2"},
    "globallakestor": {"long": "Globallake storage", "unit": "kg m-2"},
    "globalwetlandstor": {"long": "Globalwetland storage", "unit": "kg m-2"},
    "riverstor": {"long": "River storage",  "unit": "kg m-2"},
    "reservoirstor": {"long": "Global reservoir storage",  "unit": "kg m-2"},
    "tws": {"long": "Total water storage",  "unit": "kg m-2"}
}
