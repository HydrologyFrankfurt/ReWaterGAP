# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 14:24:15 2022.

@author: nyenah
"""
import xarray as xr
import numpy as np
import datetime as dt
from misc import watergap_version
from view import output_var_info as var_info


class OutputVariable:
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
        self.variable_name = variable_name
        self.create = create
        if self.create is True:
            self.grid_coords = grid_coords

            # Geting length of time,lat,lon from grid coordinates (grid_coords)
            lat_length = len(self.grid_coords['lat'].values)
            lon_length = len(self.grid_coords['lon'].values)
            time_length = len(self.grid_coords['time'].values)

            # Create dummy data for variable
            dummy_data = np.zeros((time_length, lat_length, lon_length),
                                  dtype=np.float32)

            # create Xarray dataset for output variable without variable name
            self.data = xr.Dataset(coords=self.grid_coords).\
                chunk({'time': 1, 'lat': 360, 'lon': 720})

            # Add variables names for respective output varaibes
            self.data[self.variable_name] = \
                xr.DataArray(dummy_data, coords=self.grid_coords,
                             dims=('time', 'lat', 'lon'),
                             )
            # Add variable metadata
            self.data[self.variable_name].attrs = {
                "standard_name": self.variable_name,
                "long_name": var_info.modelvars[self.variable_name]['long'],
                "units": var_info.modelvars[self.variable_name]['unit'],
                }

            # Add global metadata
            self.data.attrs = {
                'title': "WaterGAP"+" "+watergap_version.__version__ + ' model ouptput',
                'institution': watergap_version.__institution__,
                'contact': "hannes.mueller.schmied@em.uni-frankfurt.de",
                'model_version':  "WaterGAP"+" "+watergap_version.__version__,
                "reference": watergap_version.__reference__,
                'Creation_date':
                    dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

        # ======================================================================================================

    def write_daily_output(self, array, time_step):
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

