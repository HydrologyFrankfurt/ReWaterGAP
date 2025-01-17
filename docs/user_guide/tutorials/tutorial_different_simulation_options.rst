.. _tutorial_different_simulation_options:

################################################################################
Running Water Gap with different simulation options (other model configurations)
################################################################################

.. contents:: 
    :depth: 3
    :backlinks: entry

.. _naturalized_run:

Naturalized Run
###############

This simulation computes naturalized flows and storages that would occur if there were neither human water use nor global man-made reservoirs/regulated lakes.

To run Water Gap in a naturalized mode, find the tutorial in the :ref:`five minute guide here <naturalized_run>`.

.. _standard_anthropogenic_run:

Standard anthropogenic Run
##########################

The standard run in WaterGAP simulates the effects of both human water use and man-made reservoirs (including their commissioning years) on flows and storages.

In the example below, we will create a standard run for one year (1989) and go through the necessary steps, step-by-step.

**Prerequisites:** You will need to clone WaterGAP and create an environment to run it in. If you haven't done so already follow the :ref:`five minute guide <five_minute_guide>` for this.

.. _prepare_input_data:

1) Prepare the input data
***************************

Download all required climate forcing and water use data, remove all leap days, and place the data in the "input_data" folder in your ReWaterGAP repository as explained :ref:`above <prepare_input_data>`.

.. _modify_the_configuration_file_tutorial:

2) Set up the configuration file
*********************************

WaterGAP can be setup for your specific usecase. In the following we will be going through the various configuration options as well as the available output options and configuring the simulation for a standard anthropogenic run without restart. For a detailed description on the possible settings see our :ref:`guide to the configuration file <configuration_file>`.

To configure WaterGAP, go to your WaterGAP repository and navigate to "Config_ReWaterGAP.json" and open the configuration file. 

**2.1) File Paths**

The first options in the configuration file regard input and output file paths. In this example, we will leave them unmodified. The locations for input and output data can be seen in the picture below.

.. figure:: ../../images/user_guide/tutorial/input_directory_configuration_file.png

**2.2) Runtime Options**

In the configuration file find the runtime options. Then find the simulation options. Set all options under "AntNat_opts" to "true" and all options under "Demand_satisfaction_opts" to "true" to set up a standard anthropogenic run.

.. figure:: ../../images/user_guide/tutorial/runtime_options_standard_run.png

**2.3) Restart Options**

In this run, WaterGap will not restart from a previous state. Under "restart_options" make sure each option is set to "false".

.. figure:: ../../images/user_guide/tutorial/restart_options_no_restart.png

To find more information on restart options find a tutorial on how to save and restart WaterGAP :ref:`here <restart_from_saved_state>`.

**2.4) Simulation Period Options**

In this example we are running the simulation for the year 1989. Under "SimulationPeriod" change the "start" date to "1989-01-01" and the "end" date to "1989-12-31".
For the reservoir operational years set the start and end years to "1989". 

We will be using a five year spin-up period in this example. Set "spinup_years" to "5".

.. figure:: ../../images/user_guide/tutorial/simulation_period_options_tutorial.png

**2.5) Time step**

Under "time_step" set the resolution to "daily".

.. figure:: ../../images/user_guide/tutorial/time_step_daily.png

**2.6) Simulation Extend**

We will not be running WaterGAP for a basin in this example so set the "run_basin" option under "SimulationExtent" to "false".

**2.7) Output Variables**

Any number of variables may be written out. In this example, we will only write out the "streamflow" variable. Under "LateralWaterBalanceFluxes" find "streamflow" and set it to "true". Everything else should be set to "false". For a detailed explanation on which variables can be written out see the :ref:`glossary <glossary>`.

.. figure:: ../../images/user_guide/tutorial/output_variables_tutorial.png

**2.8) Save the configuration file**

Save the configuration file

3) Run the simulation
*********************

Navigate to your ReWaterGAP folder in the terminal, activate your environment, and run WaterGAP using the following command:

.. code-block:: bash

	$ python3 run_watergap.py Config_ReWaterGAP.json

In case of a problem find help in the :ref:`five minute guide <five_minute_guide>`.

If your run has been successful, your Terminal should look like this:

.. figure:: ../../images/user_guide/tutorial/standard_run_successful_terminal.png

In your WaterGAP repository under "output_data" you will find a file named "dis_1989-12-31.nc". 

4) Visualize your results
********************************

To visualize the output of any given simulation we suggest using `Panopoly <https://www.giss.nasa.gov/tools/panoply/>`_. Find our guide to Panopoly :ref:`here <visualize_using_panopoly>`.

For the year 1989-01-01 the result should look like this:

.. figure:: ../../images/user_guide/tutorial/panopoly_standard_run_tutorial.png

.. _human_water_use_only:

Human Water Use only 
####################

This simulation includes human water use but excludes global man-made reservoirs/regulated lakes. When creating a human-water-use-only run, the setup follows the standard run in all but one step. In the example below, we will create a human-water-use-only run for one year (1989) and go through the steps step-by-step.

**Prerequisites:** You will need to clone WaterGAP and create an environment to run it in. If you haven't done so, follow the :ref:`five minute guide <five_minute_guide>` for this.

1) Prepare the input data.
********************************

Download all required climate forcing and water use data, remove all leap days, and place the data in the "input_data" folder in your ReWaterGAP repository as explained :ref:`above <prepare_input_data>`.

2) Set up the configuration file
********************************

The only difference between a standard and a human-water-use-only run are the simulation options. In your configuration file, under "SimulationOption" find “AntNat_opts”. Set "ant" to "true," "subtract_use" to "true" and "res_opt" to "false" as seen in the picture :ref:`below <use_only_run_example_picture>`.

.. _use_only_run_example_picture:

.. figure:: ../../images/user_guide/tutorial/runtime_options_use_only_run.png

Set up File Paths, other Runtime Options, Restart Options, Simulation Period Options, Time step, Simulation Extend and Output Variables as described :ref:`above <modify_the_configuration_file_tutorial>` and save it.

3) Run the simulation
********************************

Navigate to your ReWaterGAP folder in the terminal, activate your environment, and run WaterGAP using the following command:

.. code-block:: bash

	$ python3 run_watergap.py Config_ReWaterGAP.json

In case of a problem find help in the :ref:`five minute guide <five_minute_guide>`.

In your WaterGAP repository under "output_data" you will find a file named "dis_1989-12-31.nc".  

4) Visualize your results
********************************

To visualize the output of any given simulation we suggest using `Panopoly <https://www.giss.nasa.gov/tools/panoply/>`_. Find our guide to Panopoly :ref:`here <visualize_using_panopoly>`.

For the year 1989-01-01 the result should look like this:

.. figure:: ../../images/user_guide/tutorial/panopoly_use_only_run_tutorial.png

.. _reservoirs_only:

Reservoirs only
###############

This simulation excludes human water use but includes global man-made reservoirs/regulated lakes. When creating a reservoirs-only run, the setup follows the standard run in all but one step. In the example below, we will create a reservoirs-only run for one year (1989) and go through the steps step-by-step.

**Prerequisites:** You will need to clone WaterGAP and create an environment to run it in. If you haven't done so, follow the :ref:`five minute guide <five_minute_guide>` for this.

1) Prepare the input data.
********************************

Download all required climate forcing and water use data, remove all leap days, and place the data in the "input_data" folder in your ReWaterGAP repository as explained :ref:`above <prepare_input_data>`.

2) Set up the configuration file
********************************

The only difference between a standard and a reservoirs-only run are the simulation options. In your configuration file, under "SimulationOption" find “AntNat_opts”. Set "ant" to "true," "subtract_use" to "false" and "res_opt" to "true" as seen in the picture :ref:`below <reservoirs_only_run_example_picture>`.

.. _reservoirs_only_run_example_picture:

.. figure:: ../../images/user_guide/tutorial/runtime_options_reservoirs_only_run.png

Set up File Paths, other Runtime Options, Restart Options, Simulation Period Options, Time step, Simulation Extend and Output Variables as described :ref:`above <modify_the_configuration_file_tutorial>` and save it.

3) Run the simulation
********************************

Navigate to your ReWaterGAP folder in the terminal, activate your environment, and run WaterGAP using the following command:

.. code-block:: bash

	$ python3 run_watergap.py Config_ReWaterGAP.json

In case of a problem find help in the :ref:`five minute guide <five_minute_guide>`.

In your WaterGAP repository under "output_data" you will find a file named "dis_1989-12-31.nc".  

4) Visualizing your results using Panopoly
************************************************

To visualize the output of any given simulation we suggest using `Panopoly <https://www.giss.nasa.gov/tools/panoply/>`_. Find our guide to Panopoly :ref:`here <visualize_using_panopoly>`.

For the year 1989-01-01 the result should look like this:

.. figure:: ../../images/user_guide/tutorial/panopoly_reservoirs_only_run_tutorial.png
