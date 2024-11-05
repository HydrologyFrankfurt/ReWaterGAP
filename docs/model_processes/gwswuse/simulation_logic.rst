.. _simulation_logic_gwswuse:

################
Simulation Logic
################

The simulation logic is the core of the ReGWSWUSE software. This chapter describes in detail the simulation logic of the ReGWSWUSE software, which is used for modeling water use across various sectors. It includes the calculation processes and the underlying formulas.

********
Overview
********

ReGWSWUSE, the WaterUseModels, and the WaterGAP Global Hydrological Model (WGHM) are integral sub-models of the comprehensive WaterGAP model. While the WaterUseModels model water use in various sectors—such as irrigation, households, industry, thermal power, and livestock—they do not differentiate between groundwater (GW) and surface water (SW). This differentiation, along with the subsequent calculation of net abstractions, is a central task of ReGWSWUSE, allowing for the quantification of human impact on global water resources.

ReGWSWUSE links the water use data from the WaterUseModels with the hydrological model (WGHM) by breaking down the data and calculating the shares of consumptive use, withdrawals, returns, and net abstractions for groundwater and surface water bodies in each sector. The main tasks include:

- **Consumptive Use:** ReGWSWUSE differentiates the sector-specific consumptive uses of freshwater calculated in the WaterUseModels by splitting it into groundwater and surface water. This division is based on the relative shares specified for each sector.
- **Withdrawals:** The software calculates water withdrawals from groundwater and surface water for all sectors. Specific irrigation efficiencies are used for irrigation, and then the total water withdrawal for irrigation is calculated. These calculations are essential for determining the actual amount of water withdrawn from the respective water sources.
- **Returns:** Another central feature of ReGWSWUSE is the calculation of returns of excess water to groundwater and surface water bodies. These returns occur when a portion of the withdrawn water is not consumed and flows back into the water compartments of groundwater and surface water.
- **Net Abstractions:** Finally, ReGWSWUSE calculates net abstractions, which represent the difference between water withdrawals and returns—essentially the actual amount of water lost to the water resource due to human water use. These net abstractions are a crucial variable for estimating human impact on water resources.

After calculating the sector-specific water use data, this data is integrated into ReGWSWUSE to determine consumptive use, withdrawals, returns, and net abstractions across all sectors. These aggregated values are essential for the global analysis of water use and are incorporated into the hydrological model (WGHM).

Through these processes, ReGWSWUSE connects the sectoral water use models (WaterUseModels) with the hydrological model (WGHM) of WaterGAP. The results from ReGWSWUSE feed directly into WGHM, where they are used to model water flows, storage processes, and the impact of human activities on water resources at a global level.

***************************
Sector-Specific Simulations
***************************

In the sector-specific simulations, consumptive use, water withdrawals, returns, and net abstractions are calculated individually for groundwater and surface water resources for each sector. There are differences in assumptions and calculation processes within WaterGAP that vary by sector.

While the sectors of households, industry, thermal power plants, and livestock differ only in their assumptions about certain variables and do not show sector-specific differences in the simulations, the irrigation sector is distinctly different. It not only has a different simulation logic but also a finer temporal resolution. In the WaterGAP model, it is assumed that potential water use remains constant throughout the year for the mentioned sectors (households, industry, thermal power, and livestock). In contrast, the irrigation sector takes into account that water use varies from month to month.

Additionally, water withdrawals for irrigation in ReGWSWUSE are calculated fully considering the different irrigation efficiencies for the withdrawal infrastructures of groundwater and surface water. Optional functions are also available, allowing for flexible adjustments of consumptive water use in the irrigation sector. 


.. figure:: ../images/gwswuse/gwswuse_logic.png
   :align: center
   
   *Figure 1: In the Figure, all calculation steps of the ReGWSWUSE software are illustrated, starting from the sector-specific input data to the aggregation of cross-sectoral results. It is shown that for the sectors of households, industry, thermal power plants, and livestock, the consumptive use and water withdrawals are input in the unit m³/year. For irrigation, only the consumptive use is input, specifically in the unit m³/month.*


