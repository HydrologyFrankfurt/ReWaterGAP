5 minute guide to WaterGAP
--------------------------

**1: Download and Install Python** (Skip this step if python is already installed)
	
Download the current Python version for your OS from `the official Python Website <https://www.python.org/downloads/>`__ and install.

**2: Download and Install the package manager "Mamba"** (Skip this step if mamba is already installed)
	
Go to the `Mamba Website <https://github.com/conda-forge/miniforge>`__ , choose your OS (Linux or MacOS) and download the installation file (the downloaded file has an ".sh" extension)
	
	
Open your terminal and navigate to the downloaded file (it has the name "Miniforge3-(OSname)-(architecture).sh")
	
	
Install Mamba by running the following command and follow the installation prompts. The prompt will notify you where to install Mamba (see :ref:`image <mamba_licence_location>` below). The created folder will be called "miniforge3".


.. code-block:: bash
		
	$ bash Miniforge3-MacOSX-arm64.sh (example for MacOS Apple Silicon)

.. _mamba_licence_location:

.. figure:: ../images/getting_started/mamba_licence_location.png


After the installation is complete, you will see the :ref:`Mamba logo <installation_complete>` .


.. _installation_complete:

.. figure:: ../images/getting_started/installation_complete.png



Navigate to the "bin" folder in the newly created "miniforge3" folder.

.. code-block:: bash

	$ cd /Users/leon/miniforge3/bin (example for MacOS Apple Silicon)
	
	Activate mamba by running the following command

.. code-block:: bash

		$ source activate


**3: Clone the WaterGAP repository**

Using the Terminal, navigate to the directory of choice where the WaterGAP folder will be copied into. Then use the following command to clone the repository.

.. code-block:: bash

		git clone https://github.com/HydrologyFrankfurt/ReWaterGAP.git

Find more information in the official GitHub documentation `here <https://docs.github.com/en/get-started/quickstart/fork-a-repo#cloning-your-forked-repository>`__ .

**4: Create an environment to run ReWaterGAP in**

Navigate to the ReWaterGAP folder in the terminal using the following command.

.. code-block:: bash

	$ cd user/…/ReWaterGAP
	

	Create an environment (e.g. with the name "watergap") and install the required packages from the requirements.txt file by running the following command.

.. code-block:: bash

	example
	$ mamba create --name watergap --file requirements.txt

	Activate the WaterGAP environment using the following command.

.. code-block:: bash

	example
	$ mamba activate watergap



**5. Get Input Data**

The following data should be provided by the User in NetCDF format:

Climate Forcing
	- precipitation
	- longwave radiation
	- shortwave radiation
	- temperature

Water Use
	- potential consumptive use from irrigation (monthly)
	- potential water withdrawal use from irrigation (monthly)
	- potential net abstractions from surface water (monthly)
	- potential net abstractions from groundwater (monthly)


The files need to be copied to their respective folders in ../ReWaterGAP/input_data (see picture):

.. figure:: ../images/getting_started/input_data.png


You can find the necessary climate forcing data at `ISIMIP <https://data.isimip.org/search/tree/ISIMIP3b/SecondaryInputData/climate/atmosphere/mri-esm2-0/>`__ .

**6: Run WaterGAP using the configuration file „Config_ReWaterGAP.json“ - Naturalized run**

.. code-block:: bash

	$ python3 run_watergap.py Config_ReWaterGAP.json
