.. _contributing_to_code:

########################
Contributing to the code (Under construction)
########################

*******************************************
Write a New Variable to NetCDF in the Model
*******************************************

The variable we will be writing out is the “wetland_extent”. For this we will need to change the respective storage module (in the model folder found in the source repository) and additional files outlined below. 

1. Update the module “lakes_wetlands.py”
	- Find the “lakes_wetlands.py” module in the model folder in the source repository at “model/lateralwaterbalance/lakes_wetlands.py”
	- In the “lakes_wetlands.py” module you can find the “lake_wetland_water_balance” function. Within this function you can find the variable “lake_wet_area”, which contains the area of lakes and wetlands (both local and global).
		[image here 1]
	- Add the “lake_wet_area” to the return  value of the function “lake_wetland_water_balance”
		[image here 2]

2. Edit the module “routing.py”
	- Find the “routing.py” module in the model folder in the source repository at “model/lateralwaterbalance/routing.py”
	- In the “routing.py” module you can find the “river_routing” function. Within this function we will create two variables
	- Find the sections with the headers “Local wetland” and “Global wetland”. Create the variable names “local_wetland_extent” and “global_wetland_extent”
		[image here 3]
	- Modify the routing script for wherever the function “lake_wetland_water_balance “ is called to account for the new variable added in Step 1.
		[image here 4]
	- Add the “local_wetland_extent” and “global_wetland_extent” to the return  values of the function “river_routing”
		[image here 5]

3. Edit the module “waterbalance_lateral.py”
	- Find the “waterbalance_lateral.py” module in the model folder in the source repository at “model/lateralwaterbalance/waterbalance_lateral.py”
	- In the “waterbalance_lateral.py” module under the “routing” section, you can find the “out” variable, where all the river routing outputs are called. Below the last out variable, add the newly created “local_wetland_extent” and “global_wetland_extent” variables and assign the respective return values to the variables created.
		[image here 6]
	- Update the “LateralWaterBalance.fluxes” to add the new variables (first add a meaningful variable name and assign the variable to it). WaterGAP only differentiates between “storages” and “fluxes” as standard output. If the created variables are neither, we will add it to “fluxes”. 
		[image here 7]

4. Modify NetCDF Write Function
	- “view/createandwrite.py”
	- Find “lb_output_vars”
	Add the variables created in Step 3 to the “lb_output_vars” and add the names so it will follow the format of:
	..code block
          "meaningful variable name": "full name in configuration file",
	- In WaterGAP all storages are stored as [mm] and all fluxes are stores as [mm/s]. In this case, for area, it is neither and it is added as [km2]. For this expand the bracket for lateral fluxes under the “base_units” function to include the new variables
		[image here 8]

5. Modify the output variable info
	- view/output_var_info.py
	- Update the attributes for the new variables under “LateralWaterBalanceFluxes”.
		[image here 9]

6. Delete the Cache (Important)
	- After any changes to the python modules in the “model/lateralwaterbalance/” or “model/verticalwaterbalance/” delete the “__pycache__” folders. 
	Numba is used to improve runtimes for WaterGAP. Numba directly translates the Python code to machine code. For this model codes are cached. According to Numba “The cache is invalidated when the corresponding source file is modified. However, it is necessary sometimes to clear the cache directory manually. For instance, changes in the compiler will not be recognized because the source files are not modified.” [1]_

##########
References 
##########

.. [1] https://numba.pydata.org/numba-doc/dev/developer/caching.html#:~:text=To%20clear%20the%20cache%2C%20the,raised%20at%20the%20compilation%20site.
