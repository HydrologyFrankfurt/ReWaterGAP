.. _irrigation_gwswuse:

#####################
Irrigation Simulation
#####################

Input Data
##########

The irrigation-specific ReGWSWUSE simulation is based on input data for the following variables:

- irr.consumptive_use_tot_aei or irr.consumptive_use_tot_aai (total consumptive use for irrigation)
- irr.fraction_gw_use (fraction of groundwater used)
- irr.fraction_return_gw (fraction of returns to groundwater)
- irr.efficiency_sw (efficiency for surface water use)

For scenarios of deficit irrigation, additional variables are considered:

- irr.gwd_mask (groundwater depletion mask)
- irr.abstraction_part_mask (abstraction part mask)
- irr.fraction_aei_aai (ratio of equipped versus actually irrigated area)
- irr.time_factor_aai (time factor for irrigated area adjustments)

Configuration Options
#####################

Runtime configuration options enable modification of the irrigation simulation in ReGWSWUSE through:

- Simulation Options that alter the simulation logic.
- Parameter Settings that allow specific parameter values to be set in the simulation.
- Configurable parameters in the configuration file include efficiency_gw_threshold and deficit_irrigation_factor. 

Simulation options include the following.

irrigation_efficiency_gw_mode
*****************************

Controls how groundwater irrigation efficiency (irr.efficiency_gw) is set, which is always temporally constant. Adjustable options incluse: 

- **enforce**: Sets the efficiency for each cell based on the efficiency_gw_threshold parameter.
- **adjust**: Efficiency varies by cell and considers both the groundwater efficiency threshold and surface water efficiency (irr.efficiency_sw), ensuring groundwater efficiency is at least equal to that of surface water.

irr_consumptive_use_input_based_on
**********************************

Specifies whether irrigation-specific potential consumptive use (irr.consumptive_use_tot) is based on areas equipped for irrigation (AEI) or those actually irrigated (AAI). Adjustable options incluse: 

- **aei**: When irr.consumptive_use_tot refers to equipped areas, it is multiplied by irr.fraction_aai_aei, representing the actual irrigated proportion.
- **aai**: When irr.consumptive_use_tot already refers to actually irrigated areas, the fraction is not applied.

correct_irr_simulation_by_t_aai
*******************************

This option adjusts potential monthly consumptive water use based on updated AAI values from 2015-2020, allowing area adjustments post-2015 using irr.time_factor_aai. Adjustable options incluse: 

- **true**: Multiplies potential consumptive use by time_factor_aai for updated AAI.
- **false**: Does not apply this adjustment.

deficit_irrigation_mode
***********************

If enabled, assumes deficit irrigation in cells with notable groundwater depletion rates (from 1980-2009) and significant irrigation abstraction rates (1960-2000), reducing irrigation by 30% below the optimal need. Adjustable options incluse: 

- **true**: Applies deficit irrigation factor adjustments.
- **false**: Assumes optimal irrigation levels.


Simulation logic
################

Preprocessing of irr.consumptive_use_tot
****************************************

The simulation starts with preprocessing of the input potential consumptive water use, `irr.cu_tot_input`. This preprocessing is based on configuration options, which are denoted by “cm.” in the following text. 

1. **Configuration Setting: cm.irr_input_based_on**  
   This setting is applied first:

.. math::
	
	CU_tot,irr(y,m,id) = 
	\begin{cases}
	CU_(tot,irr)(y,m,id) * \frac{{aai}{aei} ; cm.irr_input_based_on_aei = true \\
	CU_(tot,irr)(y,m,id) ; cm.irr_input_based_on_aei = false
	\end{cases}	
	

2. **Correction with Time Factor (t_aai)**  
   Based on the configuration option `cm.correct_irr_by_t_aai`, the potential consumptive water use, :math:`irr.cu_tot`, for the years 2016 to 2020 is adjusted using the time factor :math:t_aai` (time_factor_aai).

.. math::
 
	CU_tot,irr(y,m,id) = 
	\begin{cases}
	CU_{tot,irr}(y,m,id) * \frac{{aai}{aei} ; cm.irr_input_based_on_aei = true \\
	CU_(tot,irr)(y,m,id) ; cm.irr_input_based_on_aei = false
	\end{cases}	
	

3. **Deficit Irrigation Mode (`cm.deficit_irrigation_mode`)**  
   Next, the configuration setting for :math:`cm.deficit_irrigation_mode` is applied:

Calculation of Groundwater and Surface Water Use
************************************************

Using a time-invariant, irrigation-specific raster that represents the relative shares of groundwater use in the irrigation sector, :math:`irr.fraction_gw_use`, the potential consumptive use of groundwater and surface water is calculated.

.. math::
	
	CU_{tot,irr}(y,m,id) =
   	\begin{cases} 
   	CU_{tot,irr}(y,m,id) * \frac{aai}{aei} \\
   	b & \text{if } x \leq 0
   	\end{cases}
	

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
