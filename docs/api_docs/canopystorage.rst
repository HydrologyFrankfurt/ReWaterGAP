Canopy Storage 
===============
Canopy storage and related fluxes are calculated based on Müller Schmied et al 2021 [1]_.

.. autofunction:: canopy_storage_module.daily_canopy_storage

Water balance
-------------
The canopy storage :math:`S_c` :math:`(mm)` is calculated as:

.. math::
   \frac{dS_c}{d_t} =  P − P_t − E_c

where :math:`P` is precipitation :math:`(mm/d)` , :math:`P_t` is throughfall, the fraction of :math:`P` that reaches the soil :math:`(mm/d)` and :math:`E_c` is evaporation from the canopy :math:`(mm/d)`.

.. note::
   Canopy storage is also a function of land area fraction. 

Inflows
-------
Daily precipitation :math:`P` is read in from the selected climate
forcing (see :ref:`Climate Forcing <forcings>` in Data section).

.. _canopy_outflows:

Outflows
--------
Throughfall :math:`P_t` is calculated as

.. math::
	:nowrap:

	\[
	P_t= 
	\begin{cases}
	0, & \text{if } P<({S_c}_{,max}- S_c) \\
	P - ({S_c}_{,max} - S_c), & \text{otherwise}
	\end{cases}
	\]

where :math:`{S_c}_{,max}` is maximum canopy storage calculated as

.. math::
    {S_c}_{,max} = m_c · L 

where :math:`m_c` is `0.3 mm` [2]_, and :math:`L (-)` is the oneside leaf area index. :math:`L` is a function of daily temperature and
precipitation and limited to minimum or maximum values. Maximum :math:`L` values per land cover class (Table C1) [1]_,
whereas minimum :math:`L` values are calculated as

.. math::
   {L}_{min} = 0.1{f_d}_{,lc} + (1 − {f_d}_{,lc}){c_e}_{,lc}{L}_{max}

where :math:`{f_d}_{,lc}` is the fraction of deciduous plants and :math:`{c_e}_{,lc}` is
the reduction factor for evergreen plants per land cover type (Table C1) [1]_. See :ref:`Lead Area Index <leafareaindex>` section under API reference for leaf Area index calculation. 

See :ref:`Radiation and Evapotranspiration <radiation_evap>` section under API reference for radiation and evaporation calculation. 

References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021

.. [2] Deardorff, J. W.: Efficient prediction of ground surface temperature and moisture, with inclusion of a layer of vegetation, J. Geophys. Res., 83, 1889, https://doi.org/10.1029/JC083iC04p01889, 1978


