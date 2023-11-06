.. _groundwater_storage:

Groundwater Storage
===================
Groundwater storage and related fluxes are calculated based on section 4.5 of Müller Schmied et al 2021 [1]_.

.. autofunction:: groundwaterstorage.compute_groundwater_balance


Water balance
-------------
Groundwater storage :math:`S_g` :math:`(m^3)` is computated as

.. _groundwater_balance:

.. math::
   \frac{dS_g}{d_t} =  {R}_{g} − {R}_{gl,res,w}− {Q}_{g}- {NA}_{g}

where :math:`R_g` is diffuse groundwater recharge from soil (:math:`m^3 {d}^{-1}`).
:math:`{R}_{gl,res,w}` is point groundwater recharge from surface
water bodies (lakes, reservoirs and wetlands) in (semi)arid
areas (:math:`m^3 {d}^{-1}`), :math:`Q_g` is groundwater discharge (:math:`m^3 {d}^{-1}`) and :math:`NA_g` is net abstraction from groundwater
(:math:`m^3 {d}^{-1}`)


Inflows
-------

Diffuse groundwater recharge from soil  :math:`R_g (m^3 {d}^{-1})` is the main inflow in humid cells
and point groundwater recharge from surface water bodies (lakes, reservoirs and wetlands) :math:`{R}_{gl,res,w} (m^3 {d}^{-1})` is the main inflow in (semi)arid
grid cells. :math:`{R}_{gl,res,w}` varies temporally with the area of the surface water body, which depends on the respective water storage.


Outflows
--------
Groundwater discharge, :math:`Q_g (m^3 {d}^{-1})` to surface waterbodies is an outflow which is computed as:

.. math::
   {Q}_{g} =  {k}_{g} \times {S}_{g}


WaterGAP computes actual net abstraction from groundwater, :math:`NA_g (m^3 {d}^{-1})` from the potential net groundwater abstraction. 
The potential net abstraction from groundwater is computed from the Groundwater-Surface Water Use (GWSWUSE) model (see section 2 of Müller Schmied et al 2021 [1]_).
Details on the computation of the actual net abstaction groundwater can be found in the **Water Abstraction** section. 


.. note::
   :ref:`Groundwater storage <groundwater_balance>` is solved analytically for each timestep
   of one day to prevent numerical inaccuracies. This avoids the use of very small timesteps which will be computaionally 
   expensive and hence lead to numerical problems.
   
   Since :math:`R_g` , :math:`{R}_{gl,res,w}` and :math:`NA_g`  are constant per each time step, they are grouped as one constant called 
   Net recharge :math:`(NR={R}_{g} − {R}_{gl,res,w} − {NA}_{g})`. The final balance euqation to solve is then:
   
   .. math::
      \frac{dS_g}{d_t} =  NR − {Q}_{g}

   Analytical solution is given as:

   .. math::
      S_g(t) =  S_g(t-1) \times {exp}^{-k_g} + \frac{NR}{k_g} \times (1-{exp}^{-k_g})


References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