Calculation of GW and SW Parts of Consumptive Use
#################################################

The first calculation step performed for all sectors is the calculation of consumptive use of groundwater and surface water using time-invariant raster data on the sector-specific relative share of groundwater use (fraction_gw_use). The sector-specific consumptive uses (consumptive_use_tot) are multiplied by the relative shares of groundwater use to obtain the consumptive use of groundwater per sector. Subsequently, the consumptive groundwater use is subtracted from the total consumptive use on a cell-by-cell basis to derive the consumptive use of surface water per sector. In WaterGAP 2.2e, it is assumed that the livestock and thermal power plant sectors rely exclusively on surface water.

Adjust Consumptive Use in Irrigation
####################################
Before this step is conducted, the input consumptive use for irrigation is modified. This modification consists of three optional steps that can be set through configuration.

The first modification can be used when the input consumptive use refers to areas equipped for irrigation (AEI) and the irrigation results should pertain to actually irrigated areas (AAI). When this configuration is enabled ("input_based_on_aei": True), the consumptive use is multiplied by the annual relative shares of AAI to AEI (fraction_aai_aei). The annual fraction_aai_aei values are country-specific and generated based on time series of national AAI and AEI from AQUASTAT.

The second modification (configuration: correct_irr_simulation_by_t_aai: True) serves to correct the consumptive use for irrigation for the years 2016 to 2020 using a time factor (time_factor_aai) based on the temporal development of AAI since 2015. This modification is intended to incorporate updated irrigation area information up to the year 2020. In GIM, the consumptive use is calculated considering the HID dataset, which includes raster data for AEI up to 2015.

The third modification of the irrigation-specific consumptive use accounts for deficit irrigation under certain conditions, such that irrigation does not lead to optimal growth of the crops. In WaterGAP, two conditions for deficit irrigation are defined. The first condition relates to the average annual groundwater depletion rate for the period from 1980 to 2009. If this rate exceeds 5 mm per year on average for the period, the first condition for a raster cell is met. The second condition for deficit irrigation pertains to the share of irrigation in total water withdrawals per raster cell for the period from 1960 to 2000; if this share exceeds 5%, this condition is also met. If the conditions for deficit irrigation for a raster cell are satisfied, the consumptive use is multiplied by the deficit_irrigation_factor, which is also set via configuration. 

These are the three modification options for consumptive use in irrigation. For the WaterGAP 2.2e version, only the consideration of deficit irrigation with a deficit_irrigation_factor of 0.7 is included, provided that the previously described conditions are met.

Calculation of GW and SW Parts of Abstraction
#############################################

After splitting the sectoral consumptive uses into groundwater and surface water, the water withdrawals for groundwater and surface water are calculated for each sector. For the sectors of households, industry, thermal power plants, and livestock, this calculation follows the same procedure as the calculation of groundwater and surface water shares of consumptive use, utilizing the sector-specific relative share of groundwater use.

For the irrigation sector, this calculation process differs. The groundwater and surface water shares of the water withdrawals for irrigation are derived from the previously calculated corresponding shares of consumptive use divided by the specific irrigation efficiencies for groundwater and surface water. Once the groundwater and surface water shares of water withdrawals for irrigation are calculated, the total water withdrawals for irrigation can be determined by summation.

The irrigation efficiency for groundwater is set within the software, and there are two configuration modes for this, which are set via "irr_efficiency_gw_mode." The "enforce" mode, derived from the WaterGAP 2.2e version, sets the irrigation efficiency for groundwater uniformly to the value efficiency_gw_threshold, which is 0.7 in version 2.2e. The "adjust" mode assumes that the irrigation efficiency is at least equal to that for surface water or takes the value of efficiency_gw_threshold.

