.. _lakes_wetlands:

Lakes and wetlands
==================
Lakes and wetlands storages and related fluxes are calculated based on section 4.6 of Müller Schmied et al 2021 [1]_.  In WaterGAP, lakes and wetlands are categorized into two types: local and global. Local water bodies receive inflow only from the runoff generated within the grid cell, while global water bodies additionally receive streamflow from upstream grid cells. All local (global) wetlands within a :math:`0.5° \times 0.5°` grid cell are simulated as one local (global) wetland that covers a specified fraction of the cell, and all local lakes within a grid cell are aggregated and simulated as one. It is important to note that the water balance of global lakes is computed at the outflow cell. 
The location, area, and other attributes of these water bodies are defined using the Global Lakes and Wetland Database (GLWD) (Lehner and Döll, 2004). Area fractions of local lakes and wetlands, except for global lake (which have absolute area), are obtained from this database (see appendix D in Müller Schmied et al 2021), and this information is then used for the computation of the maximum capacity of the surface water bodies.

.. note::
   Each grid cell can have a maximum of one local wetland, one global wetland, one local lake, and one global lake compartment. The lateral water flow within the cell follows 
   the sequence shown in the :ref:`watergap schematic diagram <watergap_scheme>`. For example, if there is a local lake compartment in a grid cell, it receives a fraction of 
   the outflow from the groundwater compartment (under a humid climate) and of the fast surface and subsurface outflow. The outflow from the local lake becomes inflow to the 
   local wetland if it exists, otherwise to the global lake

.. autofunction:: lakes_wetlands.lake_wetland_balance

Water balance
-------------
Lakes and wetland storage :math:`{S}_{l,w}` :math:`[m^3]` is computed as

.. math::
   \frac{dS_l,w}{d_t} =  {Q}_{in} + A(P  − {E}_{pot}) − {R_g}_{l,w}  − {NA}_{l}  − {Q}_{out}

where :math:`{Q}_{in}` is inflow into the lake or wetland from upstream :math:`[m^3 {d}^{-1}]`, 
:math:`A` is a global (or local) water body surface area :math:`[m^2]` in the grid cell at time step :math:`t`,
:math:`P` is precipitation :math:`[m^3 {d}^{-1}]`, :math:`{E}_{pot}` is :ref:`potential evapotranspiration <pot_evap>` :math:`[m^3 {d}^{-1}]`, :math:`{R_g}_{l,w}` is point source groundwater recharge from the water body (only in arid/semiarid regions) :math:`[m^3 {d}^{-1}]`, :math:`{NA}_{l}` is net abstraction from lakes :math:`[m^3 {d}^{-1}]` 
and :math:`{Q}_{out}` is the outflow from the water body to other surface water bodies including river storage :math:`[m^3 {d}^{-1}]`. 

The area of these surface water bodies (except global lakes) varies temporally and is computed as: 

.. math::
   A = r \times {A}_{max}

where :math:`r` is the reduction factor :math:`[–]`, and :math:`{A}_{max}` is the maximum extent
of the water body :math:`[m^2]` and is computed as the :math:`{A}_{grid} \times {A}_{fraction,l}`.
:math:`{A}_{grid}` is the area of :math: `0.5° \times 0.5°` grid cell and :math:`{A}_{fraction,l}` is the area fraction of the surface waterbody :math:`[m^2]`.


The reduction factor is applied differently for local and global lakes. 
In the case of local lakes, the reduction factor is used to reduce the lake area, while for global lakes, it is only used for reducing evaporation since the global lake area is assumed not to be dynamic. This would prevent the continuous decline of global lake levels in some cases such as (semi)arid regions.
The reduction factor is computed for local and global lakes as:

.. _lake_red:

.. math::
   r = 1- \left(\frac{|S_l - Sl,max|}{2({S}_{l,max})}\right)^p,  0 <= r <=1


where :math:`S_l` is the volume of the water :math:`[m^3]` stored in the lake at time step t :math:`days`, :math:`{S}_{l,max}` is the maximum storage of the lake :math:`[m^3]`. 
:math:`{S}_{l,max}` is computed based on :math:`{A}_{max}` and a maximum storage depth of 5 m, and p is the reduction exponent :math:`[–]`, set to 3.32 [1]_. 

**Note:** According to the  :ref:`lake reduction factor equation <lake_red>`, the area is reduced by :math:`1 \%` if :math:`S_l = 50 \% \times {S}_{l,max}`, 
by :math:`10 \%` if :math:`S_l = 0` and by :math:`100 \%` if :math:`S_l=-{S}_{l,max}`.

In the case of local and global wetlands, the reduction factor is used to reduce the area. It is computed as:

.. _wetland_red:

.. math::
   r = 1- \left(\frac{|S_w - Sw,max|}{{S}_{w,max}}\right)^p,  0 <= r <=1


where :math:`S_w` is the volume of the water :math:`m^3` stored in the wetlands at time step t :math:`days`, :math:`{S}_{w,max}` is the maximum storage of the wetland :math:`m^3`.  Reduction exponent p sis also et to 3.32 [1]_. 

.. note: 
   Also by the  :ref:`wetland reduction factor equation <wetland_red>`, the area is reduced by :math:`10 \%` if :math:`S_w = 50 \% \times {S}_{w,max}`, 
by :math:`70 \%` if :math:`S_w = 10 \% \times {S}_{w,max}`.


Inflows
-------
Computation of inflow :math:`{Q}_{in}` differs for local and global water bodies. 
For local lakes and wetlands, inflow comes only from local runoff within the same grid cell. 
A fraction  :math:`fswb` (see fractional routing) of the fast surface and subsurface runoff, as well as discharge from groundwater in humid grid cells, is directed to these local water bodies (see :ref:`watergap schematic diagram <watergap_scheme>`). If a grid cell contains both a local lake and a wetland, the outflow from the lake becomes the inflow to the wetland.
On the other hand, global lakes and wetlands receive inflow from both local runoff and river inflow from upstream grid cells. 


Outflows
--------
to be completed soon

References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
