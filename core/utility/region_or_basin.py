import geopandas as gpd

import regionmask

"""Select Region or Basin."""

class Select_region:
    """Select region or basin of interest based on outflow station."""
    def __init__(self, run_region, mask_watergap, super_basins, stations):
        self.region = 0
        if run_region is True: 
            # Specify the latitude and longitude points using list comprehensions
            outflow_lat = stations["Lat"].values  # Replace with actual latitude
            outflow_lon = stations["Lon"].values # Replace with actual longitude
    
            # Create a GeoDataFrame with the outflow points
            outflow_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(outflow_lon, outflow_lat))
            
            # Spatial query to find the basins for the outflow points
            selected_super_basins = super_basins[super_basins.intersects(outflow_gdf.unary_union)]
            
            # Use regionmask to create the mask
            mask = regionmask.mask_geopandas(selected_super_basins,  mask_watergap)
                    
            self.region = mask.values*0
        else:
            self.region = mask_watergap.values*0
        
        

# =============================================================================
# To be added       
# =============================================================================
# import xarray as xr      
# super_basins_shapefile = 'Z:/projects/ReWaterGAP/rewatergap/input_data/static_input/super_basins/WLM_superbasins_names_outflowcellcoords_upstreamarea.shp'
# mask_watergap_path = 'Z:/projects/ReWaterGAP/rewatergap/input_data/static_input/cell_area.nc'

# super_basins = gpd.read_file(super_basins_shapefile)
# mask_watergap = xr.open_dataarray(mask_watergap_path, decode_times=False)

# # Specify the latitude and longitude points using list comprehensions
# outflow_lat = [0.25, ]  # Replace with actual latitude
# outflow_lon = [-50.25, ]  # Replace with actual longitude

# # Create a GeoDataFrame with the outflow points
# outflow_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(outflow_lon, outflow_lat))

# # Spatial query to find the basins for the outflow points
# selected_basins = super_basins.intersects(outflow_gdf.unary_union)
    

# # basin_shapefile_path = 'Z:/projects/ReWaterGAP/rewatergap/input_data/static_input/WaterGAP22e_cal_bas/WaterGAP22e_cal_bas.shp'
# # basins_cal = gpd.read_file(basin_shapefile_path)


# # Print information about the selected basins
# if not selected_basins.empty:
#     print("Selected Basins Information:")
#     print(selected_basins)
# else:
#     print("No basins found for the given outflow points.")

# # Optionally, you can plot the results
# import matplotlib.pyplot as plt

# ax = selected_basins.plot(edgecolor='black', figsize=(10, 10))
# outflow_gdf.plot(ax=ax, color='red', markersize=50)
# plt.title('Basins with Outflow Points')
# plt.show()



