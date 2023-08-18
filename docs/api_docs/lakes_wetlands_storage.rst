Lakes and wetlands storage
==========================
Lakes and wetlands storages and related fluxes are calculated based on section 4.6 of Müller Schmied et al 2021 [1]_.  In WaterGAP, lakes and wetlands are categorized into two types: local and global. Local water bodies receive inflow only from the runoff generated within the grid cell, while global water bodies additionally receive streamflow from upstream grid cells. All local (global) wetlands within a 0.5◦ × 0.5◦ grid cell are simulated as one local (global) wetland that covers a specified fraction of the cell, and all local lakes within a grid cell are aggregated and simulated as one. It is important to note that the water balance of global lakes is computed at the outflow cell. 
The location, area, and other attributes of these water bodies are defined using the Global Lakes and Wetland Database (GLWD) (Lehner and Döll, 2004). Area fractions of local lakes and wetlands, except for global lake (which have absolute area), are obtained from this database (see appendix D in Müller Schmied et al 2021), and this information is then used for the computation of the maximum capacity of the surface water bodies.

.. note::
   Each grid cell can have a maximum of one local wetland, one global wetland, one local lake, and one global lake compartment. The lateral water flow within the cell follows 
   the sequence shown in the :ref:`watergap schematic diagram <watergap_scheme>`, . For example, if there is a local lake compartment in a grid cell, it receives a fraction of 
   the outflow from the groundwater compartment (under a humid climate) and of the fast surface and subsurface outflow . The outflow from the local lake becomes inflow to the 
   local wetland if it exists, otherwise to the global lake

.. autofunction:: lakes_and_wetlands.lake_wetland_balance

Water balance
-------------
Lakes and wetland storage  :math:`{S}_{l,w}` :math:`(m^3)` is computated as

.. math::
   \frac{dS_l,w}{d_t} =  {Q}_{in} + A(P  − {E}_{pot}) − {R_g}_{l,w}  − {NA}_{l}  − {Q}_{out}

where :math:`{Q}_{in}` is inflow into the lake or wetland from upstream :math:`(m^3 {d}^{-1})`, 
:math:`A` is global (or local) water body surface area :math:`(m^2)` in the grid cell at time step t,
:math:`P` is precipitation :math:`(m^3 {d}^{-1})`, :math:`{E}_{pot}` is :ref:`potential evapotranspiration <pot_evap>` :math:`(m^3 {d}^{-1})`, :math:`{R_g}_{l,w}` is point source groundwater recharge from the water body (only in arid/semiarid regions) :math:`(m^3 {d}^{-1})`, :math:`NA_l` is net abstraction from lakes :math:`(m^3 {d}^{-1})` 
and :math:`{Q}_{out}` is outflow from the water body to other surface water bodies including river storage :math:`(m^3 {d}^{-1})`. 

The area of these surface water bodies (except global lake) varies temporally and it computed as 

.. math::
   A = r \times {A}_{max}

where :math:`r` is reduction factor (–), and :math:`{A}_{max}`  is maximum extent
of the water body :math:`m^2}` computed as the *(area of 0.5 \times 0.5 grid cell) \times area fraction of surface waterbody)*.

Reduction factor is computed for in the case of local lakes  as:

.. math::
   r = 1- \frac{|S_l - S_l,max|}{2(Sl,max)} , 0 <= r <=1


.. note::
   Water balance equation is solved analytically for (global) lake and wetland per timestep of 1 day
   but numerically for (local) lake and wetlands. 


Inflows
-------
Computation of inflow (Qin), differs for local and global water bodies. 
For local lakes and wetlands, inflow comes only from local runoff within the same grid cell. 
A fraction  *fswb* (see farctional routing) of the fast surface and subsurface runoff, as well as discharge from groundwater in humid grid cells, is directed to these local water bodies (see :ref:`watergap schematic diagram <watergap_scheme>`). If a grid cell contains both a local lake and wetland, the outflow from the lake becomes the inflow to the wetland.
On the other hand, global lakes and wetlands receive inflow from both local runoff and river inflow from upstream grid cells. 


Outflows
--------
to be completed soon

References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
