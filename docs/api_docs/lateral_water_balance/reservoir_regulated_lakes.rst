.. _reservoir:

##########
Reservoirs
##########

In WaterGAP, reservoirs with a storage capacity of at least :math:`0.5` :math:`{km}^{3}` are classified as “global” reservoirs. Similarly, global regulated lakes (lakes where outflow is controlled by a dam or weir) must have a maximum storage capacity of at least :math:`0.5` :math:`{km}^{3}` or cover an area exceeding :math:`100` :math:`{km}^{2}`. Both types are modeled using the same water balance equation.

The outflow from these reservoirs and regulated lakes is simulated using a modified version of the Hanasaki et al. (2006) algorithm [5]_, which differentiates between those primarily used for irrigation and others [4]_. As with global lakes, the water balance for global reservoirs and regulated lakes is calculated at the outflow cell [1]_ [6]_. Maximum water storage capacity, primary use, and commissioning years are available from the GRanD database [1]_ [6]_.

In WGHM, reservoirs begin filling at the start of their commissioning year, and regulated lakes transition from global lakes to global regulated lakes [1]_. A total of 1255 reservoirs and 88 regulated lakes are considered. However, those sharing the same outflow cell are combined into a single water storage compartment by summing their maximum storages and areas, resulting in the simulation of 1181 global reservoirs and 86 regulated lake compartments in WGHM [6]_.

.. note::
   There can be only one global reservoir/regulated lake compartment per grid cell.

.. autofunction:: reservior_regulated_lakes.reservior_and_regulated_lake

*************
Water balance
*************
Reservoir storage :math:`{S}_{res}` :math:`[m^3]` is computed as

.. math::
   \frac{dS_res}{d_t} =  {Q}_{in} + A(P  − {E}_{pot}) − {R_g}_{rest}  − {NA}_{l}  − {Q}_{out}

where :math:`{Q}_{in}` is inflow into the reservoir from upstream [:math:`{m}^{3}` :math:{d}^{-1}]`, 
:math:`A` is the reservoir surface area :math:`[m^2]` in the grid cell at time step :math:`t`,
:math:`P` is precipitation [:math:`{m}^{3}` :math:{d}^{-1}]`, :math:`{E}_{pot}` is :ref:`potential evapotranspiration <pot_evap>` [:math:`{m}^{3}` :math:{d}^{-1}]`, :math:`{R}_{g,res}` is point source groundwater recharge from the water body (only in arid/semiarid regions) [:math:`{m}^{3}` :math:{d}^{-1}]`, :math:`{NA}_{res}` is net abstraction from reservoirs [:math:`{m}^{3}` :math:{d}^{-1}]` 
and :math:`{Q}_{out}` is the outflow from the water body to other surface water bodies including river storage [:math:`{m}^{3}` :math:{d}^{-1}]`. 


In the case of global reservoirs/regulated lakes, which may cover more than one :math:`0.5° \times 0.5°` cell, an area adjustment is not made (as done for local lake and wetland area :ref:<lake_red>), as it is not known in which grid cells the area reduction occurs. Here we only compute reduction factor :math:r to reduce evaporation. This will prevent continuous decline of global reservoir levels in some cases such as semiarid regions.

The reduction factor :math:`{r}` is computed as:

.. _reservoir_red:

.. math::
   r = 1- \left(\frac{|S_res - Sres,max|}{{S}_{res,max}}\right)^p,  0 <= r <=1


where :math:`{S}_{res}` is the volume of the water :math:`{m}^{3}` stored in the reservoir at time step :math:`{t}` :math:`days`, :math:`{S}_{res,max}` is the maximum storage of the reservoi :math:`{m}^{3}`. Reduction exponent :math:`{p}` is :math:`{2.184}` [1]_. 

.. note::
   In the case of reservoirs/regulated lakes, storage capacity :math:`{S}_{res,max}` is taken from the database [1]_. Reservoir area is reduced by 15% if :math:`{S}_{res}` is 50% of :math:`{S}_{res,max}` and by 75% if Sres is only 10% of :math:`{S}_{res,max}`. For regulated lakes without available maximum storage capacity, :math:`{S}_{res,max}` is computed as in the case of :ref:global lakes<lakes and wetlands>.

   Reservoir and regulated lake storage is not allowed to fall below 10% of its storage capacity [1]_.

*******
Inflows
*******

Computation of inflow :math:`{Q}_{in}`; global reservoirs receive inflow from both local runoff and river inflow from upstream grid cells (see :ref:`watergap schematic <model_schematic>`). 

