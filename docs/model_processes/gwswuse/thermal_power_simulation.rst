.. _thermal_power_simulation:

########################
Thermal Power Simulation
########################

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
