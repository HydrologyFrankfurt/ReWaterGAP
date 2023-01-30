Snow Storage 
++++++++++++
.. note::
	Simulation of the snow dynamics is calculated such that each :math:`0.5° × 0.5°` grid cell is subdivided into 100 non localized subgrids that are assigned different land surface elevations according to GTOPO30 (U.S. Geological Survey, 1996) [1]_. The daily temperature of  each subgrid is calculated from daily temperature at the 0.5◦ × 0.5◦ cell by applying an adiabatic lapse rate of 0.6 :math:`°C/100m` [2]_. The daily snow water balance is computed for each of the subcells such that within a 0.5◦ × 0.5◦ cell there may be subcells with and without snow cover or snowfall [3]_. Subgrid values are then aggregated to 0.5◦ × 0.5◦ cell values. See section 4.3  of Müller Schmied et al 2021 [3]_.

Snow Storage  consists of two modules.

.. _numba:

1.  Numba optimized snow water content 
======================================
This module is also made up of two functions.

*A.* numba_snow which computes snow water content for the the 100 subgrid of 0.5 grid in series 

.. autofunction:: numba_snow_water_content.numba_snow

  
*B.* run_snow_parallel which parallelizes the computation for each 0.5 grid in parallel. 
   Input data of dimensions 360x720 is divided into *N* chunks for parallel computations (Default is 20 chunks). 

.. autofunction:: numba_snow_water_content.run_snow_parallel


2.  Snow water equivalent 
==========================
This module calls the :ref:`numba optimized module <numba>` using the *cal_snow* method to compute snow water storage.

.. autoclass:: snow_water_equivalent.Snow
    :members:



Water balance
=============
Snow storage :math:`S_sn` :math:`(mm)` is calculated as:

.. math::
   \frac{dS_sn}{d_t} =  {P}_{sn} − M − {E}_{sn}

where :math:`{P}_{sn}` is the part of :ref:`throughfall <canopy_outflows>` :math:`(P_t)` that falls as snow :math:`(mm/d)`, :math:`M` is snowmelt :math:`(mm/d)` and :math:`{E}_{sn}` is  sublimation :math:`(mm/d)`.

.. note::
   Snow storage is also corrected with land area fraction.


Inflows
=======
Snow fall from throughfall :math:`{P}_{sn}` is  is calculated as

.. math::
	:nowrap:

	\[
	{P}_{sn}= 
	\begin{cases}
	P_t, & \text{if }  T < T_f \\
	0, & \text{otherwise}
	\end{cases}
	\]

where :math:`T` is daily air temperature :math:`(°C)`, and :math:`T_f` is snow freeze temperature, set to :math:`0 °C` . In order to prevent excessive snow
accumulation, when snow storage :math:`{S}_{sn}` reaches :math:`1000 mm` in a subcell, the temperature in this subcell is increased to the temperature in the highest subcell with a temperature above :math:`T_f` [2]_.

Outflows
========
Snow melt :math:`M`  is calculated with a land-cover-specific degreeday factor :math:`D_F (mmd^−1 °C^-1)` (Table C2) [3]_ when the temperature :math:`T` in a subgrid surpasses melting temperature :math:`T_m = 0 (◦C)` as

.. math::
	:nowrap:

	\[
	M= 
	\begin{cases}
	D_F(T-T_m), & \text{if }  T > T_m, {S}_{sn} > 0\\
	0, & \text{otherwise}
	\end{cases}
	\]

Sublimation :math:`{E}_{sn}` is calculated as the fraction of :math:`{E}_{pot}` that remains available after :math:`E_c`. For calculating :math:`{E}_{pot}` , land-cover-specific albedo values are used if :math:`{S}_{sn}` surpasses :math:`3 mm` in the 0.5◦ × 0.5◦ cell (Table C2) [3]_. See potential evapotranspiration under :ref:`Canopy evaporation <evaporation>`.

.. math::
	:nowrap:

	\[
	{E}_{sn}= 
	\begin{cases}
	{E}_{pot} - E_c, & \text{if } ({E}_{pot} - E_c) > {S}_{sn} \\
	{S}_{sn}, & \text{otherwise}
	\end{cases}
	\]






References 
==========

.. [1] U.S. Geological Survey: USGS EROS archive – digital elevation– global 30 arc-second elevation (GTOPO30), available at: https://www.usgs.gov/centers/eros/science/usgs-eros-archivedigital-elevation-global-30-arc-second-elevation-gtopo30?qtscience_center_objects=0#qt-science_center_objects (last access: 25 MArch 2020), 1996

.. [2] Schulze, K. and Döll, P.: Neue Ansätze zur Modellierung von Schneeakkumulation und -schmelze im globalen Wassermodell WaterGAP, in: Tagungsband zum 7. Workshop zur großskaligen Modellierung in der Hydrologie, edited by: Ludwig, R., Reichert, D., and Mauser, W., November 2003, 145–154, Kassel University Press, Kassel, 2004

.. [3] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
