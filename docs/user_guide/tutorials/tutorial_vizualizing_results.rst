.. _tutorial_vizualizing_results:

Vizualizing your results using Panopoly
#########################################

To visualize the output of any given simulation we suggest using `Panopoly <https://www.giss.nasa.gov/tools/panoply/>`__. You can use it to open the input files in NetCDF format or your output files after the simulation has finished running. In this Tutorial we will be using Panopoly to vizualize the output data of the :ref:`standard anthropogenic run <standard_anthropogenic_run>` for the year 1989.

Begin by downloading and installing Panopoly. Then click on "file" -> "open". Navigate to your ReWaterGAP folder. Then to "output_data" and select the created file "dis_1989-12-31.nc". Click on "open".

You should now see your data set. Double-click the "dis" file in "Geo2D" format and click create.

.. figure:: ../../images/user_guide/tutorial/panopoly_map.png

Once you see a world map, labeled "Streamflow or River discharge" go to "Window" -> "Plot Controls" where you will see the time set to "1" of "365". By increasing the time you will see the River discharge change visually on the map. We recommend changing the color scheme to "GMT_hot.cpt" under "Window" -> "Color Tables Browser".

.. figure:: ../../images/user_guide/tutorial/panopoly_plot_controls.png
