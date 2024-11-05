.. _simulation_logic_gwswuse:

################
Simulation Logic
################

*********************
Irrigation Simulation
*********************

Input Data
##########

The irrigation-specific ReGWSWUSE simulation is based on input data for the following variables:

- irr.consumptive_use_tot_aei or irr.consumptive_use_tot_aai (total consumptive use for irrigation)
- irr.fraction_gw_use (fraction of groundwater used)
- irr.fraction_return_gw → fraction of returns to groundwater
- irr.efficiency_sw → efficiency for surface water use

For scenarios of deficit irrigation, additional variables are considered:

- irr.gwd_mask → groundwater depletion mask
- irr.abstraction_part_mask → abstraction part mask
- irr.fraction_aei_aai → ratio of equipped vs. actually irrigated area
- irr.time_factor_aai → time factor for irrigated area adjustments

Configuration Options
#####################

Runtime configuration options enable modification of the irrigation simulation in ReGWSWUSE through:

Simulation Options that alter the simulation logic.
Parameter Settings that allow specific parameter values to be set in the simulation.
Configurable parameters in the configuration file include efficiency_gw_threshold and deficit_irrigation_factor. Simulation options include:

irrigation_efficiency_gw_mode: Controls how groundwater irrigation efficiency (irr.efficiency_gw) is set, which is always temporally constant. Options:

"enforce": Sets the efficiency for each cell based on the efficiency_gw_threshold parameter.
"adjust": Efficiency varies by cell and considers both the groundwater efficiency threshold and surface water efficiency (irr.efficiency_sw), ensuring groundwater efficiency is at least equal to that of surface water.
irr_consumptive_use_input_based_on: Specifies whether irrigation-specific potential consumptive use (irr.consumptive_use_tot) is based on areas equipped for irrigation (AEI) or those actually irrigated (AAI). Options:

"aei": When irr.consumptive_use_tot refers to equipped areas, it is multiplied by irr.fraction_aai_aei, representing the actual irrigated proportion.
"aai": When irr.consumptive_use_tot already refers to actually irrigated areas, the fraction is not applied.
correct_irr_simulation_by_t_aai: This option adjusts potential monthly consumptive water use based on updated AAI values from 2015-2020, allowing area adjustments post-2015 using irr.time_factor_aai. Options:

"true": Multiplies potential consumptive use by time_factor_aai for updated AAI.
"false": Does not apply this adjustment.
deficit_irrigation_mode: If enabled, assumes deficit irrigation in cells with notable groundwater depletion rates (from 1980-2009) and significant irrigation abstraction rates (1960-2000), reducing irrigation by 30% below the optimal need. Options:

"true": Applies deficit irrigation factor adjustments.
"false": Assumes optimal irrigation levels.


Simulation logic
################

Preprocessing of irr.consumptive_use_tot
****************************************

The simulation starts with preprocessing of the input potential consumptive water use, `irr.cu_tot_input`. This preprocessing is based on configuration options, which are denoted by “cm.” in the following text. 

1. **Configuration Setting: cm.irr_input_based_on**  
   This setting is applied first:

..math:


2. **Correction with Time Factor (t_aai)**  
   Based on the configuration option `cm.correct_irr_by_t_aai`, the potential consumptive water use, :math:`irr.cu_tot`, for the years 2016 to 2020 is adjusted using the time factor :math:t_aai` (time_factor_aai).

..math:
	

3. **Deficit Irrigation Mode (`cm.deficit_irrigation_mode`)**  
   Next, the configuration setting for :math:`cm.deficit_irrigation_mode` is applied:

Calculation of Groundwater and Surface Water Use
************************************************

Using a time-invariant, irrigation-specific raster that represents the relative shares of groundwater use in the irrigation sector, :math:`irr.fraction_gw_use`, the potential consumptive use of groundwater and surface water is calculated.

..math:
	

..math:
	



Calculation of Potential Water Withdrawals
******************************************

To calculate irrigation water withdrawals, irrigation efficiency values are required. In the GWSWUSE model, it is assumed that irrigation efficiencies differ for groundwater and surface water withdrawal infrastructures. The surface water efficiencies are input as a raster with national values. Groundwater efficiencies depend on the configuration option :math:`cm.irrigation_efficiency_gw_mode` and are set using the parameter:

After setting the irrigation efficiency for groundwater, the irrigation water withdrawals from both groundwater and surface water are calculated.


Calculation of Total Irrigation Withdrawals
*******************************************
Once the irrigation-specific water withdrawals from groundwater and surface water are calculated, the total irrigation-specific water withdrawals can also be computed.



Calculation of Return Flows
***************************
After calculating the water withdrawals, return flows in irrigation are determined. Return flows occur because not all water withdrawn for irrigation is used in plant growth and some returns to groundwater and surface water. The total return flows in the irrigation sector are calculated in the GWSWUSE model as the difference between total water withdrawal and total consumptive water use.

The irrigation-specific return flows into groundwater bodies and surface water bodies are calculated using a time-invariant raster that represents the relative shares of the total irrigation-specific return flows that flow into groundwater.


Calculation of Net Abstractions
*******************************
Finally, irrigation-specific net abstractions from groundwater and surface water per raster cell (id) are calculated. The net abstractions for each water body are defined as the difference between water withdrawals and return flows for each water body.

*******************
Domestic Simulation
*******************

Input Data
##########

The ReGWSWUSE simulation specific to the demoestic sector relies on input data for the following variables:

- :math:`CU_{tot,dom}`: liv.consumptive_use_tot
- :math:`WU_{tot,dom}`: liv.abstraction_tot
- :math:`f_{gw,dom}`: liv.fraction_gw_use
- :math:`f_{return,gw,dom}`: liv.fraction_return_gw (0 if no input file provided)

Configuration Options
#####################

Currently, there are no specific configuration options in ReGWSWUSE that affect the simulation logic specific to the domestic sector.

Simulation Logic
################

Consumptive Water Use and Abstraction from Groundwater and Surface Water
************************************************************************

For consumptive groundwater use (:math:`CU_{gw,dom}`) and surface water use (:math:`CU_{sw,dom}`) in the domestic sector:

..math:
	CU_{gw,dom}(y,id) = CU_{tot,dom}(y,id) * f_{gw,dom}(id)

..math:
	CU_{sw,dom}(y,id) = CU_{tot,dom}(y,id) * (1 - f_{gw,dom}(id))

For water abstractions from groundwater (:math:`WU_{gw,dom}`) and surface water (:math:`WU_{sw,dom}`) in the domestic sector:

..math:
	WU_{gw,dom}(y,id) = WU_{tot,dom}(y,id) * f_{gw,dom}(id)

..math:
	WU_{sw,dom}(y,id) = WU_{tot,dom}(y,id) * (1 - f_{gw,dom}(id))


Calculation of Return Flows
***************************

Manufacturing-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from manufacturing water use (:math:`RF_{tot,dom}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,dom}`) and surface water (:math:`RF_{sw,dom}`), according to the relative share of return flows to groundwater within total manufacturing sector returns (:math:`f_{return,gw,dom }`):


..math:
	RF_{tot,dom}(y,id) = WU_{tot,dom}(y,id) - CU_{tot,dom}(y,id)

..math:
	RF_{gw,dom}(y,id) = RF_{tot,dom}(y,id) * f_{return,gw,dom}(,id)

..math:
	RF_{sw,dom}(y,id) = RF_{tot,dom}(y,id) * (1 - f_{return,gw,dom}(id))


Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,dom}`) and surface water (:math:`NA_{sw,dom}`) in the domestic sector are calculated similarly:

..math:
	NA_{gw,dom}(y,id) = WU_{gw,dom}(y,id) - RF_{gw,dom}(y,id)

..math:
	NA_{sw,dom}(y,id) = WU_{sw,dom}(y,id) - RF_{sw,dom}(y,id)

************************
Manufacturing Simulation
************************

The ReGWSWUSE simulation for the manufacturing sector is analogous to the domestic-specific ReGWSWUSE simulation.