Calculation of Complete Return Flows
####################################

Following the splitting and calculation of water withdrawals, the calculation of return flows overall and specifically for groundwater and surface water is performed. This process is identical for all sectors. First, the total returns (return_flow_tot) are calculated by subtracting the consumptive use from the water withdrawal, yielding the completely excess water that is not evapotranspired during use and flows back. 

Next, the absolute groundwater share of the return flow is calculated by multiplying with the relative groundwater share of the return (fraction_return_gw). By subtracting the absolute groundwater share from the total return flow, the surface water share of the return flow (return_flow_sw) is determined.

Calculation of Net Abstractions
###############################

The net abstractions for groundwater (net_abstraction_gw) and surface water (net_abstraction_sw) are calculated separately and are the same for all sectors. They are defined as the difference between water withdrawals and returns to the respective water resource. To clarify, this means sector-specific groundwater withdrawals minus sector-specific returns to groundwater, and analogously for surface water.

Unit Conversion (m³/year to m³/month)
#####################################
To aggregate cross-sectoral total results for consumptive uses, water withdrawals, returns, and net abstractions, all sector-specific results must be in the same temporal resolution and unit. Since there is monthly variability for the irrigation sector, the cross-sectoral results for the individual variables should also be in monthly resolution and the unit m³/month. For this purpose, the annual data for households, industry, thermal power plants, and livestock are converted from annual resolution and the unit m³/year to data with monthly resolution and the unit m³/month. The annual values are divided by the number of days in the year and multiplied by the number of days in the corresponding month. In WaterGAP, 365 days are assumed for calculations for each year, meaning that February is assumed to have 28 days every year.

Aggregation of Cross-Sectoral Results
#####################################

Once all sector-specific calculations are completed, the aggregation of the computed values occurs. These aggregated data provide a comprehensive overview of water withdrawals, returns, consumptive use, and net abstractions across all sectors. All cross-sectoral raster data is presented in monthly resolution and the unit m³/month.

Aggregated Values Include:

Consumptive Use
- Total consumptive use (total.consumptive_use_tot)
- Consumptive use derived exclusively from groundwater sources (total.consumptive_use_gw)
- Consumptive use derived exclusively from surface water sources (total.consumptive_use_sw)

Water Withdrawals
- Total water withdrawal (total.water_withdrawal_tot)
- Water withdrawal exclusively from groundwater sources (total.water_withdrawal_gw)
- Water withdrawal exclusively from surface water sources (total.water_withdrawal_sw)

Returns
- Total returns (total_return_flow_tot)
- Returns exclusively to groundwater sources (total.return_flow_gw)
- Returns exclusively to surface water sources (total.return_flow_sw)

Net Abstractions
- Net abstraction from groundwater sources (total.net_abstraction_gw)
- Net abstraction from surface water sources (total.net_abstraction_sw)

Additionally, for the irrigation sector, optional functions can be used to adjust the irrigation-specific consumptive use, and the irrigation-specific water withdrawals are fully calculated in GWSWUSE using groundwater and surface water-specific irrigation efficiencies.

While the sectors of households, industry, thermal power plants, and livestock differ only in their assumptions about certain variables and do not show sector-specific differences in the simulations, the irrigation sector also differs in simulation logic and temporal resolution. In WaterGAP, it is assumed that potential water use remains constant throughout the year for the sectors of households, industry, thermal power plants, and livestock. In contrast, it is assumed that irrigation use varies from month to month. This is due to the monthly variability assumed for the irrigation sector in WaterGAP, as well as additional adjustment functions for irrigation-specific consumptive use (e.g., deficit irrigation).


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

.. math::