********
Outflows
********

.. autofunction:: reservoir_release_hanasaki.hanasaki_res_reslease

Reservoirs also lose water through :ref:`evaporation <pot_evap>` (:math:`{E}_{pot}`), which is assumed to be equal to the potential evapotranspiration computed using the Priestley–Taylor equation with an albedo of 0.08.

In arid and semiarid grid cells, reservoirs are assumed to recharge the groundwater through focused groundwater recharge (:math:`{R}_{{g}_{res}}`) is calculated as:

.. math::
   {R}_{{g}_{res}} = {k}_{{gw}_{res}} * {r} * {A}_{max}

where :math:`{k}_{{gw}_{res}}` is the groundwater recharge constant below reservoirs :math:`[0.01 {m}*{d}^{-1}]`.

..note::
	Unlike the commissioning year of a reservoir, which marks the completion of the dam [1]_, the operational year refers to the 12-month period during which reservoir management is specified. This period begins with the first month where the naturalized mean monthly streamflow falls below the annual mean.

To compute the daily outflow, e.g. release, from global reservoirs/regulated lakes, the total annual outflow during the reservoir-specific operational year is calculated as:

.. math::
	{Q}_{out,res,annual} = {k}_{rele} * {Q}_{dis,mean,annual}

with {k}_{rele} being the reservoir release factor that is computed each year on the first day of the operational year as:

.. math::
 	{k}_{rele} = \frac{{S}_{res}}}{}

where :math:`{S}_{res}` is the reservoir/regulated lake storage [:math:`{m}^{3}`], and :math:`{S}_{res,max}` is the storage capacity [:math:`{m}^{3}`]. Thus, total release in an operational year with low reservoir storage at the beginning of the operational year will be smaller than in a year with high reservoir storage.

In the initial filling phase of a reservoir after dam construction, :math:`{k}_{rele}` is set to :math:`{0.1}` until :math:`{S}_{res}` exceeds 10% of its maximum capacity (:math:`{S}_{res,max}`). We define a capacity ratio (:math:`{c}_{ratio}`) as:

.. math::
  	{c}_{ratio} = \frac{{S}_{res,max}}{{Q}_{dis,mean,annual}}

If :math:`{c}_{ratio}` is greater than :math:`{0.5}`, the outflow from a non-irrigation reservoir remains constant and independent of actual inflow. 

For irrigation reservoirs, outflow is determined by monthly net abstractions in the next five downstream cells or up to the next reservoir [4]_ [5]_. For reservoirs with a lower ratio (:math:`{c}_{ratio}` :math:`<` :math:`0.5), the release also depends on daily inflow, increasing on days with high inflow [5]_. If the reservoir storage falls below 10% of :math:`{S}_{res,max}`, the release is reduced to 10% of the normal release to maintain a minimum environmental flow for ecosystems. Daily outflow may also include overflow if the reservoir’s storage capacity is exceeded due to high inflow.

##########
References 
##########
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
.. [2] Döll, P., Müller Schmied, H., Schuh, C., Portmann, F. T., and Eicker, A. (2014). Global-scale assessment of groundwater depletion and related groundwater abstractions: Combining hydrological modeling with information from well observations and GRACE satellites, Water Resour. Res., 50, 5698–5720, https://doi.org/10.1002/2014WR015595
.. [3] Döll, P., Kaspar, F., and Lehner, B. (2003). A global hydrological model for deriving water availability indicators: model tuning and validation, J. Hydrol., 270, 105–134, https://doi.org/10.1016/S0022-1694(02)00283-4
.. [4] Döll, P., Fiedler, K., and Zhang, J.: Global-scale analysis of river flow alterations due to water withdrawals and reservoirs, Hydrol. Earth Syst. Sci., 13, 2413–2432, https://doi.org/10.5194/hess-13-2413-2009, 2009
.. [5] Naota Hanasaki, Shinjiro Kanae, Taikan Oki; A reservoir operation scheme for global river routing models; Journal of Hydrology; Volume 327, Issues 1–2; 2006; https://doi.org/10.1016/
.. [6] Müller Schmied, H., Trautmann, T., Ackermann, S., Cáceres, D., Flörke, M., Gerdener, H., Kynast, E., Peiris, T. A., Schiebener, L., Schumacher, M., and Döll, P.: The global water resources and use model WaterGAP v2.2e: description and evaluation of modifications and new features, Geosci. Model Dev. Discuss. [preprint], https://doi.org/10.5194/gmd-2023-213, in review, 2023.
