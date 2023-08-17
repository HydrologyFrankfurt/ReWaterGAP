Lakes and wetlands storage
==========================
Lakes and wetlands are important components of the hydrological cycle, and their storage and related fluxes are calculated based on section 4.6 of Müller Schmied et al 2021[1]_.  In this model, lakes and wetlands are categorized into two types: local and global. Local water bodies receive inflow only from the runoff generated within the grid cell, while global water bodies additionally receive streamflow from upstream grid cells. All local (global) wetlands within a 0.5◦ × 0.5◦ grid cell are simulated as one local (global) wetland that covers a specified fraction of the cell, and all local lakes within a grid cell are aggregated and simulated as one. It is important to note that the water balance of global lakes is computed at the outflow cell. 
The location, area, and other attributes of these water bodies are defined using the Global Lakes and Wetland Database (GLWD) (Lehner and Döll, 2004). Area fractions of local lakes and wetlands, except for global lake (which have absolute area), are obtained from this database (see appendix D in Müller Schmied et al 2021), and this information is then used for the computation of the maximum capacity of the surface water bodies.

.. autofunction:: lakes_and_wetlands.lake_wetland_balance

Water balance
-------------
Lakes and wetland storage  :math:`{S}_{l,w}` :math:`(m^3)` is computated as

.. math::
   \frac{dS_l,w}{d_t} =  {Q}_{in} + A(P  − {E}_{pot}) − {R_g}_{l,w}  − {NA}_{l}  − {Q}_{out}

where :math:`{Q}_{in}' is inflow into the lake or wetland from upstream (:math:`m^3 {d}^{-1}`), 
:math:`A' is global (or local) water body surface area (:math:`m^2`) in the grid cell at time step t,
:math:`P' is precipitation (:math:`m^3 {d}^{-1}`), :math:`{E}_{pot}' is :ref:`potential evapotranspiration <pot_evap>`  (:math:`m^3 {d}^{-1}`), 
:math:`{R_g}_{l,w}' is point source groundwater recharge from the water body (only in arid/semiarid regions) (:math:`m^3 {d}^{-1}`), :math:`NA_l` is net abstraction from lakes (:math:`m^3 {d}^{-1}`).


Inflows
-------

to be completed soon 


Outflows
--------
to be completed soon

References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