2. **Correction with Time Factor (t_aai)**  
   Based on the configuration option `cm.correct_irr_by_t_aai`, the potential consumptive water use, :math:`irr.cu_tot`, for the years 2016 to 2020 is adjusted using the time factor :math:t_aai` (time_factor_aai).

.. math::
	

3. **Deficit Irrigation Mode (`cm.deficit_irrigation_mode`)**  
   Next, the configuration setting for :math:`cm.deficit_irrigation_mode` is applied:

Calculation of Groundwater and Surface Water Use
************************************************

Using a time-invariant, irrigation-specific raster that represents the relative shares of groundwater use in the irrigation sector, :math:`irr.fraction_gw_use`, the potential consumptive use of groundwater and surface water is calculated.

.. math::
	

.. math::
	



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

.. math::
	CU_{gw,dom}(y,id) = CU_{tot,dom}(y,id) * f_{gw,dom}(id)

.. math::
	CU_{sw,dom}(y,id) = CU_{tot,dom}(y,id) * (1 - f_{gw,dom}(id))

For water abstractions from groundwater (:math:`WU_{gw,dom}`) and surface water (:math:`WU_{sw,dom}`) in the domestic sector:

.. math::
	WU_{gw,dom}(y,id) = WU_{tot,dom}(y,id) * f_{gw,dom}(id)

.. math::
	WU_{sw,dom}(y,id) = WU_{tot,dom}(y,id) * (1 - f_{gw,dom}(id))


Calculation of Return Flows
***************************

Manufacturing-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from manufacturing water use (:math:`RF_{tot,dom}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,dom}`) and surface water (:math:`RF_{sw,dom}`), according to the relative share of return flows to groundwater within total manufacturing sector returns (:math:`f_{return,gw,dom }`):


.. math::
	RF_{tot,dom}(y,id) = WU_{tot,dom}(y,id) - CU_{tot,dom}(y,id)

.. math::
	RF_{gw,dom}(y,id) = RF_{tot,dom}(y,id) * f_{return,gw,dom}(,id)

.. math::
	RF_{sw,dom}(y,id) = RF_{tot,dom}(y,id) * (1 - f_{return,gw,dom}(id))


Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,dom}`) and surface water (:math:`NA_{sw,dom}`) in the domestic sector are calculated similarly:

.. math::
	NA_{gw,dom}(y,id) = WU_{gw,dom}(y,id) - RF_{gw,dom}(y,id)

.. math::
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

.. math::
	CU_{gw,man}(y,id) = CU_{tot,man}(y,id) * f_{gw,man}(id)

.. math::
	CU_{sw,man}(y,id) = CU_{tot,man}(y,id) * (1 - f_{gw,man}(id))

For water abstractions from groundwater (:math:`WU_{gw,man}`) and surface water (:math:`WU_{sw,man}`) in the manufacturing sector:

.. math::
	WU_{gw,man}(y,id) = WU_{tot,man}(y,id) * f_{gw,man}(id)

.. math::
	WU_{sw,man}(y,id) = WU_{tot,man}(y,id) * (1 - f_{gw,man}(id))


Calculation of Return Flows
***************************

Manufacturing-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from manufacturing water use (:math:`RF_{tot,man}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,man}`) and surface water (:math:`RF_{sw,man}`), according to the relative share of return flows to groundwater within total manufacturing sector returns (:math:`f_{return,gw,man }`):


.. math::
	RF_{tot,man}(y,id) = WU_{tot,man}(y,id) - CU_{tot,man}(y,id)

.. math::
	RF_{gw,man}(y,id) = RF_{tot,man}(y,id) * f_{return,gw,man}(,id)