Input Data
##########

The ReGWSWUSE simulation specific to the manufacturing sector relies on input data for the following variables:

- :math:`CU_{tot,man}`: liv.consumptive_use_tot
- :math:`WU_{tot,man}`: liv.abstraction_tot
- :math:`f_{gw,man}`: liv.fraction_gw_use
- :math:`f_{return,gw,man}`: liv.fraction_return_gw (0 if no input file provided)

Configuration Options
#####################

Currently, there are no specific configuration options in ReGWSWUSE that affect the simulation logic specific to the manufacturing sector.

Simulation Logic
################

Consumptive Water Use and Abstraction from Groundwater and Surface Water
************************************************************************

For consumptive groundwater use (:math:`CU_{gw,man}`) and surface water use (:math:`CU_{sw,man}`) in the manufacturing sector:

..math:
	CU_{gw,man}(y,id) = CU_{tot,man}(y,id) * f_{gw,man}(id)

..math:
	CU_{sw,man}(y,id) = CU_{tot,man}(y,id) * (1 - f_{gw,man}(id))

For water abstractions from groundwater (:math:`WU_{gw,man}`) and surface water (:math:`WU_{sw,man}`) in the manufacturing sector:

..math:
	WU_{gw,man}(y,id) = WU_{tot,man}(y,id) * f_{gw,man}(id)

..math:
	WU_{sw,man}(y,id) = WU_{tot,man}(y,id) * (1 - f_{gw,man}(id))


Calculation of Return Flows
***************************

Manufacturing-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from manufacturing water use (:math:`RF_{tot,man}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,man}`) and surface water (:math:`RF_{sw,man}`), according to the relative share of return flows to groundwater within total manufacturing sector returns (:math:`f_{return,gw,man }`):


..math:
	RF_{tot,man}(y,id) = WU_{tot,man}(y,id) - CU_{tot,man}(y,id)

..math:
	RF_{gw,man}(y,id) = RF_{tot,man}(y,id) * f_{return,gw,man}(,id)

..math:
	RF_{sw,man}(y,id) = RF_{tot,man}(y,id) * (1 - f_{return,gw,man}(id))


Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,man}`) and surface water (:math:`NA_{sw,man}`) in the manufacturing sector are calculated similarly:

..math:
	NA_{gw,man}(y,id) = WU_{gw,man}(y,id) - RF_{gw,man}(y,id)

..math:
	NA_{sw,man}(y,id) = WU_{sw,man}(y,id) - RF_{sw,man}(y,id)

************************
Thermal Power Simulation
************************

The ReGWSWUSE simulation for the thermal power sector is analogous to the domestic-specific ReGWSWUSE simulation.

Input Data
##########

The ReGWSWUSE simulation for the thermal power sector relies on input data for the following variables:

- :math:`CU_{tot,tp}`: liv.consumptive_use_tot
- :math:`WU_{tot,tp}`: liv.abstraction_tot
- :math:`f_{gw,tp}`: liv.fraction_gw_use
- :math:`f_{return,gw,tp}`: liv.fraction_return_gw (0 if no input file provided)

Configuration Options
#####################

Currently, there are no specific configuration options in ReGWSWUSE that affect the simulation logic specific to the thermal power sector.

Simulation Logic
################

Consumptive Water Use and Abstraction from Groundwater and Surface Water
************************************************************************

For consumptive groundwater use (:math:`CU_{gw,tp}`) and surface water use (:math:`CU_{sw,tp}`) in the thermal power sector:

..math:
	CU_{gw,tp}(y,id) = CU_{tot,tp}(y,id) * f_{gw,tp}(id)

..math:
	CU_{sw,tp}(y,id) = CU_{tot,tp}(y,id) * (1 - f_{gw,tp}(id))


For water abstractions from groundwater (:math:`WU_{gw,liv}`) and surface water (:math:`WU_{sw,liv}`) in the thermal power sector:

..math:
	WU_{gw,liv}(y,id) = WU_{tot,liv}(y,id) * f_{gw,liv}(id)

..math:
	WU_{sw,liv}(y,id) = WU_{tot,liv}(y,id) * (1 - f_{gw,liv}(id))

Calculation of Return Flows
***************************

Thermal Power-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from thermal power water use (:math:`RF_{tot,tp}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,tp}`) and surface water (:math:`RF_{sw,tp}`), according to the relative share of return flows to groundwater within total thermal power sector returns (:math:`f_{return,gw,tp}`):

..math:
	RF_{tot,tp}(y,id) = WU_{tot,tp}(y,id) - CU_{tot,tp}(y,id)

..math:
	RF_{gw,tp}(y,id) = RF_{tot,tp}(y,id) * f_{return,gw,tp}(,id)

..math:
	RF_{sw,tp}(y,id) = RF_{tot,tp}(y,id) * (1 - f_{return,gw,tp}(id))

Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,man}`) and surface water (:math:`NA_{sw,man}`) in the manufacturing sector are calculated similarly:

