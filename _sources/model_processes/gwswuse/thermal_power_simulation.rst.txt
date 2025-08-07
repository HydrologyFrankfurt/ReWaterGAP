.. _thermal_power_simulation:

########################
Thermal Power Simulation
########################

The ReGWSWUSE simulation for the thermal power sector is analogous to the domestic-specific ReGWSWUSE simulation.

Input Data
##########

The ReGWSWUSE simulation for the thermal power sector relies on input data for the following variables:

- :math:`CU_{tot,tp}`: tp.consumptive_use_tot
- :math:`WU_{tot,tp}`: tp.abstraction_tot
- :math:`f_{gw,tp}`: tp.fraction_gw_use
- :math:`f_{return,gw,tp}`: tp.fraction_return_gw (0 if no input file provided)

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

