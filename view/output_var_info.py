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
    "canopy_evap":  {"long": "Canopy evaporation", "unit": " kg m-2 s-1"},
    "throughfall": {"long": "Throughfall", "unit": " kg m-2 s-1"},
    "snow_fall":  {"long": "Snowfall", "unit": " kg m-2 s-1"},
    "snow_melt": {"long": "Snowmelt", "unit": " kg m-2 s-1"},
    "snow_evap": {"long": "Snow evaporation", "unit": " kg m-2 s-1"},
    "snowcover_frac": {"long": "Snow cover fraction ", "unit": "-"},
    "qrd": {"long": "Diffuse groundwater recharge", "unit": " kg m-2 s-1"},
    "qs": {"long": "Surface runoff", "unit": " kg m-2 s-1"},

    # LateralWaterBalanceFluxes
    "consistent_precipitation": {"long": "modified or consistent precipitation", "unit": " kg m-2 s-1"},
    "qg": {"long": "Groundwater discharge", "unit": " kg m-2 s-1"},
    "qtot": {"long": "Total runoff (sum of surrface runoff and groundwater discharge)", "unit": " kg m-2 s-1"},
    "qrf": {"long": "Focussed groundwater recharge below surface water bodies", "unit": " kg m-2 s-1"},
    "qr": {"long": "sum of diffuse groundwater recharge + groundwater recharge from surfacewater bodies", "unit": " kg m-2 s-1"},
    "locallake_outflow": {"long": "Locallake outflow", "unit": " kg m-2 s-1"},
    "localwetland_outflow": {"long": "Localwetland outflow", "unit": " kg m-2 s-1"},
    "globallake_outflow": {"long": "Globallake outflow", "unit": " kg m-2 s-1"},
    "globalwetland_outflow": {"long": "Globalwetland outflow", "unit": " kg m-2 s-1"},
    "dis": {"long": "Streamflow or River discharge", "unit": "m3 s-1"},
    "dis_from_upstream":{"long": "Streamflow or River discharge from upstream cell", "unit": "m3 s-1"},
    "dis_from_inland_sink" : {"long": "Stream flow from inland sink",  "unit": " m3 s-1"},
    
    "atotuse_gw": {"long": "actual net abstraction from  groundwater", "unit": " kg m-2 s-1"},
    "atotuse_sw": {"long": "actual net abstraction from suurface water", "unit": " kg m-2 s-1"},
    "atotuse":{"long": "Total Actual Water Consumption (all sectors)", "unit": " kg m-2 s-1"},
    
    "evap-total":{"long": "Potential consumptive use(NAg+NAs) and total actual evaporation from land", 
                                 "unit": " kg m-2 s-1"},

    "total_demand_into_cell": {"long": "total dailay demand into cell", "unit": " kg m-2 s-1"},

    "unsat_potnetabs_sw_from_demandcell": {"long": "unsatisfied potential"
                                           "demand from demandcell in surfacewater", 
                                           "unit": " kg m-2 s-1"}, 
    
    "returned_demand_from_supply_cell": {"long": "returned demand from supply cell", "unit": " kg m-2 s-1"},
    "prev_returned_demand_from_supply_cell": {"long": "returned demand from supply cell previous time step", "unit": " kg m-2 s-1"},
    
    "total_unsatisfied_demand_ripariancell": {"long": " total unsatisfied potential"
                                           "demand to ripariancell in surfacewater", "unit": " kg m-2 s-1"},
    
    "accumulated_unsatisfied_potential_netabs_sw":
        {"long": "accumulated unsatisfied potential net abstraction from surfacewater",  "unit": " kg m-2 s-1"},
    "get_neighbouring_cells_map": {"long": "neighbouring cells map", "unit": "-"},
    
    "total_unsatisfied_demand_from_supply_to_all_demand_cell":
        {"long": "total unsatisfied demand from supply to all demand_cell",  "unit": " kg m-2 s-1"},
    
    "ncrun":  {"long": "Net cell runoff (river discharge - upstream river disharge)",  "unit": " kg m-2 s-1"}, 
     "river_velocity": {"long": "River velocity",  "unit": "m s-1"}, 
    "land_area_fraction": {"long": "Daily land area fraction",  "unit": "-"},
    
    
    
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
