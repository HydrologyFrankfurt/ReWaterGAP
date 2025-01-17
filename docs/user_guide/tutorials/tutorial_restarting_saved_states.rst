.. _tutorialstutorial_restarting_saved_states:

How to Restart WaterGap from saved state
########################################

To run Watergap from a saved state, you must first save data from a previous simulation. In this tutorial, we will be looking at the previous example, where we ran the simulation for a :ref:`standard anthropogenic run <standard_anthropogenic_run>` for the year 1989, create a saved state, and then restart the simulation from this data to continue running for 1990.

.. _creating_a_saved_state:

Creating a saved state
######################

Restarting the simulation works for any of the simulation options (:ref:`Standard Run <standard_anthropogenic_run>`, :ref:`Naturalized Run <naturalized_run>`, :ref:`Human Water Use <human_water_use_only>` and :ref:`Reservoirs only <reservoirs_only>`). In this example, we will be creating a saved state for a :ref:`standard anthropogenic run <standard_anthropogenic_run>`.

Before running the simulation we have to modify the configuration file. In your WaterGAP repository, navigate to "**Config_ReWaterGAP.json**". Under "**RestartOptions**", set "**restart**" to "false" and "**save_model_states_for_restart**" to "true", as this is the run we will be creating the saved state from. On your computer create a folder to save the saved state data in. In this example, we will be using a folder under "Users/username/restart_data". In your configuration file, set "**save_and_read_states_dir**" to the created directory, as shown in the `image below <saving_for_restart>`_ .

.. _saving_for_restart:

.. figure:: ../images/user_guide/tutorial/restart_options_saving.png

Then set your "**SimulationPeriod**" to the preferred year (In this example 1989) and the "**spinup_years**" to 5.

.. figure:: ../images/user_guide/tutorial/restart_options_simulation_period_before.png

All other options and steps to run the simulation will remain as they are described under `standard anthropogenic run <standard_anthropogenic_run>`_.

.. figure:: ../images/user_guide/tutorial/output_variables_tutorial.png

Run the simulation. You will then find your saved state data file "restartwatergap_1989-12-31.pickle" in your saved state directory (in this example under "Users/username/restart_data").

.. figure:: ../images/user_guide/tutorial/restart_options_output_file.png

Running the simulation from saved data
########################################

In this step we will be running the simulation from the previously saved state, for the year 1990, starting one day after the last day saved in the saved state. It is possible to run the simulation for any time period even beyond the one year used here.

To run the simulation from a previously saved state go to the configuration file and navigate to "**RestartOptions**". Set **restart** to "true" and "**save_model_states_for_restart**" to "false", as this is the run we will be using the saved data for. Under "**save_and_read_states_dir**" set the path to the previously created directory holding your saved data (in this example under "Users/username/restart_data").

.. figure:: ../images/user_guide/tutorial/restart_options_restarting.png

When we created the saved data we ran the simulation for the year 1989, with a five year spin up. Since this is our saved data, when running the simulation from this saved state we can only run it starting the day after. Here, we will be running the simulation for the year 1990, starting one day after the saved state data ends and without a spin up, as the saved state already includes this data.

All other options will remain as they are described under :ref:`creating a saved state <creating_a_saved_state>`.

.. figure:: ../images/user_guide/tutorial/restart_options_simulation_period_after.png

Lastly, run the simulation with these options. To verify that everything is running as intended, you should receive this message in the terminal:

.. figure:: ../images/user_guide/tutorial/restart_options_terminal_restart_run_successful.png

.. _visualize_using_panopoly:

****************************************
Vizualizing your results using Panopoly
****************************************

To visualize the output of any given simulation we suggest using `Panopoly <https://www.giss.nasa.gov/tools/panoply/>`__. You can use it to open the input files in NetCDF format or your output files after the simulation has finished running. In this Tutorial we will be using Panopoly to vizualize the output data of the :ref:`standard anthropogenic run <standard_anthropogenic_run>` for the year 1989.

Begin by downloading and installing Panopoly. Then click on "file" -> "open". Navigate to your ReWaterGAP folder. Then to "output_data" and select the created file "dis_1989-12-31.nc". Click on "open".

You should now see your data set. Double-click the "dis" file in "Geo2D" format and click create.

.. figure:: ../images/user_guide/tutorial/panopoly_map.png

Once you see a world map, labeled "Streamflow or River discharge" go to "Window" -> "Plot Controls" where you will see the time set to "1" of "365". By increasing the time you will see the River discharge change visually on the map. We recommend changing the color scheme to "GMT_hot.cpt" under "Window" -> "Color Tables Browser".

.. figure:: ../images/user_guide/tutorial/panopoly_plot_controls.png

.. _installation_guide_gwswuse:
