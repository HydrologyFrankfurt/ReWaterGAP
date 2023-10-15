Net abstractions 
===============
Computation of actual net abstractions from surface water and groundwater 
-------------------------------------------------------------------------
In WaterGAP, water usage across five sectors is simulated, differentiating between groundwater and surface water sources. The model assumes how much water is returned to either surface water or groundwater. Unlike other hydrological models, the impact of human water use on water storage and flow is calculated by subtracting net abstractions from either groundwater (groundwater use) or surface water bodies like lakes/reservoirs and rivers (surface water use). Priority is assigned to the water body type in ascending priority where global lakes/reservoirs are 1, rivers 2, and local lakes/reservations 3. 

Net abstractions are the difference between the water abstractions from a storage compartment (groundwater or surface water) and the water returned to that compartment [1]_. This concept is used to gauge the impact of human water use on water storage. Thus, the impact of irrigation on soil water storage is neglected in WaterGAP. 

Net abstractions :math:`({NA})` can be either positive or negative; the latter occurs if return flows to a storage compartment exceed abstractions from the compartment. 
Potential net abstraction from groundwater :math:`({NA}_{pot,g})` and potential net abstraction from surface water :math:`({NA}_{pot,s})`, which do not take into account water availability, are computed in GWSWUSE (Groundwater-Surface Water Use) and are input to WGHM (WaterGAP Global Hydrology Model). The sum of these potential net abstractions reflects the potential consumptive water use – the part of taken water that's evaporated or transpired during usage.


1 Computation of potential net abstractions from surface water and groundwater
------------------------------------------------------------------------------
Only three sectors are assumed to use groundwater, in addition to surface water, as their source: irrigation, domestic, and manufacturing. A fraction of the water returned from irrigation (whether from surface or groundwater) refills groundwater at a rate of :math:`{f}_{rgi}`, while the rest directly flows back to surface water bodies. For the other sectors, their return flows go directly to the surface water. Implementing these assumptions, the module GWSWUSE computes :math:`({NA}_{pot,g})` as the sum of the three sectors using groundwater minus the artificial groundwater recharge [1]_. Implementing these assumptions, the module GWSWUSE computes  

.. math::
   {NA}_{pot,g} = [{WA}_{pot,g,irri} + {WA}_{pot,g,dom} + {WA}_{pot,g,man}] - [{frgi}*({WA}_{pot,g,irri} - {CU}_{pot,g,irri} + {WA}_{pot,s,irri} - {CU}_{pot,s,irri})]


with WApot: potential water abstraction, in km3/month, CUpot: potential consumptive use, in km3/month, NA: net abstraction, in km3/month, frgi: fraction of return flow (WA-CU) from irrigation to groundwater, and g: groundwater, s: surface water, irri: irrigation, dom: domestic, man: manufacturing. The term that is subtracted at the right-hand side of Eq. (1), the return flow from irrigation with surface water or groundwater to groundwater, can be regarded as artificial groundwater recharge [1]_.

with:

- :math:`{WA}_{pot}`: potential water abstraction, in [km3/month], 
- :math:`{CU}_{pot}`: potential consumptive use, in [km3/month], 
- :math:`{NA}`: net abstraction, in [km3/month], 
- :math:`{f}_{rgi}`: fraction of return flow :math:`({WA}-{CU})` from irrigation to groundwater,

and the indices:

- *g*: groundwater, 
- *s*: surface water, 
- *irri*: irrigation, 
- *dom*: domestic, 
- *man*: manufacturing. 

.. note::
For computations in WaterGAP, net abstractions are converted from [km3/month] to [km3/day]


The subtracted artificial groundwater recharge is the returned flow from irrigation with surface water or groundwater to groundwater (Döll et al., 2012).


For water uses where the source of the water and the destination for the return flow are surface water bodies, only the consumptive use needs to be included in the computation of NApot,s. This applies to water use for cooling thermal power plants, livestock, as well as surface water use in the domestic and manufacturing sectors. 
Thus, NApot,s is computed as:

.. math::
   {NA}_{pot,s} = [{CU}_{pot,liv} + {CU}_{pot,thermal} + {CU}_{pot,s,dom} + {CU}_{pot,s,man} + {WA}_{pot,s,irri}] – [(1-{f}_{rgi})*({WA}_{pot,g,irri}-{CU}_{pot,g,irri}+{WA}_{pot,s,irri}-{CU}_{pot,s,irri}) + ({WA}_{pot,g,dom} -{CU}_{pot,g,dom} + {WA}_{pot,g,man} - {CU}_{pot,g,man})]

with: 
- _liv_: livestock,
- _thermal_: cooling of thermal power plants.

 
1 Actual net abstraction from surface water
-------------------------------------------
The demand for groundwater abstractions is always fulfilled in WaterGAP, assuming an unlimited groundwater volume, which differs from the demand for surface water abstractions. If the potential net abstraction from surface water (NApot,s), is positive, fulfilling the demand might not be possible due to water scarcity in the surface water bodies of the grid cell.
There are three options for managing this situation by spatially shifting parts of NApot,s to other grid cells.

