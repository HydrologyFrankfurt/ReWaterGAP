.. _tutorial_docker:

############################################
Running the WaterGAP (WGHM) Docker Container
############################################

*************
Prerequisites
*************

To run Docker images, Docker Engine (Docker) must be installed on your local machine. You can download it from `Docker's official website <https://www.docker.com/>`_. The Docker documentation provides installation instructions for each supported operating system.

1) Building the Docker Image
############################

Using a Prebuilt Image 
**********************

If you prefer not to build the image yourself, you can download a prebuilt version from `Zenodo <10.5281/zenodo.17063459>`__ and proceed directly to :ref:`Step 2 <running_the_watergap_container>`.

.. note::
   The prebuild image is not updated regularly and is best used for using Docker functionality. Last update: 05.09.2025.

Building the Image Manually (Recommended)
*****************************************

If you want to build the image yourself, follow these steps:
 1. Download the `Dockerfile` from `the WaterGAP GitHub Repository <https://github.com/HydrologyFrankfurt/ReWaterGAP/blob/main/Dockerfile>`_.
 2. Create a folder on your local machine (e.g: "docker_wghm") and place the `Dockerfile` in it.
 3. Open a command-line terminal and navigate to the folder where the `Dockerfile` is located.

To build the Docker image, run the following command:

.. code-block:: bash

  $ docker build -t rewatergap_wghm .

This will create an image named `rewatergap_wghm`.

.. _running_the_watergap_container:

2) Running the WaterGAP Container
#################################

We will use a standardized run for the year 1981 as an example.

Step 1: Prepare the Working Directory
*************************************

1. On your local PC, create a folder (e.g., `docker_wghm`). If you built the docker image yourself you will already have this folder. This will be your working directory.
2. If you downloaded the ready-built image from Zenodo, place it into the working directory folder. 
3. Download and place the required **climate forcing** and **water use** input data into this folder. You can find more information on these datasets from :ref:`our tutorial on them here <prepare_input_data>`.
4. Inside the `docker_wghm` folder, create an **output directory** to store the results.

.. figure:: ../../images/user_guide/tutorial/Docker_folder.png

Step 2: Load image and Mount the Working Directory to the Docker Environment
********************************************************************************

If you've downloaded the image file (rewatergap_wghm.tar), in your current working directory, load the image using the command below. If you built the image yourself skip this command.

.. code-block:: bash

  $ docker load -i rewatergap_wghm.tar

.. note::
  Depending on your machine this step might take a while. In out case it took around 2 minutes.

To make the `docker_wghm` folder accessible inside the container, use the following command:

.. code-block:: bash

  $ docker run -v $(PWD):/app/mounted_dir -it rewatergap_wghm bash

This command:
 - Mounts the `Docker_wghm` folder to `/app/mounted_dir` inside the container.
 - Runs the container in interactive mode (`-it`). This makes sure, you can see what you have mounted.

Use the exit command to leave this interacitve mode after you have checked, that the right folder has been mounted.

Step 3: Configure the WaterGAP Model
************************************
To modify the configuration file, follow these steps:

1. Copy the configuration file from the Docker container to your local `docker_wghm` folder:

.. code-block:: bash

  $ docker cp <container_id>:/app/Config_ReWaterGAP.json ./Config_ReWaterGAP.json

.. note::
  To find your `container_id`, use the following command. The requred id is also marked in the picture below.

  .. code-block:: bash

    $ docker ps -a

 .. figure:: ../../images/user_guide/tutorial/Docker_container_id.png

2. Open `Config_ReWaterGAP.json` in a text editor of your choice.
3. Update the file paths for **climate forcing**, **water_use**, and **output** directories. Since the directory is mounted as `mounted_dir`, the paths should be set as:

- "climate_forcing": "mounted_dir/climate_forcing/",
- "water_use": "mounted_dir/water_use/",
- "output": "mounted_dir/output/"

.. figure:: ../../images/user_guide/tutorial/file_paths_docker.png

4. Update the configuration file to set it up for a standard run for the year 1981. :ref:`For more information see the tutorial here <standard_anthropogenic_run>`.

.. note::
  See the configuration file settings for how to run the model for other runoptions :ref:`here <tutorial_different_simulation_options>`. If your run is a restart run, make sure that your restart files are saved to "mounted_dir/output".

5. Save the updated configuration file.

3) Running the WaterGAP Model
#############################

Now that the environment is set up and the configuration file is updated, you can proceed with running the WaterGAP model inside the Docker container.

.. code-block:: bash

  $ docker run -v $(PWD):/app/mounted_dir -it rewatergap_wghm

.. figure:: ../../images/user_guide/tutorial/docker_run.png