.. math::
	RF_{sw,man}(y,id) = RF_{tot,man}(y,id) * (1 - f_{return,gw,man}(id))


Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,man}`) and surface water (:math:`NA_{sw,man}`) in the manufacturing sector are calculated similarly:

.. math::
	NA_{gw,man}(y,id) = WU_{gw,man}(y,id) - RF_{gw,man}(y,id)

.. math::
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

.. math::
	CU_{gw,tp}(y,id) = CU_{tot,tp}(y,id) * f_{gw,tp}(id)

.. math::
	CU_{sw,tp}(y,id) = CU_{tot,tp}(y,id) * (1 - f_{gw,tp}(id))


For water abstractions from groundwater (:math:`WU_{gw,liv}`) and surface water (:math:`WU_{sw,liv}`) in the thermal power sector:

.. math::
	WU_{gw,liv}(y,id) = WU_{tot,liv}(y,id) * f_{gw,liv}(id)

.. math::
	WU_{sw,liv}(y,id) = WU_{tot,liv}(y,id) * (1 - f_{gw,liv}(id))

Calculation of Return Flows
***************************

Thermal Power-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from thermal power water use (:math:`RF_{tot,tp}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,tp}`) and surface water (:math:`RF_{sw,tp}`), according to the relative share of return flows to groundwater within total thermal power sector returns (:math:`f_{return,gw,tp}`):

.. math::
	RF_{tot,tp}(y,id) = WU_{tot,tp}(y,id) - CU_{tot,tp}(y,id)

.. math::
	RF_{gw,tp}(y,id) = RF_{tot,tp}(y,id) * f_{return,gw,tp}(,id)

.. math::
	RF_{sw,tp}(y,id) = RF_{tot,tp}(y,id) * (1 - f_{return,gw,tp}(id))

Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,man}`) and surface water (:math:`NA_{sw,man}`) in the manufacturing sector are calculated similarly:

.. math::
	NA_{gw,tp}(y,id) = WU_{gw,tp}(y,id) - RF_{gw,tp}(y,id)

.. math::
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

.. math::
	CU_{gw,liv}(y,id) = CU_{tot,liv}(y,id) * f_{gw,liv}(id)

.. math::
	CU_{sw,liv}(y,id) = CU_{tot,liv}(y,id) * (1 - f_{gw,liv}(id))

For water abstractions from groundwater (:math:`WU_{gw,liv}`) and surface water (:math:`WU_{sw,liv}`) in the manufacturing sector:

.. math::
	WU_{gw,liv}(y,id) = WU_{tot,liv}(y,id) * f_{gw,liv}(id)

.. math::
	WU_{sw,liv}(y,id) = WU_{tot,liv}(y,id) * (1 - f_{gw,liv}(id))


Calculation of Return Flows
***************************

Manufacturing-specific return flows are calculated analogously to irrigation and domestic sector return flows. First, the total return flows from livestock water use (:math:`RF_{tot,liv}`) are calculated, followed by the division of these flows into groundwater (:math:`RF_{gw,liv}`) and surface water (:math:`RF_{sw,liv}`), according to the relative share of return flows to groundwater within total livestock sector returns (:math:`f_{return,gw,liv}`):


.. math::
	RF_{tot,liv}(y,id) = WU_{tot,liv}(y,id) - CU_{tot,liv}(y,id)

.. math::
	RF_{gw,liv}(y,id) = RF_{tot,liv}(y,id) * f_{return,gw,liv}(,id)

.. math::
	RF_{sw,liv}(y,id) = RF_{tot,liv}(y,id) * (1 - f_{return,gw,liv}(id))


Calculation of Net Abstractions
*******************************

Net abstractions for groundwater (:math:`NA_{gw,liv}`) and surface water (:math:`NA_{sw,liv}`) in the livestock sector are calculated similarly:

.. math::
	NA_{gw,liv}(y,id) = WU_{gw,liv}(y,id) - RF_{gw,liv}(y,id)

.. math::
	NA_{sw,liv}(y,id) = WU_{sw,liv}(y,id) - RF_{sw,liv}(y,id)



Cross-Sectoral Aggregate Results
################################