1. With the 'riparian water supply' option, if the demanding cell is situated along a global lake or reservoir, NApot,s can be fulfilled from the storage of the lake or reservoir, if possible. In WaterGAP this is achieved by computing storages in the output cell.
2. Alternatively, with the 'neighboring cell water supply' option, any accumulated unsatisfied potential net abstraction from surface water can be satisfied from a neighboring cell with available supply.
3. Lastly, in the 'delayed water supply' option, surface water demands that couldn't be met on a given day are shifted to a later time in the year (Müller Schmied et al., 2021, p. 1050).


1.1	Riparian water supply option
----------------------------------
If the demand cell is a riparian cell of a global lake or reservoir, NAs is satisfied from the lake/reservoir storage if possible. For this purpose, the NApot,s values of all riparian cells are aggregated for each time step if they are positive and then assigned to the outflow cell, subtracting them from the lake/reservoir storage of the outflow cell.
Negative NApot,s (return flows) are used to increase the storage of the riparian cell itself. 

If satisfaction is impossible, the not-satisfied part from the outflow cell is proportionally redistributed to the riparian cells, right after calculating the global lake/reservoir storage. The proportional contribution of each riparian cell to the aggregated demand in the outflow cell is employed to distribute the unmet demand to the riparian cells. The unmet demand from a global lake outflow cell is attempted to be satisfied in riparian cells (local lakes or rivers) either on the same day or the next day, depending on the routing order.
The actual net abstraction from surface water in the global lake/reservoir outflow cells, resulting from NApot,s in riparian demand cells (net_abstraction_sw_for_riparian_cells), and the part of the potential net abstraction from surface water in the riparian demand cell that is supplied from the global lake/reservoir outflow cell (net_abstraction_sw_from_outflow_cell) can be written out.


1.2	Neighboring cell water supply option 
----------------------------------------
Unsatisﬁed surface water demand of all other cells can be taken from the neighboring cell with the largest river and lake/reservoir storage simulating the effect of water transfers. However, in each cell i, the first priority is to satisfy the water demand of cell i (from water storage in cell i), and only the second priority, is to satisfy water demand allocated from the neighboring cell(s) from water storage in cell i. 
If not all the unsatisfied demand of the demand cell can be fulfilled in the supply cell, the unsatisfied demand is assigned back to the demand cell. 
In both cases, the :math:`{NA}_{s}` of the demand cell is reduced as compared to :math:`{NA}_{pot,s}` and the :math:`{NA}_{s}` of the supply cell is increased. 
If unsatisfied :math:`{NA}_{s}` of the demand cell can be satisfied in the supply cell, then NAg in the demand cell remains constant, as the full return flow from irrigation with surface water occurs in the demand cell. 
In this case, the sum of :math:`{NA}_{g}` and :math:`{NA}_{s}` in each grid cell is no longer equal to the total actual consumptive water use in both the supply and the demand cells. The actual net abstraction from surface water in supply cell due to NApot,s in neighboring demand cells (net_abstraction_sw_for_neighbor_cells) and the part of potential net abstraction from surface water demand cell that is supplied from the supply cell (net_abstraction_sw_from_supply_cell) can be written out. In case of the delayed water supply option, it is first attempted to fulfill the delayed use in the cell before shifting it to the neighboring cell.


1.3	Delayed water supply option
-------------------------------
Temporal distribution, by allowing delayed satisfaction of daily surface water demands, aims to compensate that WaterGAP likely underestimates demand satisfaction due to the generic reservoir algorithm and an underestimation of the storage of water, e.g., by small tanks and dams [2]_. If even after the spatial distribution of unsatisfied :math:`{NA}_{s}`, there is still unsatisfied :math:`{NA}_{s}`, it is possible to satisfy it until the end of the calendar year. Unsatisfied :math:`{NA}_{s}` of the grid cell is registered by adding it to the variable “accumulated unsatisfied potential net abstraction from surface water” AccUnNApot,s (at the end of each time step). At the beginning of the next time step, it  is added to the NApot,s of that day, and it is attempted to satisfy AccUnNApot,s by subtracting it from the surface water storages, either increasing or decreasing AccUnNApot,s. 
The daily unsatisfied net abstraction from surface water UnNApot,s of a grid cell is computed as AccUnNApot,s(t) minus AccUnNApot,s(t-1) at the end of each time step. If it is positive, then less water than demanded can be taken from the surface water on this day. If it is zero, :math:`{NA}_{s}` = :math:`{NA}_{pot,s}`. If it is negative, more surface water is net abstracted on this day than demanded. If for the previous time step, :math:`{NA}_{s}` is not equal to :math:`{NA}_{pot,s}` and if there is withdrawal from the surface for irrigation, :math:`{NA}_{g}`  is adapted to account for the change in return flows from the surface water.