..math:
	NA_{gw,tp}(y,id) = WU_{gw,tp}(y,id) - RF_{gw,tp}(y,id)

..math:
	NA_{sw,tp}(y,id) = WU_{sw,tp}(y,id) - RF_{sw,tp}(y,id)


********************
Livestock Simulation
********************

The ReGWSWUSE simulation for the livestock sector is analogous to the domestic-specific ReGWSWUSE simulation.

Input Data
##########

The ReGWSWUSE simulation specific to the livestock sector relies on input data for the following variables:

- :math:`CU_{tot,liv}`: liv.consumptive_use_tot
- :math:`WU_{tot,liv}`: liv.abstraction_tot
- :math:`f_{gw,liv}`: liv.fraction_gw_use
- :math:`f_{return,gw,liv}`: liv.fraction_return_gw (0 if no input file provided)

Configuration Options
#####################

Currently, there are no specific configuration options in ReGWSWUSE that affect the simulation logic specific to the livestock sector.

Simulation Logic
################

Consumptive Water Use and Abstraction from Groundwater and Surface Water
************************************************************************

For consumptive groundwater use (:math:`CU_{gw,liv}`) and surface water use (:math:`CU_{sw,liv}`) in the livestock sector:

..math:
	CU_{gw,liv}(y,id) = CU_{tot,liv}(y,id) * f_{gw,liv}(id)

..math:
	CU_{sw,liv}(y,id) = CU_{tot,liv}(y,id) * (1 - f_{gw,liv}(id))

For water abstractions from groundwater (:math:`WU_{gw,liv}`) and surface water (:math:`WU_{sw,liv}`) in the manufacturing sector:

..math:
	WU_{gw,liv}(y,id) = WU_{tot,liv}(y,id) * f_{gw,liv}(id)

..math:
	WU_{sw,liv}(y,id) = WU_{tot,liv}(y,id) * (1 - f_{gw,liv}(id))


Calculation of Return Flows
***************************

Manufacturing-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from livestock water use (:math:`RF_{tot,liv}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,liv}`) and surface water (:math:`RF_{sw,liv}`), according to the relative share of return flows to groundwater within total livestock sector returns (:math:`f_{return,gw,liv}`):


..math:
	RF_{tot,liv}(y,id) = WU_{tot,liv}(y,id) - CU_{tot,liv}(y,id)

..math:
	RF_{gw,liv}(y,id) = RF_{tot,liv}(y,id) * f_{return,gw,liv}(,id)

..math:
	RF_{sw,liv}(y,id) = RF_{tot,liv}(y,id) * (1 - f_{return,gw,liv}(id))


Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,liv}`) and surface water (:math:`NA_{sw,liv}`) in the livestock sector are calculated similarly:

..math:
	NA_{gw,liv}(y,id) = WU_{gw,liv}(y,id) - RF_{gw,liv}(y,id)

..math:
	NA_{sw,liv}(y,id) = WU_{sw,liv}(y,id) - RF_{sw,liv}(y,id)



Cross-Sectoral Aggregate Results
################################

After calculating sector-specific results for consumptive uses, water withdrawals, returns, and net withdrawals from or towards groundwater and surface water, the sector-specific results for each variable are summed to derive cross-sectoral totals. To compute the aggregate cross-sectoral results, sector-specific results must be harmonized with regard to temporal resolution and unit consistency. This process involves initially summing results across the household, industrial production, thermal power, and livestock sectors, then dividing by 365 days and multiplying by the number of days in the month to standardize to units of :math:`{m}^{3}`:math:`{/}`:math:`{m}^{3}`{month}`. These values can then be combined with irrigation-specific results to finalize the aggregate cross-sectoral results.

