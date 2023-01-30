# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 14:24:15 2022.

@author: nyenah
"""
import xarray as xr
import numpy as np
from controller import configuration_module as cm


class OuputVariable:
    """Create ouput variables."""

    def __init__(self, variable_name, create, grid_coords):
        """
        Create multidemnsional dataset with variable name.

        Parameters
        ----------
        variable_name : string
            Variable name for output variable.
        grid_coords : xarray coordinate
            Contains coordinates to create output variable.
        create : boolean
             Create and write to empty data set for variable if True.

        Returns
        -------
        Output variable.

        """
        self.create = create
        if self.create is True:
            self.variable_name = variable_name
            self.grid_coords = grid_coords
            self.path = cm.config_file['FilePath']['outputDir']

            # Geting length of time,lat,lon from grid coordinates (grid_coords)
            lat_length = len(self.grid_coords['lat'].values)
            lon_length = len(self.grid_coords['lon'].values)
            time_length = len(self.grid_coords['time'].values)

            # Create dummy data for variable
            dummy_data = np.zeros((time_length, lat_length, lon_length),
                                  dtype=np.float32)

            # create Xarray dataset for output variable without variable name
            self.data = xr.Dataset(coords=self.grid_coords)

            # Add variables names for respective output varaibes
            self.data[self.variable_name] = \
                xr.DataArray(dummy_data, coords=self.grid_coords,
                             dims=('time', 'lat', 'lon'))

    def write_daily_ouput(self, array, time_step):
        """
        Write results to output variable  per time step.

        Parameters
        ----------
        array : numpy array
            results (array) to be wriiten to vaiable per time step.
        time_step : TYPE
           time step for writing ouput variable.

        Returns
        -------
        array.

        """
        if self.create is True:
            self.data[self.variable_name][time_step, :, :] = array

    def to_netcdf(self, filename):
        """
        Write output variable to NETCDF.

        Parameters
        ----------
        filename : string
            filename to save dataset.

        Returns
        -------
        NETCDF.

        """
        # I need to add meta data
        if self.create is True:
            self.data.to_netcdf(self.path + filename + '.nc')