After calculating sector-specific results for consumptive uses, water withdrawals, returns, and net withdrawals from or towards groundwater and surface water, the sector-specific results for each variable are summed to derive cross-sectoral totals. To compute the aggregate cross-sectoral results, sector-specific results must be harmonized with regard to temporal resolution and unit consistency. This process involves initially summing results across the household, industrial production, thermal power, and livestock sectors, then dividing by 365 days and multiplying by the number of days in the month to standardize to units of :math:`{m}^{3}`:math:`{/}`:math:`{m}^{3}`{month}`. These values can then be combined with irrigation-specific results to finalize the aggregate cross-sectoral results.

Consumptive Wateruse
********************

.. math::
	CU_{tot}(y,m,id) = CU_{tot,irr}(y,m,id) + \frac{CU_{tot,dom}(y,id) + CU_{tot, man}(y,id) + CU_{tot,tp}(y,id) + CU_{tot,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


.. math::
	CU_{gw}(y,m,id) = CU_{gw,irr}(y,m,id) + \frac{CU_{gw,dom}(y,id) + CU_{gw, man}(y,id) + CU_{gw,tp}(y,id) + CU_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	CU_{sw}(y,m,id) = CU_{sw,irr}(y,m,id) + \frac{CU_{sw,dom}(y,id) + CU_{sw, man}(y,id) + CU_{sw,tp}(y,id) + CU_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


Wateruse
********
.. math::
	WU_{tot}(y,m,id) = WU_{tot,irr}(y,m,id) + \frac{WU_{tot,dom}(y,id) + WU_{tot,man}(y,id) + WU_{tot,tp}(y,id) + WU_{tot,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

.. math::
	WU_{gw}(y,m,id) = WU_{gw,irr}(y,m,id) + \frac{WU_{gw,dom}(y,id) + WU_{gw,man}(y,id) + WU_{gw,tp}(y,id) + WU_{gw,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

.. math::
	WU_{sw}(y,m,id) = WU_{sw,irr}(y,m,id) + \frac{WU_{sw,dom}(y,id) + WU_{sw,man}(y,id) + WU_{sw,tp}(y,id) + WU_{sw,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

.. math::
	WU_{tot}(y,m,id) = WU_{tot,irr}(y,m,id) + WU_{tot,dom}(y,id) + WU_{tot,man}(y,id) + WU_{tot,tp}(y,id) + WU_{tot,liv}(y,id)

.. math::
	WU_{gw}(y,m,id) = WU_{gw,irr}(y,m,id) + WU_{gw,dom}(y,id) + WU_{gw,man}(y,id) + WU_{gw,tp}(y,id) + WU_{gw,liv}(y,id)

.. math::
	WU_{sw}(y,m,id) = WU_{sw,irr}(y,m,id) + WU_{sw,dom}(y,id) + WU_{sw,man}(y,id) + WU_{sw,tp}(y,id) + WU_{sw,liv}(y,id)

Returns
*******

.. math::
	RF_{tot}(y,m,id) = RF_{tot,irr}(y,m,id) + \frac{RF_{tot,dom}(y,id) + RF_{tot,man}(y,id) + RF_{tot,tp}(y,id) + RF_{tot,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	RF_{gw}(y,m,id) = RF_{gw,irr}(y,m,id) + \frac{RF_{gw,dom}(y,id) + RF_{gw,man}(y,id) + RF_{gw,tp}(y,id) + RF_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	RF_{sw}(y,m,id) = RF_{sw,irr}(y,m,id) + \frac{RF_{sw,dom}(y,id) + RF_{sw,man}(y,id) + RF_{sw,tp}(y,id) + RF_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


Net Abstractions
****************

.. math::
	NA_{gw}(y,m,id) = NA_{gw,irr}(y,m,id) + \frac{NA_{gw,dom}(y,id) + NA_{gw, man}(y,id) + NA_{gw,tp}(y,id) + NA_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	NA_{sw}(y,m,id) = NA_{sw,irr}(y,m,id) + \frac{NA_{sw,dom}(y,id)+NA_{sw, man}(y,id) + NA_{sw,tp}(y,id) + NA_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}
