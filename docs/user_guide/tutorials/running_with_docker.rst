# 
Running the WaterGAP (WGHM) Container
#

## Prerequisites
To run Docker images, **Docker Engine** (Docker) must be installed on your local machine. You can download it from [Docker's official website](https://www.docker.com/). The Docker documentation provides installation instructions for each supported operating system.

## 1) Building the Docker Image
### Using a Prebuilt Image (Recommended)
If you prefer not to build the image yourself, you can download a prebuilt version from **[repository/Zenodo]** and proceed directly to [Step 2: Running the Container](#2-running-the-watergap-container).

### Building the Image Manually
If you want to build the image yourself, follow these steps:
1. Download the `Dockerfile` from **[repository/Zenodo]**.
2. Create a folder on your local machine (e.g: "docker_wghm") and place the `Dockerfile` in it.
3. Open a command-line terminal and navigate to the folder where the `Dockerfile` is located.

To build the Docker image, run the following command:
```sh
$ docker build -t rewatergap_wghm .
```

This will create an image named `rewatergap_wghm`.

---
## 2) Running the WaterGAP Container

We will use a **standardized run for the year 1981** as an example.

### Step 1: Prepare the Working Directory
1. On your local PC, create a folder (e.g., `docker_wghm`).If you built the docker image yourself you will already have this folder. This will be your **working directory**.
2. Download and place the required **climate forcing** and **water use** input data into this folder. You can access these datasets from **[Data Source]**.
3. Inside the `docker_wghm` folder, create an **output directory** to store the results.

### Step 2: Mount the Working Directory to the Docker Environment
To make the `docker_wghm` folder accessible inside the container, use the following command:

```sh
$ docker run -v $(PWD):/app/mounted_dir -it rewatergap_wghm bash
```

This command:
- Mounts the `Docker_wghm` folder to `/app/mounted_dir` inside the container.
- Runs the container in **interactive mode** (`-it`). This makes sure, you can see what you have mounted.

Use the exit command to leave this interacitve mode after you have checked, that the right folder has been mounted.

### Step 3: Configure the WaterGAP Model
To modify the **configuration file**, follow these steps:
1. Copy the configuration file from the Docker container to your local `docker_wghm` folder:
```sh
$ docker cp <container_id>:/app/Config_ReWaterGAP.json ./Config_ReWaterGAP.json
```
*Note:* To find your `container_id`, use:
```sh
$ docker ps -a
```
2. Open `Config_ReWaterGAP.json` in a text editor of your choice.
3. Update the file paths for **climate forcing**, **water_use**, and **output** directories. Since the directory is mounted as `mounted_dir`, the paths should be set as:
```
"climate_forcing": "mounted_dir/climate_forcing/",
"water_use": "mounted_dir/water_use/",
"output": "mounted_dir/output/"
```

4. Update the configuration file to set it up for a standard run for the year 1981. <See here>. 

Note: See the configuration file settings for how to run the model for other runoptions <here>. If your run is a restart run, make sure that your restart files are saved to "mounted_dir/output".

5. Save the updated configuration file.

---
## 3) Running the WaterGAP Model
Now that the environment is set up and the configuration file is updated, you can proceed with running the WaterGAP model inside the Docker container.

```sh
$ docker run -v $(PWD):/app/mounted_dir -it rewatergap_wghm
```

