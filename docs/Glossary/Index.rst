.. _glossary:

========
Glossary
========

Standard Output Variables
-------------------------

.. csv-table::
   :header: "Name in configuration file (Config_ReWaterGAP.json)", "Long Name", "Variable name (in NetCDF) [1]_ ", "Description", "Unit"

   "streamflow", "Discharge", "dis", "river discharge or streamflow", "m3 s-1"
   "total_runoff", "Total Runoff", "qtot", "total runoff (sum of qs and qg)", "kg m-2 s-1"
   "cell_aet_consuse", "Evapotranspiration", "evap-total", "Actual evapotranspiration including actual total water consumption.", "kg m-2 s-1"
   "pot_evap", "Potential actual evapotranspiration.", "potevap", "Potential actual evapotranspiration (land and surface water).", "kg m-2 s-1"
   "groundwater_discharge", "Groundwater Runoff", "qg", "Outflow from groundwater compartment to surface waterbodies and rivers.", "kg m-2 s-1"
   "total_groundwater_recharge", "Total groundwater recharge", "qr", "sum of qrf and qrd ", "kg m-2 s-1"
   "groundwater_recharge_diffuse", "Diffuse groundwater recharge", "qrd", "diffuse groundwater recharge", "kg m-2 s-1"
   "groundwater_recharge_swb", "Focussed/localised groundwater recharge", "qrf", "focussed groundwater recharge below surface water bodies", "kg m-2 s-1"
   "surface_runoff", "Surface Runoff", "qs", "Fast surface and subsurface runoff. Fraction of total runoff from land that does not recharge the groundwater.", "kg m-2 s-1"
   "soil_moisture", "Total Soil Moisture Content", "soilmoist", "Daily mean water storage in soil compartment. equals rootmoist", "kg m-2"
   "snow_water_equiv", "Snow Water Equivalent", "swe", "Total water mass of the snowpack as daily mean.", "kg m-2"
   "total_water_storage", "Total Water Storage", "tws", "Daily mean total water storage (tws =  canopystor + riverstor + swe + soilmoist + groundwstor + lakestor + wetlandstor + reservoirstor).", "kg m-2"
   "canopy_storage", "Canopy Water Storage", "canopystor", "Daily mean water storage in canopy storage compartment.", "kg m-2"
   "groundwater_storage", "Groundwater Storage", "groundwstor", "Daily mean water storage in groundwater compartment.", "kg m-2"
   "local_wetland_storage", "Local Wetland Water Storage", "wetlandstor", "water storage in wetlands (local wetlands receive inflow generated within the grid cell)", "kg m-2"
   "global_wetland_storage", "Global Wetland Water Storage", "wetlandstor", "water storage in wetlands (global wetlands receive additional streamflow from upstream grid cells)", "kg m-2"
   "local_lake_storage", "Local Lake Water Storage", "lakestor", "water storage in lakes (local lakes receive inflow generated within the grid cell)", "kg m-2"
   "global_lake_storage", "Global Lake Water Storage", "lakestor", "water storage in lakes (global lakes receive receive additional streamflow from upstream grid cells)", "kg m-2"
   "river_storage", "River Water Storage", "riverstor", "Daily mean water storage in river compartment.", "kg m-2"
   "global_reservoir_storage", "Reservoir Water Storage", "reservoirstor", "Daily mean water storage in man-made reservoirs and regulated lake compartment.", "kg m-2"
   "actual_net_abstr_groundwater", "Total Actual Water Consumption (all sectors) from groundwater resources", "atotusegw", "Daily actual total consumptive water use (sectors irrigation, domestic, livestock, electricity, manufacturing) from groundwater resources.", "kg m-2 s-1"
   "actual_net_abstr_surfacewater", "Total Actual Water Consumption (all sectors) from surface water resources", "atotusesw", "Daily actual total consumptive water use (sectors irrigation, domestic, livestock, electricity, manufacturing) from surface water resources.", "kg m-2 s-1"
   "actual_water_consumption", "Total Actual Water Consumption (all sectors)", "atotuse", "Sum of atotusegw and atotusesw", "kg m-2 s-1"
   "leaf_area_index", "Leaf Area Index", "lai-total", "Simulated leaf area index of the vegetation", "-"
   "cell_area (static input)", "Grid Cell Area", "cellarea", "The total area associated with each grid cell in the model.", "km2"
   "contfrac(static input)", "Continental Fraction of Grid Cell", "contfrac", "The fraction of each grid cell that is assumed to be continent, i.e., not ocean.", "-"
   "consistent_precipitation", "Consistent Precipitation", "consistent_precipitation", "Precipitation used in WaterGap model", "kg m-2 s-1"
   "local_wetland_outflow", "Local Wetland Outflow", "localwetland_outflow", "Outflow from local wetlands", "kg m-2 s-1"
   "global_wetland_outflow", "Global Wetland Outflow", "globalwetland_outflow", "Outflow from global wetlands", "kg m-2 s-1"
   "local_lake_outflow", "Local Lake Outflow", "locallake_outflow", "Outflow from local lakes", "kg m-2 s-1"
   "global_lake_outflow", "Global Lake Outflow", "globallake_outflow", "Outflow from global lakes", "kg m-2 s-1"
   "streamflow_from_upstream", "Streamflow from Upstream", "dis_from_upstream", "Discharge from upstream cell", "kg m-2 s-1"
   "net_cell_runoff", "Net Cell Runoff", "ncrun", "Part of the cell precipitation that has neither been evapotranspirated nor stored", "kg m-2 s-1"
   "river_velocity", "River Velocity", "river_velocity", "River Velocity", "m s-1"
   "land_area_fraction", "Land Area Fraction", "land_area_fraction", "Land Area Fraction", "-"
   "net_rad", "Net Radiation", "netrad", "Net Radiation (Net upwards plus Net downwards radiation)", "kg m-2 s-1"
   "canopy_evap", "Canopy Evaporation", "canopy_evap", "Evaporation from canopy", "kg m-2 s-1"
   "throughfall", "Throughfall", "throughfall", "Fraction of  the precipitation that reaches the soil", "kg m-2 s-1"
   "snow_fall", "Snowfall", "snow_fall", "Throughfall while the temperature is below 0°C", "kg m-2 s-1"
   "snow_melt", "Snow Melt", "snow_melt", "Snow Melt", "kg m-2 s-1"
   "snow_evap", "Snow Evaporation", "snow_evap", "Evaporation from snow", "kg m-2 s-1"
   "snowcover_frac", "Snowcover Fraction", "snowcover_frac", "Fraction of snow cover", "-"
   "maximum_soil_moisture", "Maximum Soil Moisture", "smax", "Maximum Soil Moisture", "kg m-2"


Other Variables (Water Use)
-------------------------

.. csv-table:: 
   :header: "Name in configuration file (Config_ReWaterGAP.json)", "Long Name", "Variable name (in NetCDF) [1]_ ", "Description", "Unit"

   "total_demand_into_cell","","","","kg m-2 s-1"
   "unsat_potnetabs_sw_from_demandcell","","","",""
   "returned_demand_from_supply_cell","","","",""
   "prev_returned_demand_from_supply_cell","","","",""
   "total_unsatisfied_demand_ripariancell","","","",""
   "accumulated_unsatisfied_potential_netabs_sw","","","",""
   "get_neighbouring_cells_map","","","",""
   "total_unsatisfied_demand_from_supply_to_all_demand_cell","","","",""

ToDo: All kg m-2 s-1



.. [1] Output variables are named according to the ISIMIP simulation protocol. See section 4 Output data: https://protocol.isimip.org/ 
