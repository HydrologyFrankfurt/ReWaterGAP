.. configuration_file_gwswuse:

###########################
Configuration File GWSWUSE
###########################

FilePath
########

**inputDir: 

Contains two paths:
	- `input_data`: Path to the folder containing input data. This folder must have a specific structure for the data to be correctly matched and processed.
   	- `gwswuse_convention`: Path to the convention file that defines the conventions for data verification and processing.
  	- `outputDir`: Path to the folder where output data will be stored.

RuntimeOptions
##############

SimulationOption
****************

- `time_extend_mode`: Controls how time-dependent input data is handled to ensure they cover the entire simulation period.
- `irrigation_efficiency_gw_mode`: Determines how irrigation efficiency with groundwater is calculated.
- `irrigation_input_based_on_aei`: Specifies how input data for irrigation-specific consumptive water use is interpreted.
- `correct_irr_simulation_by_t_aai`: Indicates whether the simulation should adjust for temporal changes in irrigated areas.
- `deficit_irrigation_mode`: Determines whether the simulation considers deficit irrigation in certain grid cells.

ParameterSetting
****************

- `efficiency_gw_threshold`: Threshold for irrigation efficiency with groundwater.
- `deficit_irrigation_factor`: Reduction factor for irrigation in grid cells identified as deficient.

CellSpecificOutput
******************

- `flag`: If true, sector-specific intermediate results for the grid cell closest to the coordinates in `CellSpecificOutput["coords"]` will be displayed in the CLI during the simulation.
- `coords`: A sub-dict for setting coordinates for the grid cell and timestep for displaying cell-specific results in the CLI:
- `Lat`: Latitude of the grid cell
- `Lon`: Longitude of the grid cell
- `Year`: Year
- `Month`: Month (for irrigation and total)

OutputSelection
***************
Determines which simulation results are saved and in what format they are output.

- `WGHM_input_run`: Controls whether the results are retained in memory for further use in a ReWGHM run.
- `Sectors`: Selection of sectors for which simulation results should be saved (e.g., irrigation, households, etc.).
- `GWSWUSE variables`: Defines which specific variables (e.g., `consumptive_use`, `abstraction`, `return_flow`, `net_abstraction`) for each water source (groundwater or surface water) should be saved.
- `Global_Annual_Totals`: Controls whether ReGWSWUSE generates a comprehensive overview of simulation results in an Excel file with global annual values.
