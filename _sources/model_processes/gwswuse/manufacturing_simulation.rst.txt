.. _manufacturing_simulation_gwswuse:

########################
Manufacturing Simulation
########################

The ReGWSWUSE simulation for the manufacturing sector is analogous to the domestic-specific ReGWSWUSE simulation.

Input Data
##########

The ReGWSWUSE simulation specific to the manufacturing sector relies on input data for the following variables:

- :math:`CU_{tot,man}`: man.consumptive_use_tot
- :math:`WU_{tot,man}`: man.abstraction_tot
- :math:`f_{gw,man}`: man.fraction_gw_use
- :math:`f_{return,gw,man}`: man.fraction_return_gw (0 if no input file provided)

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
