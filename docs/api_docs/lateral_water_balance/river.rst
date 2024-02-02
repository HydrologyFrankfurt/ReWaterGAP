.. _river:

=============
River Storage
=============

River storage and related fluxes are calculated based on section 4.7 of Müller Schmied et al 2021 [1]_.

.. autofunction:: river.river_water_balance

Water balance
-------------
River storage :math:`S_r` :math:`(m^3)` is computated as

.. _river_balance:

.. math::
   \frac{dS_r}{d_t} =  {Q}_{r,in} − {Q}_{r,out} − {NA}_{s,r}

where :math:`{Q}_{r,in}` is inflow into the river compartment (:math:`{m}^{3} {d}^{-1}`), :math:`{Q}_{r,out}` is the streamflow (:math:`{m}^{3} {d}^{-1}`), and :math:`{NA}_{s,r}` is the net abstraction of surface water from the river (:math:`{m}^{3} {d}^{-1}`).


Inflows **(Come back later)
-------

If there are no surface water bodies in a grid cell, :math:`{Q}_{r,in}` is the sum of :math:`{R}_{s}`, :math:`{Q}_{g}` and streamflow from existing upstream cell(s). Otherwise, part of :math:`{R}_{s}`, and in the case of humid cells also part of :math:`{Q}_{g}`, is routed through the surface water bodies (Reference Schematic). The outflow from the surface water body preceding the river compartment then becomes part of :math:`{Q}_{r,in}`. In addition, negative :math:`{NA}_{s}` values due to high return flows from irrigation with groundwater lead to a net increase in storage. Thus, if no surface water bodies exist in the cell, negative NAs is added to :math:`{Q}_{r,in}` (reference figure 2).

Outflows
--------

.. autofunction:: river.river_velocity


References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
