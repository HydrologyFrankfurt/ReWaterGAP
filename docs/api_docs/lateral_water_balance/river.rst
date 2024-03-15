.. _river:

=============
River Storage
=============

River storage and related fluxes are calculated based on section 4.7 of Müller Schmied et al 2021 [1]_.

.. autofunction:: river.river_water_balance

Water balance
-------------
River storage :math:`S_r` :math:`[m^3]` is computated as

.. _river_balance:

.. math::
   \frac{dS_r}{d_t} =  {Q}_{r,in} − {Q}_{r,out} − {NA}_{s,r}

where :math:`{Q}_{r,in}` is inflow into the river compartment [:math:`{m}^{3} {d}^{-1}`], :math:`{Q}_{r,out}` is the streamflow [:math:`{m}^{3} {d}^{-1}`], and :math:`{NA}_{s,r}` is the net abstraction of surface water from the river [:math:`{m}^{3} {d}^{-1}`].


Inflows
-------
The inflow :math:`{Q}_{r,in}` into the river compartment (if there are no surface water bodies) is the sum of :ref:`soil surface runoff <surface_runoff>` :math:`({R}_{s})`, :ref:`groundwater discharge <groundwater_discharge>` :math:`({Q}_{g})`, and upstream streamflow. Otherwise fraction of :math:`{R}_{s}` and :math:`{Q}_{g}` (in humid cells) is routed through the surface water bodies :ref:`(See: Model schematic) <model_schematic>`.  The outflow from the surface water body preceding the river compartment then becomes part of :math:`{Q}_{r,in}`. In addition, negative :ref:`net abstractions <net_abstractions>` :math:`({NA}_{s})` values due to high return flows from irrigation with groundwater lead to a net increase in storage. Thus, if no surface water bodies exist in the cell, negative :math:`{NA}_{s}` is added to :math:`{Q}_{r,in}`.


Outflows
--------

.. autofunction:: river.river_velocity

:math:`{Q}_{r,out}` is defined as the streamflow or river discharge that leaves a cell and is transported to the next cell downstream.

This is calculated as:

.. math::
	{Q}_{r,out} = \frac{V}{I} * {S}_{r} 

where :math:`{v}` :math:`[m/s]` is the velocity of the river flow, and :math:`{l}` is the river length :math:`[m]`. :math:`{l}` is calculated as the product of the cell's river segment length, derived from the HydroSHEDS drainage direction map [2]_, and a meandering ratio specific to that cell described in Verzano et al., 2012 [3]_. 

The velocity :math:`{v}` is calculated using the Manning–Strickler equation:

.. math::
	{v} = {n}^{-1} * {R}_{h}^{\frac{3}{2}} * {s}^{frac{1}{2}}


where :math:`{n}` is river bed roughness :math:`[–]`, :math:`{R}_{h}` is the hydraulic radius of the river channel :math:`[m]` and :math:`{s}` is river bed slope :math:`({m}*{m}^{-1})`. Calculation of :math:`{s}` is based on high-resolution elevation data (SRTM30), the HydroSHEDS drainage direction map and an individual meandering ratio. The predefined minimum :math:`{s}` is 0.0001 :math:`[{m}*{m}^{-1}]`.

Daily varying :math:`{R}_{h}` is calculated assuming a trapezoidal river cross section with a slope of 0.5. :math:`{R}_{h}` then can be calculated as a function of daily varying river depth :math:`{D}_{r}` and temporally constant bottom width :math:`{W}_{r,bottom}` [3]_. 
WaterGAP implements a consistent method for determining daily width and depth as a function of river water storage. As bankfull conditions are assumed to occur at the initial time step, the initial volume of water stored in the river is computed as:

.. math::
	{S}_{r,max} = 

where :math:`{S}_{r,max}` is the maximum volume of water that can be stored in the river at bankfull depth :math:`[{m}^3]`, :math:`{D}_{r,bf}` :math:`[{m}]` and :math:`{W}_{r,bf}` :math:`[{m}]` are river depth and top width at bankfull conditions, respectively, and :math:`{W}_{r,bottom}` is river bottom width :math:`[{m}]`. River water depth :math:`{D}_{r}` :math:`[{m}]` is simulated to change at each time step with actual :math:`{S}_{r}` as:

.. math::
	{D}_{r} = -{\frac{W_{r}{}}

**to be continued**

Using the equation for a trapezoid with a slope of 0.5, :math:`{R}_{h}` is then calculated from :math:`{W}_{r,bottom}` and :math:`{D}_{r}`. Bankfull flow is assumed to correspond to the maximum annual daily flow with a return period of 1.5 years [5]_ and is derived from daily streamflow time series.

The roughness coefficient :math:`{n}` of each grid cell is calculated according to Verzano et al. (2012), who modeled :math:`{n}` as a function of various spatial characteristics (e.g., urban or rural area, vegetation in river bed, obstructions) and a river sinuosity factor to achieve an optimal fit to streamflow observations. Because of the implementation of a new algorithm to calculate :math:`{D}_{r}`, we had to adjust their gridded :math:`{n}` values to avoid excessively high river velocities [6]_. By trial and error, we determined optimal n-multipliers at the scale of 13 large river basins that lead to a good fit to monthly streamflow time series at the most downstream stations and basin-average total water storage anomalies from GRACE. We found that in 9 out of 13 basins, multiplying :math:`{n}` by 3 resulted in the best fit between observed and modeled data. We therefore set the multiplier to 3 globally, except for the remaining four basins, where other values proved to be more adequate; this concerns the Lena basin, where :math:`{n}` is multiplied by 2; the Amazon basin, where :math:`{n}` is multiplied by 10; and the Huang He and Yangtze basins, where :math:`{n}` is kept at its original value (Fig. S1).

Net cell runoff :math:`{R}_{n,c}` :math:`({m}*{m*d}^{-1})`, the part of the cell precipitation that has neither been evapotranspirated nor stored with a time step, is calculated as:

.. math::
	{R}_{n,c} = 

where :math:`{A}_{cont}` is the continental area (0.5° \times 0.5° grid cell area minus ocean area) of the grid cell (:math:`[m^2]`). Renewable water resources are calculated as long-term mean annual :math:`{R}_{nc}` computed under naturalized conditions (Sect. 4.1). Renewable water resources can be negative if evapotranspiration in a grid cell is higher than precipitation due to evapotranspiration from global lakes, reservoirs or wetlands that receive water from upstream cells.

References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
.. [2] Lehner et al., 2008
.. [3] Verzano et al., 2012
.. [4] Allen et al. (1994)
.. [5] Schneider et al., 2011
.. [6] Schulze et al., 2005
