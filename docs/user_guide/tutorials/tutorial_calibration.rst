.. _tutorial_calibration_no:

############################################
Calibrate WaterGAP **(under development)**
############################################

.. contents:: 
    :depth: 3
    :backlinks: entry

********
Rational
********

WasterGAP is calibrated in a very simple basin-specific manner to match long-term mean annual observed streamflow at the outlet of 1509 drainage basins that cover ∼ 55 % of the global drainage area (except Antarctica and Greenland).

Calibration follows a four-step scheme with specific calibration status (CS) [1]_ [2]_ .

- **CS1**: Adjust the basin-wide uniform parameter :math:`γ` (Müller Schmied et al., 2021, their Eq. 18) in the range of [0.1–5.0] to match mean annual observed streamflow within ±1 %.
- **CS2**: Adjust :math:`γ` as for CS1 but within 10 % uncertainty range (90 %–110 % of observations).
- **CS3**: As for CS2 but apply the areal correction factor, CFA (adjusts runoff and, to conserve the mass balance, actual evapotranspiration as the counterpart of each grid cell within the range of [0.5–1.5]), to match mean annual observed streamflow with 10 % uncertainty.
- **CS4**: As for CS3 but apply the station correction factor, CFS (multiplies streamflow in the cell where the gauging station is located by an unconstrained factor), to match mean annual observed streamflow with 10 % uncertainty to avoid error propagate ion to the downstream basin.

..note
    For each basin, calibration steps 2–4 are only performed if the previous step was not successful.

****************************************************
Step-by-step guide to calibrating the WaterGAP model
****************************************************

Preparing climate and water use data 
####################################

See :ref:`tutorials <prepare_input_data>` on where to download climate forcing and water use data. 

Preparinging observed streamflow
################################

Download the observed streamflow data 
*************************************
The observed streamflow data can be downloaded from `zenodo <https://zenodo.org/records/7255968>`_ as a zip file. Download all files of the current version and unpack the zip file. You will find all necessary files as well as a readme.md file, which explains the content of the files.
The unzipped file contains files such as:

    - "WaterGAP22e_cal_stat.shp" contains the location of the calibration stations as point-shapefile. 
    - The ESRI shapefile "WaterGAP22e_cal_bas.shp"" contains the basin outlines of the calibration stations
    - "json_annual", which contains the annual streamflows for 1509 stations.

Unzip all files inside the downloaded folder and save it to the location of your choice.

Edit the path in the configuration file
***************************************
In the WaterGAP Configuration file "Config_ReWaterGAP.json" navigate to "Calibrate WaterGAP". Under "path_to_observed_discharge" add the path to the "json_annual" folder you just saved and set "run_calib" to "true".

..Example pictiure

Modify the station file
#######################
Define the basin in the stations.csv file basesd on the latitude and longitude coordinates of the stations. The coordinates have to be in multiples of 0.5 degrees.

Run WaterGAP to compute actual NAs and NAg (standard anthropogenic run)
#######################################################################

To run the calibration scheme use this command:

.. code-block:: bash

    $ python3 run_calibration.py local "number of calibration regions"

    - "local": The program is run on your local server.
    - "number of calibration regions": Watergap groups all stations into calibration regions, which are stations found in independent super basins. If "number of calibration regions" is set to 27, WaterGAP groups the 1509 stations into 27 calibration regions.


References 
##########

.. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M., Herbert, C., Niemann, C., Peiris, T. A., Popat, E., Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S., Telteu, C.E., Trautmann, T., & Döll, P. (2021). The global water resources and use model WaterGAP v2.2d: model description and evaluation. Geoscientific Model Development, 14(2), 1037–1079. https://doi.org/10.5194/gmd-14-1037-2021
.. [2] according to Müller Schmied et al., 2023:

