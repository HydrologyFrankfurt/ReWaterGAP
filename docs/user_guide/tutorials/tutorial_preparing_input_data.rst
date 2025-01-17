.. _tutorial_preparing_input_data:

Preparing Input Data
####################

.. _prepare_input_data:

In your WaterGap repository you will find an **input_data** folder, which will hold all relevant climate forcings, water use data as well as static data needed to run the simulation. Throughout this tutorial we will be running the simulation for the year 1989.

Goethe University Frankfurt Data Repository
##############################################

A comprehensive list of available data from the Goethe University Frankfurt can be found here:

- `Climate forcing GSWP3-ERA5 <https://doi.org/10.25716/GUDE.0H3E-SBWV>`_ [1]_
- `Water use input and 20CRv3-ERA5 climate forcing <https://doi.org/10.25716/GUDE.1BGX-87AA>`_ [2]_
- `Water use input and 20CRv3-W5E5 climate forcing <https://doi.org/10.25716/GUDE.0H6A-SR8Q>`_ [3]_
- `Water use input and GSWP3-ERA5 climate forcing <https://doi.org/10.25716/GUDE.1VNN-DYCV>`_ [4]_
- `Water use input and GSWP3-W5E5 climate forcing <https://doi.org/10.25716/GUDE.0296-3FD7>`_ [5]_

Installation Guide
###################

1) Download the climate forcing data of your choice.
******************************************************

To begin running WaterGAP we must download the necessary climate forcing data. In the following examples, we will be using the forcing "gswp3-w5e5_obsclim" from `ISIMIP <https://data.isimip.org/search/tree/ISIMIP3a/InputData/climate/atmosphere/gswp3-w5e5/obsclim/query//>`_ . 

The forcings from ISIMIP are sorted in groups of 10 years. We will be using the group of 1981 to 1990 as our example year of 1989 is in this group.
The forcings required are:

- precipitation [kg m-2 s-1]; `Link in ISIMIP <https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_pr_global_daily_1981_1990.nc>`_ 
- downward longwave radiation [Wm-2]; `Link in ISIMIP <https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_rlds_global_daily_1981_1990.nc>`_ 
- downward shortwave radiation [Wm-2]; `Link in ISIMIP <https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_rsds_global_daily_1981_1990.nc>`_ 
- temperature [K]; `Link in ISIMIP <https://files.isimip.org/ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/GSWP3-W5E5/gswp3-w5e5_obsclim_tas_global_daily_1981_1990.nc>`_ 

.. note::
	Make sure to remove the leap days (29th February) from the climate forcings if you are running the simulation for a leap year (WaterGap does not consider leap days).

2) Download the water use data
******************************

Next up we will need to download the necessary water use data. In the following examples, we will be using the forcing "gswp3-w5e5_obsclim" from the Goethe University Frankfurt.

The forcings required are:

- potential consumptive use from irrigation using surface water :math:`[m3/month]`
- potential water withdrawal use from irrigation using surface water :math:`[m3/month]`
- potential net abstractions from surface water :math:`[m3/month]`
- potential net abstractions from groundwater :math:`[m3/month]`

In the following tutorials we will be using data provided by Müller Schmied, H. and Nyenah, E. via the Goethe University Frankfurt which can be downloaded `here <https://doi.org/10.25716/GUDE.0296-3FD7>`_. In this data leap days have already been removed.

3) Place the downloaded data into their correct folders in the repository
*************************************************************************

Once your climate forcing and water use data has finished downloading, in your WaterGAP repository, navigate to "input_data" and place the downloaded files in their correct folders as seen in the picture below:

.. figure:: ../../images/user_guide/tutorial/input_data_folder.png

**********
References 
**********

.. [1] Müller Schmied, H. and Nyenah, E.: Climate forcing GSWP3-ERA5 as input for the global hydrological model WaterGAP, https://doi.org/10.25716/GUDE.0H3E-SBWV, 19 June 2024a.

.. [2] Müller Schmied, H. and Nyenah, E.: Water use input for WaterGAP Global Hydrological Model (Python version) and 20CRv3-ERA5 climate forcing under historical setup of direct human impacts, https://doi.org/10.25716/GUDE.1BGX-87AA, 19 June 2024b.

.. [3] Müller Schmied, H. and Nyenah, E.: Water use input for WaterGAP Global Hydrological Model (Python version) and 20CRv3-W5E5 climate forcing under historical setup of direct human impacts, https://doi.org/10.25716/GUDE.0H6A-SR8Q, 19 June 2024c.

.. [4] Müller Schmied, H. and Nyenah, E.: Water use input for WaterGAP Global Hydrological Model (Python version) and GSWP3-ERA5 climate forcing under historical setup of direct human impacts, https://doi.org/10.25716/GUDE.1VNN-DYCV, 19 June 2024d.

.. [5] Müller Schmied, H. and Nyenah, E.: Water use input for WaterGAP Global Hydrological Model (Python version) and GSWP3-W5E5 climate forcing under historical setup of direct human impacts, https://doi.org/10.25716/GUDE.0296-3FD7, 19 June 2024e.
