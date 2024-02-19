import numpy as np
import pandas as pd 
import xarray as xr

"""Select Upstream Basin."""

class Select_upstream_basin:
    """Select upstream basin of interest based on outflow station."""
    def __init__(self, run_upstream_basin,  arc_id,  stations, lat_lon_arcid, inflow_cell):
        self.upstream_basin = 0
        if run_upstream_basin is True: 

            # check if arc_id are present 
            if np.nansum(stations["station_arcid"].values)==0:
                lat_lon_arcid = lat_lon_arcid.round(2) # round data to 2 decimal place (eg. -46.7499999999999 = -46.75)
                
                # Example lists of latitude and longitude
                latitudes = stations["lat"].values.tolist()  
                longitudes = stations["lon"].values.tolist()
                
                # Create an empty list to store results
                selected_arcids = []
                
                # Iterate through the lists of latitude and longitude
                for lat, lon in zip(latitudes, longitudes):
                    # Select the arcid for the current latitude and longitude
                    selected_row =  \
                        lat_lon_arcid[(lat_lon_arcid['Lon'] == lon) & (lat_lon_arcid['Lat'] == lat)]['ArcID']
                    
                    # Check if there is a match
                    if not selected_row.empty:
                        selected_arcids.append(selected_row.iloc[0])
                    else:
                        selected_arcids.append(None)
                
                # Print the results
                for i, (lat, lon) in enumerate(zip(latitudes, longitudes)):
                    arcid = selected_arcids[i]
                    if arcid is not None:
                       pass
                    else:
                        print(f"No matching arcid found for latitude {lat} and longitude {lon}")

            else:
                selected_arcids =  stations["station_arcid"].values.tolist()
                
                
            # get upstream cell data 
            inflow_cell.set_index('Arc_ID', inplace=True)
            upstream_cells  = selected_arcids.copy()
            all_upstream = Select_upstream_basin.get_all_upstream_cells_arcid(selected_arcids, inflow_cell, upstream_cells)

            # create a 2d mask for the selected basin 
            mask = arc_id.isin(all_upstream)
            self.upstream_basin = np.where(mask==True, 0,np.nan) 

        else:
            self.upstream_basin = arc_id.values * 0
        
        
    @staticmethod
    def get_all_upstream_cells_arcid(arcid_list, inflow_cell, upstream_cells):
        temp_upstream_cell =[]
        for i in arcid_list:
            next_cells = inflow_cell.loc[i][inflow_cell.loc[i]>0]
            temp_upstream_cell.extend(next_cells)
        upstream_cells.extend(temp_upstream_cell)
        if len(temp_upstream_cell) != 0 :
            Select_upstream_basin.get_all_upstream_cells_arcid(temp_upstream_cell, inflow_cell, upstream_cells)
    
        return upstream_cells







    


