.. _getting_started:

===============
Getting started
===============

Introduction
------------

WaterGAP is a state-of-the-art global-scale water resource and water-use simulation model. 
WaterGAP was used to support the sustainable development of the Earth system by assessing water scarcity for humans, drought hazards, ecologically-relevant streamflow characteristics, the impacts of human water use and dam construction as well as freshwater-related scenarios of the future [1]_. 
Recent focus has been on quantifying the impact of climate change on the global freshwater system, including the streamflow regime, groundwater recharge, floods, and droughts. 
WaterGAP is an open-source software with the aim of increasing reproducibility among researchers.


WaterGAP has been generally categorized into two sections: 

#. **WaterGAP framework** which consists of:
  
   * *WaterGAPUse* which includes the five sectoral water use models. 
   
   * *WaterGapCore* which includes the linking model Groundwater-Surface Water Use (GWSWUSE) and the WaterGAP Global Hydrology Model (WGHM).

#. **WaterGAPTools** consisting of *pre-processing* (input-generation) and *standard calibration* (against mean annual streamflow).

.. figure:: ../images/overview_watergap_components.png
   :align: center
   
   *WaterGAP Components*


5 minute guide to WaterGAP
--------------------------

1. Cloning the Repository
    1. How to do it
2. Preparing Input Files
    1. Run with default input
    2. Run with user input
3. User Configuration
    1. How to configure a naturalized run 


References 
----------
.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
