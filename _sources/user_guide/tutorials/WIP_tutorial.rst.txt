
#################################
How to run the WaterGAP Container
#################################
  
1)	Starting the container
- Find the docker file in the <repository>

***********************
Building a Docker image
***********************

Dockerfile to build an own image
Be in the docker directory (for example dk_watergap/)
All folder/files (rewatergap software, dockerfile, requirements.txt) should be in this folder, including the Dockerfile
To build the image (here example with ot_watergap), type in the command line: 
docker build –t ot_watergap .
You should see the image in the Docker Software

**********************
Loading a docker image
**********************
  
This is only needed when having image uploaded from elsewhere to load them to default folder from var/lib/docker. For built image in the host machine, they will be automatically saved there.

Type in the command line:
docker load -i ot_watergap.tar
Adapt the init_OUTLAST.json
start/end
restart: false when no initial storage needed, true when using initial storage from previous runs
To check, if everything is in the dockerfile: run it and mount volume (mapping the climate folder etc. to our current directory (app/); 
docker run  -v $(PWD):/app/outlast_dir -it ot_watergap bash
Depends on the host machine, command can be different: PWD/pwd, e.g. {pwd} in windows
bash -> you can check what is inside the docker, for example if you type now ls
 
Run ReWaterGAP in the container by typing in the command line (without the bash):
docker run  -v $(PWD):/app/outlast_dir -it ot_watergap
Output (together with the pickle files) will be saved in the folder which was defined in init_WaterGAP_outlast.py. The current version (v0) are default to be save in the same directory. The output directory should be located independently with the model, images, etc, … after having discussed with KIT. The states for restart will be saved as a pickle file
For model runs that start from previously saved states, the restart pickle file needs to be in the docker directory (or linked accordingly) and the restart option in the init_OUTLAST.json set to True

*************************
Inside the container / xy
*************************

- a folder /app (=main working directory, where all folders etc. will be) is created
- requirements.txt for ReWaterGAP (packages etc.) are copied into app/ folder 
- the full ReWaterGAP software is copied into the app/ folder
- Run init_container.py
- defines the static paths, e.g. config path = mt/config
- read init_OUTLAST.json
- load, modify, save watergap_config according to init_OUTLAST.json
- run_watergap.py with modified watergap_config
- calculate indicators (calc_DHIs.py)
- save indicators to mt/output_data
