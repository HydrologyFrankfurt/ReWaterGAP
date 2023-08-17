.. _radiation_evap:

Radiation and Evapotranspiration
++++++++++++++++++++++++++++++++
This module contains a class and related method, which computes radiation components based on section 4.2.3 of Müller Schmied et al., 2016b [1]_
(computed within Pythons __init__ method) 
and Priestley-Taylor potential evapotranspiration based on H. Müller Schmied et al. 2021 [2]_.

.. autoclass:: radiation_evapotranspiration.RadiationPotentialEvap
    :members:
    :special-members: __init__

.. _evaporation: 

Canopy evaporation
===================
Canopy evaporation :math:`E_c` following Deardorff (1978) [3]_, is calculated as

.. math::
   E_c = {E}_{pot}\Big(\frac{S_c}{{S_c}_{,max}}\Big)^\frac{2}{3}

where :math:`{S_c}` :math:`[mm]` is the canopy storage, calculated in canopy storage under :ref:`Outflows <canopy_outflows>` and :math:`{S_c}_{,max}` :math:`[mm]` is the maximum canopy storage. :math:`{E}_{pot}` :math:`[mm/d]` is the potential evapotranspiration calculated with the **Priestley–Taylor** equation according to Shuttleworth (1993) [4]_, as:

.. _pot_evap:

.. math::
   {E}_{pot} = \alpha\Big(\frac{S_a R}{S_a + g}\Big)

:math:`\alpha` is set to 1.26 in humid and to 1.74 in (semi)arid cells (see Appendix B in Müller et al. [2]_). :math:`R` is the net radiation :math:`[mm/d]` that depends on land cover (Table C2, Müller et al. [2]_). :math:`{S_a}` is the slope of the saturation vapor pressure–temperature relationship, and :math:`g` is the psychrometric constant :math:`[{\frac{kPa}{°C}}]`.

Notes
-----
All grid cells with an aridity index AI < 0.75 are defined as semiarid/arid grid cells. Furthermore, all grid cells north of 55° N are defined as humid grid cells.
For further information on this see Müller et al. [3] Appendix B.

Net radiation
--------------
The calculation of net radiation, is based on Müller Schmied et al., 2016b [1]_. 
S↓ and L↓ describe the shortwave downward radiation and longwave downward radiation and are provided by meteorological forcings and have the unit :math:`[Wm^-2]`.

Net shortwave radiation :math:`{S}_{net}` :math:`[Wm^-2]` is calculated as:

.. math:: 
    {S}_{net} = S↓ (1 − {\alpha}_{LC}),

where :math:`{\alpha}_{LC}` is the albedo :math:`[-]` based on land cover type [Müller, Schmied et al. Table C2 [2]_]. 
Albedo values for WaterGAP are taken from assumptions of the IMAGE model [5]_. 
In the case of a reasonable snow cover, the albedo value is varying dynamically in WaterGAP to represent the influence of snow cover dynamics on radiation balance [2]_.

Upward shortwave radiation :math:`S↑ [Wm−2]`is calculated as:

.. math::
    S↑ = S↓ − {S}_{net}

Upward longwave radiation :math:`L↑` :math:`[Wm^-2]` is calculated as:

.. math::
    L↑ = {ε}_{LC}σT^4,

where :math:`{ε}_{LC}` is the emissivity :math:`[-]` based on land cover type Table C2) [2]_, :math:`σ` is the Stefan–Boltzmann constant :math:`(5.67 × 10−8 [Wm^-2·K^−4])` and :math:`T` is the temperature in :math:`[K]` . 

Net longwave radiation :math:`{L}_{net}` :math:`[\frac{W}{m^-2}]` is calculated as:

.. math::
    {L}_{net} = L↓ − L↑.

Net radiation :math:`R` :math:`[\frac{W}{m^-2}]` is calculated as:

.. math::
   R = {S}_{net} + {L}_{net}


Slope of the saturation and psychrometric constant
---------------------------------------------------
:math:`s_a` is the slope of the saturation vapor pressure–temperature relationship :math:`[\frac{kPa}{°C}]` defined as:

.. math::
   s_a = \frac{4098 (0.6108 e^\frac{17.27T}{T + 237.3})}{(T + 237.3)^2}

where :math:`T` :math:`[°C]` is the daily air temperature.

The the psychrometric constant :math:`g` :math:`[{\frac{kPa}{°C}}]` is defined as:

.. math::
   g = \frac{0.0016286 p_a}{l_h}

where :math:`p_a`  is atmospheric pressure of the standard atmosphere :math:`(101.3 kPa)`, and :math:`l_h` is latent heat :math:`[{\frac{MJ}{kg}}]`. Latent heat is
calculated as:

.. math::
    :nowrap:

    \[
    l_h= 
    \begin{cases}
    2.501 - 0.002361 T, & \text{if } T > 0 \\
    2.501 + 0.334, & \text{otherwise}
    \end{cases}
    \]


Reference
=========
.. [1] Müller Schmied, H., Müller, R., Sanchez-Lorenzo, A., Ahrens, B., and Wild, M.: Evaluation of radiation components in a global freshwater model with station-based observations, Water, 8, 450, https://doi.org/10.3390/w8100450, 2016b

.. [2] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021

.. [3] Deardorff, J. W.: Efficient prediction of ground surface temperature and moisture, with inclusion of a layer of vegetation, J. Geophys. Res., 83, 1889, https://doi.org/10.1029/JC083iC04p01889, 1978

.. [4] Shuttleworth, W.: Evaporation, in: Handbook of Hydrology, edited by: Maidment, D., McGraw-Hill, New York, 1–4, 1993

.. [5] Alcamo, J.; Leemans, R.; Kreileman, E. Global Change Scenarios of the 21st Century—Results from the IMAGE 2.1 Model; Pergamon: Oxford, UK, 1998.
