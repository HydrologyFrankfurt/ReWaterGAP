.. _domestic_simulation_gwswue:

###################
Domestic Simulation
###################

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
