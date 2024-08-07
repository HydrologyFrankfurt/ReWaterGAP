.. _river:

#####
River
#####

River storage and related fluxes are calculated based on section 4.7 of Müller Schmied et al 2021 [1]_.

.. autofunction:: river.river_water_balance

*************
Water balance
*************
River storage :math:`S_r` :math:`[m^3]` is computated as

.. _river_balance:

.. math::
   \frac{dS_r}{d_t} =  {Q}_{r,in} − {Q}_{r,out} − {NA}_{s,r}

where :math:`{Q}_{r,in}` is inflow into the river compartment [:math:`{m}^{3} {d}^{-1}`], :math:`{Q}_{r,out}` is the streamflow [:math:`{m}^{3} {d}^{-1}`], and :math:`{NA}_{s,r}` is the :ref:`net abstractions <net_abstractions>` of surface water from the river [:math:`{m}^{3} {d}^{-1}`].

*******
Inflows
*******
The inflow :math:`{Q}_{r,in}` into the river compartment (if there are no surface water bodies) is the sum of :ref:`soil surface runoff <surface_runoff>` :math:`({R}_{s})`, :ref:`groundwater discharge <groundwater_discharge>` :math:`({Q}_{g})`, and upstream streamflow. Otherwise fraction of :math:`{R}_{s}` and :math:`{Q}_{g}` (in humid cells) is routed through the surface water bodies (See: :ref:`Model Schematic <model_schematic>`). The outflow from the surface water body preceding the river compartment then becomes part of :math:`{Q}_{r,in}`. In addition, negative net abstractions :math:`({NA}_{s})` values due to high return flows from irrigation with groundwater lead to a net increase in storage. Thus, if no surface water bodies exist in the cell, negative :math:`{NA}_{s}` is added to :math:`{Q}_{r,in}`.

********
Outflows
********

.. autofunction:: river.river_velocity

:math:`{Q}_{r,out}` is defined as the streamflow or river discharge that leaves a cell and is transported to the next cell downstream.

This is calculated as:

.. math::
	{Q}_{r,out} = \frac{v}{l} * {S}_{r} 

where :math:`{v}` :math:`[m/s]` is the velocity of the river flow, and :math:`{l}` is the river length :math:`[m]`. :math:`{l}` is calculated as the product of the cell's river segment length, derived from the HydroSHEDS drainage direction map [2]_, and a meandering ratio specific to that cell described in Verzano et al., 2012 [3]_. 

The velocity :math:`{v}` is calculated using the Manning–Strickler equation:

.. math::
	{v} = {n}^{-1} * {R}_{h}^{\frac{3}{2}} * {s}^{\frac{1}{2}}


where :math:`{n}` is river bed roughness :math:`[–]`, :math:`{R}_{h}` is the hydraulic radius of the river channel :math:`[m]` and :math:`{s}` is river bed slope :math:`[{m}*{m}^{-1}]` [1]_ .

Daily varying :math:`{R}_{h}` is calculated assuming a trapezoidal river cross section with a slope of 0.5. :math:`{R}_{h}` then can be calculated as a function of daily varying river depth :math:`{D}_{r}` and temporally constant bottom width :math:`{W}_{r,bottom}` [3]_. 
WaterGAP implements a consistent method for determining daily width and depth as a function of river water storage. Bankfull flow conditions are assumed to occur at the initial time step and the initial volume of water stored in the river is calculated as:

.. math::
	{S}_{r,max} = {\frac{1}{2}} * {l} * {D}_{r,bf} * ({W}_{r,bottom} + {W}_{r,bf})

where :math:`{S}_{r,max}` is the maximum volume of water that can be stored in the river at bankfull depth :math:`[{m}^3]`, :math:`{D}_{r,bf}` :math:`[{m}]` and :math:`{W}_{r,bf}` :math:`[{m}]` are river depth and top width at bankfull conditions, respectively, and :math:`{W}_{r,bottom}` is river bottom width :math:`[{m}]`. River water depth :math:`{D}_{r}` :math:`[{m}]` is simulated to change at each time step with actual :math:`{S}_{r}` as:

.. math::
	{D}_{r} = - {\frac{{W}_{r,bottom}}{4}} + {\sqrt{{{W}_{r,bottom}} * {\frac{{W}_{r,bottom}}{16}} + {0.5} * {\frac{{S}_{r}}{l}}}}

WaterGap also computes net cell runoff :math:`{R}_{n,c}` :math:`[{m}*{m*d}^{-1}]`, which is the part of the cell precipitation that has neither been evapotranspirated nor stored. It is calculated as:

.. math::
	{R}_{n,c} = {\frac{{Q}_{r,in}-{Q}_{r,out}}{{A}_{cont}}} * {10}^{9}

where :math:`{A}_{cont}` is the continental area (0.5° \times 0.5° grid cell area minus ocean area) of the grid cell (:math:`[m^2]`). Renewable water resources are calculated as long-term annual mean :math:`{R}_{nc}` under naturalized conditions (without human impact). It is possible for renewable water resources to be negative if evapotranspiration in a grid cell is higher than precipitation due to evapotranspiration from global lakes, reservoirs or wetlands that receive water from upstream cells.

##########
References 
##########
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
.. [2] Lehner, B., K. Verdin, and A. Jarvis (2008), New Global Hydrography Derived From Spaceborne Elevation Data, Eos Trans. AGU, 89(10), 93–94, doi:10.1029/2008EO100001.
.. [3] Verzano, K., Bärlund, I., Flörke, M., Lehner, B., Kynast, E., Voß, F., and Alcamo, J.: Modeling variable river flow velocity on continental scale: Current situation and climate change impacts in Europe, J. Hydrol., 424–425, 238–251, https://doi.org/10.1016/j.jhydrol.2012.01.005, 2012
.. [4] Allen, P. M., Arnold, J. C., and Byars, B. W.: Downstream channel geometry for use in planning level models, J. Am. Water Resour. As., 30, 663–671, https://doi.org/10.1111/j.1752-1688.1994.tb03321.x, 1994
.. [5] Schneider, C., Flörke, M., Eisner, S., and Voss, F.: Large scale modelling of bankfull flow: An example for Europe, J. Hydrol., 408, 235–245, https://doi.org/10.1016/j.jhydrol.2011.08.004, 2011
.. [6] Schulze, K., Hunger, M., and Döll, P.: Simulating river flow velocity on global scale, Adv. Geosci., 5, 133–136, https://doi.org/10.5194/adgeo-5-133-2005, 2005
