Soil Storage 
===============
This module computes soil storage and related fluxes for all grid cells based on section 4.4 of Müller Schmied et al 2021 [1]_.

.. autoclass:: soil.Soil
    :members:


.. note:: 
   The computation order for the soil storage module is as follows:
   First, :ref:`immediate runoff (R1) <immediate_runoff>` is calculated. After, 
   :ref:`effective precipitation <effective_precipitation>` is reduced by the immediate runoff. 
   Then, :ref:`daily runoff (R3) <runoff>` is calculated followed by :ref:`actual evapotranspiration <actual_evapotranspiration>`. 
   Soil storage is updated. Afterwards, :ref:`ground water recharge <diffuse_groundwater_recharge>` is calculated based on daily runoff.
   Then, total daily runoff from land (RL) is calculated as:

   .. math::
      RL = R1 + R3 + R2

   where soil water overflow (R2) is calulated as:

   .. math::
      {P}_{eff} = 
      \begin{cases}
      {P}_{eff} +{S}_{s,p} - {S_s,max}, & \text{if } ({P}_{eff} + {S}_{s,p})>{S_s}_{,max} \\
      0, & \text{otherwise}
      \end{cases}

      
   where :math:`{P}_{eff}` is :ref:`effective precipitation <effective_precipitation>`, :math:`{S}_{s,p}` and :math:`{S_s,max}` is :ref:`soil storage <soil_storage>`
   of previous day and maximum soil storage respectively.
   
   Surface runoff is finally calculated as total daily runoff from land minus ground water recharge.

Water balance
-------------
.. _soil_storage:

Soil storage :math:`S_s` :math:`(mm)` is calculated as:

.. math::
   \frac{dS_s}{d_t} =  {P}_{eff} − {R}_{l}− {E}_{s}

where :math:`{P}_{eff}` is effective precipitation :math:`(mm/d)`, :math:`{R}_{l}` is runoff from land :math:`(mm/d)` and :math:`{E}_{s}` is  the actual evapotranspiration from soil :math:`(mm/d)`.

Inflows
-------
Effective precipitation :math:`{P}_{eff}` is  is calculated as

.. _effective_precipitation:

.. math::
   {P}_{eff} = {P}_{t} − {P}_{sn} + M

where :math:`{P}_{t}` is throughfall :math:`(mm/d)`, :math:`{P}_{sn}` is snowfall :math:`(mm/d)` and :math:`M` is snow melt :math:`(mm/d)`.

.. note::
   In urban areas (defined from MODIS data) :math:`50 \%` of :math:`{P}_{eff}` is directly turned into immediate runoff and is calculated as:

.. _immediate_runoff:

   .. math::
     {immediate \: runoff} = 0.5 \times {P}_{eff}  \times fraction \: of \: build \: up \: area

   Next, effective precipitation is reduced by the immediate runoff. The resulting effective precipitation used to compute the soil water balance. 
   See function **immediate runoff** : in source code. 

Outflows
--------
Actual evapotranspiration :math:`{E}_{s}`  from soil :math:`(mm/d)` is calculated as

.. _Actual_evapotranspiration:

.. math::
    {E}_{s} = min\biggl(({E}_{pot} - E_c) , ({E}_{pot,max} - E_c) \times \frac{S_s}{S_s,max} \biggr)  

where :math:`{E}_{pot}` is potential evapotranspiration :math:`(mm/d)`, :math:`{E}_{c}` is canopy evaporation :math:`(mm/d)` and :math:`{S}_{s,max}` is the maximum soil water content :math:`(mm)` derived as a product of total available water capacity in the upper meter of the soil [2]_ and land-cover-specific rooting depth (Table C2 [1]_). The maximum potential evapotranspiration :math:`{E}_{pot,max}` is set to :math:`15 (mm/d)` globally. 


Daily runoff from soil :math:`{R3} (mm/day)` is calculated following Bergström (1995) [3]_ as

.. _runoff:

.. math::
   R3 = {P}_{eff} \biggl(\frac{S_s}{S_s,max}\biggr)^\Gamma

where \Gamma is the runoff coefficient (–). This parameter, which varies between 0.1 and 5.0, is used for calibration.
Together with soil saturation, it determines the fraction of :math:`{P}_{eff}` that becomes :math:`{R1}`.

.. note::
     If the sum of :math:`{P}_{eff}` and :math:`S_s` of the previous day exceed :math:`{S_s,max}`, the overflow  :math:`{R2}` is added together with 
     daily runoff :math:`{R1}` and immediate runoff :math:`{R3}` to total daily runoff from land :math:`{R}_{L}`.


:math:`{R1}` is partitioned into fast surface and subsurface runoff :math:`{R}_{s}` and diffuse groundwater recharge :math:`{R}_{g}` according to the :ref:`heuristic scheme <watergap_scheme>`.

.. _diffuse_groundwater_recharge:

.. math::
   {R}_{g} = min\biggl({R}_{gmax} , ({f}_{g} \times {Rl} \biggr)  

where :math:`{R}_{gmax}` is soil-texture-specific maximum groundwater recharge with values of 7, 4.5 and 2.5 (mm/d) for sandy,
loamy and clayey soils, respectively, and :math:`{f}_{g}` is the groundwater recharge factor ranging between 0 and 1. :math:`{f}_{g}` is determined
based on relief, soil texture, aquifer type, and the existence of permafrost or glaciers [4]_. 

.. note:: 
   If a grid cell is defined as (semi)arid and has coarse (sandy) soil, groundwater recharge will only occur if precipitation exceeds a critical value of 12.5 mm/d, otherwise the water remains in the soil. The fraction of :math:`{R}_{1}` that does not recharge the groundwater becomes :math:`{R}_{s}`, which recharges surface water bodies and the river compartment.



References 
----------


.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021

.. [2] Batjes, N. H.: ISRIC-WISE derived soil properties on a 5 by 5 arc-minutes global grid (ver. 1.2), Tech. Rep. 2012/01, ISRIC–World Soil Information, Wageningen, 2012.

.. [3] Bergström, S.: The HBV model, in: Computer models of watershed hydrology, edited by: Singh, V., Water Resources Publications, Lone Tree, USA, 443–476, 1995

.. [4] Döll, P. and Fiedler, K.: Global-scale modeling of groundwater recharge, Hydrol. Earth Syst. Sci., 12, 863–885, https://doi.org/10.5194/hess-12-863-2008, 2008.