2 Actual net abstraction from groundwater
-----------------------------------------
In the computation of :math:`{NA}_{pot,g}` in GWSWUSE, it is assumed that the total demand for irrigation by surface water can be fulfilled by the water available in surface water bodies including the river. As net abstractions from groundwater are a function of the return flows of irrigation with surface water (return flows of all other sectors are assumed to only flow to surface water bodies [1]_, the potential net abstraction from groundwater NApot,g needs to be adapted if, for each cell and time step, the actual net abstraction from surface water for irrigation is smaller than what was assumed when computing NApot,s of a day (i.e., not all demand for net abstractions from surface water can be fulfilled even after spatial redistribution) or if, due to the delayed water use option, more surface water is abstracted for irrigation than demanded on this day (so whenever net abstraction from surface water on a specific day differs from the potential one computed in GWSWUSE). It is assumed in WGHM that irrigation water abstraction is reduced as a priority, and fulfilled only after non-irrigation demands are fulfilled. Actual net abstraction from groundwater NAg is computed in each time step based on NApot,g(t) and UnNApot,s(t-1), using the equations to compute NApot,g and NApot,s as described in Döll et al. (2012)[1]_.


UnNApot,s(t-1) is positive and WApot,s,irri(t) >0
In this case, the surface water abstraction for irrigation on the previous day was lower than that assumed when computing NApot,g. Thus, return flows to groundwater are decreased and NAg becomes larger than NApot,g. We derive the algorithm by setting, as a first step, all water uses that are not related to surface water use for irrigation to zero, as they are not affected by the reduction of net abstraction from surface water as compared to NApot,s. The equations in italics show the derivation, the normal letters what is included in the code. Then, Eq. (2) is simplified to

.. math::

   {NA}_{pot,s} = WApot,s,irri- (1-frgi)(WApot,s,irri-CUpot,s,irri)
   {eff}= CUpot,s,irri/WApot,s,irri
   NApot,s = WApot,s,irri- (1-frgi)(WApot,s,irri-eff WApot,s,irri)
   NApot,s = WApot,s,irri- (1-frgi)(1-eff) WApot,s,irri
   NApot,s = WApot,s,irri [1-(1-frgi)(1-eff)]
   factor = [1-(1-frgi)(1-eff)]
   NApot,s = factor WApot,s,irri
   NAs = NApot,s - UnNApot,s
   factor WAs,irri = factor WApot,s,irri - UnNApot,s
   WAs,irri = (1/factor) (factor WApot,s,irri - UnNApot,s)

Neglecting all water uses except surface water use for irrigation, Eq. 1 is simplified to

.. math::
   {NA}_{pot,g} = -{f}_{rgi}*({1}-{eff})*{WA}_{pot,s,irri}

Then, the change in return flow to groundwater due to changing from WApot,s,irri to Ws,irr is computed as

.. math::
   return_flow_change = {f}_{rgi}*({1}-{eff})({WA}_{s,irri}-{WA}_{pot,s,irri}) //(negative)
   NAg(t) = NApot,g(t) – return flow change(t-1) (output)





UnNApot,s(t-1) is positive and WApot,s,irri(t) = 0
Then, NAg is not adjusted as without irrigation, there is never any return flow to groundwater. The daily unsatisfied net abstraction from surface water is added to the accumulated unsatisfied NAs from other sectors as
G_acc_unsat_net_abstraction_other_sectors += UnNApot,s 
and return NAg = NApot,g

UnNApot,s(t-1) is negative and WApot,s,irri(t) >0
In this case, the actual NAs subtracted from surface water storage was larger than NApot,s on the previous day, as part of the unsatisfied NApot,s accumulated from earlier time could by satisfied. If this additional NAs was caused by supplying irrigation water and not only for satisfying the water demand of other sectors (which have priority), then more return flow to groundwater is generated than it was assumed when NApot,g was computed in GWSWUSE. Thus, return flows to groundwater are increased and NAg becomes smaller than NApot,g
NAs = NApot,s + added_net_abstraction_sw_irri
factor WAs,irri = factor WApot,s,irri + add_net_abstraction_sw_irri
WAs,irri = (1/factor) (factor WApot,s,irri + add_net_abstraction_sw_irri)
return_flow_change = frgi(1-eff)(WAs,irri-WApot,s,irri) //(positive)
NAg(t) = NApot,g(t) – return flow change(t-1) (output)


UnNApot,s(t-1) is negative and WApot,s,irri(t) = 0
See  case (UnNApot,s(t-1) is positive and WApot,s,irri(t) = 0)

References 
----------
.. [1] P. Döll, H. Hoffmann-Dobrev, F.T. Portmann, S. Siebert, A. Eicker, M. Rodell, G. Strassberg, B.R. Scanlon, Impact of water withdrawals from groundwater and surface water on continental water storage variations, Journal of Geodynamics. https://doi.org/10.1016/j.jog.2011.05.001
.. [2] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
