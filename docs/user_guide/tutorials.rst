.. _tutorials:


############################
Tutorial (Under Development)
############################

.. contents:: 
    :depth: 4

.. note::
	Before following this tutorial, please follow the five minute guide found :ref:`here <five_minute_guide>`.


Running Water Gap with different simulation options (other model configurations)
================================================================================

Naturalized Run
***************

This simulation computes naturalized flows and storages that would occur if there were neither human water use nor global man-made reservoirs/regulated lakes.

To run Water Gap in a naturalized mode, see :ref:`here <naturalized_run>`.

Standard anthropogenic Run
**************************

The standard run in WaterGAP simulates the effects of both human water use and man-made reservoirs (including their commissioning years) on flows and storages.

The example below shows a step-by-step guide on how you can create a standard run for one year (1901).

1) Download the climate forcing data of your choice. In this example we will be using the forcing "gswp3-w5e5_obsclim" from `ISIMIP<https://data.isimip.org/search/tree/ISIMIP3a/InputData/climate/atmosphere/gswp3-w5e5/obsclim/query//>`_ . The forcings from ISIMIP are in groups of 10 years. We will be using the group of 1901 to 1910 in this example.
The forcings required are:
	- precipitation (kg m-2 s-1); `Link in ISIMIP<https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_pr_global_daily_1901_1910.nc>`_ ;
	- downward longwave radiation (Wm-2); `Link in ISIMIP<https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_rlds_global_daily_1901_1910.nc>`_ ;
	- downward shortwave radiation (Wm-2); `Link in ISIMIP<https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_rsds_global_daily_1901_1910.nc>`_ ;
	- temperature (K); `Link in ISIMIP<https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_tas_global_daily_1901_1910.nc>`_ ;

2) Download the water use data
The forcings required are:
	- potential consumptive use from irrigation using surface water (m3/month)
	- potential water withdrawal use from irrigation using surface water (m3/month)
	- potential net abstractions from surface water (m3/month)
	- potential net abstractions from groundwater (m3/month)
A download link will be made available at a later date. If you require the data, request a download link by sending us an <email>.

3) Place the downloaded files, as seen in the <5 minute guide (image)>, in the correct folders in <input_data>.

<picture>

4) Modify the configuration file required to run a standard run.
	- Go to Runtime Options in the confiog file. Then to Simulation Options. Set all options under "AntNat_opts" to "true", as shown <here picture from config>. Set all options under "Demand_satisfaction_opts" to "true". For more details see the <config file>

5) Under Restart Options in the configuration file, make sure erverything is "false" as seen here <>. WaterGap will not be restarted from a previous state in this run.
	
6) Under "SimulationPeriod" in the configuration file, change the "start" date to "1901-01-01" and the "end" date to "1901-12-31". For reservoir operational year set the start and end years to "1901". as shown <below picture>.
Note: We will be using no spin up years in this example. Usually we will be running the simulation for a peroid of 5 years, with an additional 5 year spin up.

<picture>

Time step daily
We are not running for basin so leave "false"
Output Variables we will be writing out are:
	- streamflow; set to "true" in config
This can also be done for any number of other variables of choice. For a detailed explanation on which variables can be written out see the <glossary>. In this example we will only be looking at streamflow.

Save config

Run the simulation 
	- copy terminal commands from 5 min guide

If successful it shbould look like this:
<picture terminal>
<picture panopoly>
	plot of river discharge + plot control for one day





.. _human_water_use_only:

Human Water Use only 
********************

This simulation includes human water use but excludes global man-made reservoirs/regulated lakes.

.. _reservoirs_only:

Reservoirs only
***************

This simulation excludes human water use but includes global man-made reservoirs/regulated lakes.

.. _restart_from_saved_state:

How to Restart WaterGap from saved state
========================================

Running WaterGAP with GWSWUSE (under development)
=================================================