Consumptive Wateruse
********************

..math:
	CU_{tot}(y,m,id) = CU_{tot,irr}(y,m,id) + \frac{CU_{tot,dom}(y,id) + CU_{tot, man}(y,id) + CU_{tot,tp}(y,id) + CU_{tot,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


..math:
	CU_{gw}(y,m,id) = CU_{gw,irr}(y,m,id) + \frac{CU_{gw,dom}(y,id) + CU_{gw, man}(y,id) + CU_{gw,tp}(y,id) + CU_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

..math:
	CU_{sw}(y,m,id) = CU_{sw,irr}(y,m,id) + \frac{CU_{sw,dom}(y,id) + CU_{sw, man}(y,id) + CU_{sw,tp}(y,id) + CU_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


Wateruse
********
..math:
	WU_{tot}(y,m,id) = WU_{tot,irr}(y,m,id) + \frac{WU_{tot,dom}(y,id) + WU_{tot,man}(y,id) + WU_{tot,tp}(y,id) + WU_{tot,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

..math:
	WU_{gw}(y,m,id) = WU_{gw,irr}(y,m,id) + \frac{WU_{gw,dom}(y,id) + WU_{gw,man}(y,id) + WU_{gw,tp}(y,id) + WU_{gw,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

..math:
	WU_{sw}(y,m,id) = WU_{sw,irr}(y,m,id) + \frac{WU_{sw,dom}(y,id) + WU_{sw,man}(y,id) + WU_{sw,tp}(y,id) + WU_{sw,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

..math:
	WU_{tot}(y,m,id) = WU_{tot,irr}(y,m,id) + WU_{tot,dom}(y,id) + WU_{tot,man}(y,id) + WU_{tot,tp}(y,id) + WU_{tot,liv}(y,id)

..math:
	WU_{gw}(y,m,id) = WU_{gw,irr}(y,m,id) + WU_{gw,dom}(y,id) + WU_{gw,man}(y,id) + WU_{gw,tp}(y,id) + WU_{gw,liv}(y,id)

..math:
	WU_{sw}(y,m,id) = WU_{sw,irr}(y,m,id) + WU_{sw,dom}(y,id) + WU_{sw,man}(y,id) + WU_{sw,tp}(y,id) + WU_{sw,liv}(y,id)

Returns
*******

..math:
	RF_{tot}(y,m,id) = RF_{tot,irr}(y,m,id) + \frac{RF_{tot,dom}(y,id) + RF_{tot,man}(y,id) + RF_{tot,tp}(y,id) + RF_{tot,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

..math:
	RF_{gw}(y,m,id) = RF_{gw,irr}(y,m,id) + \frac{RF_{gw,dom}(y,id) + RF_{gw,man}(y,id) + RF_{gw,tp}(y,id) + RF_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

..math:
	RF_{sw}(y,m,id) = RF_{sw,irr}(y,m,id) + \frac{RF_{sw,dom}(y,id) + RF_{sw,man}(y,id) + RF_{sw,tp}(y,id) + RF_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


Net Abstractions
****************

..math:
	NA_{gw}(y,m,id) = NA_{gw,irr}(y,m,id) + \frac{NA_{gw,dom}(y,id) + NA_{gw, man}(y,id) + NA_{gw,tp}(y,id) + NA_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

..math:
	NA_{sw}(y,m,id) = NA_{sw,irr}(y,m,id) + \frac{NA_{sw,dom}(y,id)+NA_{sw, man}(y,id) + NA_{sw,tp}(y,id) + NA_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}
