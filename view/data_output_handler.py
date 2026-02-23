# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Create ouput variables."""

import datetime as dt
import xarray as xr
import numpy as np
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
        create : boolean
             Create and write to empty data set for variable if True.
        grid_coords : xarray coordinate
            Contains coordinates to create output variable.

        Returns
        -------
        Output variable.

        """
        self.variable_name = variable_name
        self.create = create
        if self.create:
            self.grid_coords = grid_coords

            # Geting length of time,lat,lon from grid coordinates (grid_coords)
            lat_length = len(self.grid_coords['lat'].values)
            lon_length = len(self.grid_coords['lon'].values)
            time_length = len(self.grid_coords['time'][:365].values)

            # Create dummy data for variable
            if self.variable_name == "get_neighbouring_cells_map":
                dummy_data = np.zeros((time_length, lat_length, lon_length, 2),
                                      dtype=np.int32)
                self.data = xr.Dataset(
                        {'get_neighbouring_cells_map':
                         (['time', 'lat', 'lon', 'dim2'], dummy_data)},

                        coords={
                            'time': self.grid_coords['time'][:365].values,
                            'lat': self.grid_coords['lat'].values,
                            'lon': self.grid_coords['lon'].values,
                            # Adding a new dimension 'dim2'
                            'dim2': np.arange(2)})

            elif self.variable_name == "smax":  # maximum soil moisture
                dummy_data = np.zeros((lat_length, lon_length),
                                      dtype=np.float32)
                self.data = xr.Dataset(
                        {'smax': (['lat', 'lon'], dummy_data)},

                        coords={'lat': self.grid_coords['lat'].values,
                                'lon': self.grid_coords['lon'].values})

            else:
                dummy_data = np.full((time_length, lat_length, lon_length),
                                     np.nan, dtype=np.float32)

                dummy_coords = {"time": self.grid_coords['time'][:365].values,
                                "lat": self.grid_coords['lat'].values,
                                "lon": self.grid_coords['lon'].values}

                # create Xarray dataset for output variable
                self.data = xr.Dataset(coords=dummy_coords).\
                    chunk({'time': 1, 'lat': len(self.grid_coords['lat'].values), 
                           'lon':  len(self.grid_coords['lon'].values)})

                # Add variables names for respective output varaibes
                self.data[self.variable_name] = \
                    xr.DataArray(dummy_data, coords=dummy_coords,
                                 dims=('time', 'lat', 'lon'),
                                 )

            # Add variable metadata
            unit_conversion_info = ["If the variable needs conversion to"
                                    " volumetric units (L³ T⁻¹ or L³),"
                                    " use watergap22e_continentalarea.nc4"
                                    " (water density is 1 kg per dm³);"
                                    "otherwise, conversion is not needed."]
            self.data[self.variable_name].attrs = {
                "standard_name": self.variable_name,
                "long_name": var_info.modelvars[self.variable_name]['long'],
                "units": var_info.modelvars[self.variable_name]['unit'],
                "unit_conversion_info": unit_conversion_info[0]
                }

            # Add global metadata
            self.data.attrs = {
                'title': "WaterGAP"+" "+watergap_version.__version__ + ' model ouptput',
                'institution': watergap_version.__institution__,
                'contact': "nyenah@em.uni-frankfurt.de",
                'model_version':  "WaterGAP"+" "+watergap_version.__version__,
                "reference": watergap_version.__reference__,
                "license": "LGPL-3.0",
                'Creation_date':
                    dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            del dummy_data  # delete dummy data to free memory

        # =====================================================================

    def write_daily_output(self, array, time_step, year, month, day):
        """
        Write results to output variable  per time step.

        Parameters
        ----------
        array : numpy array
             results (array) to be wriiten to vaiable per time step.
        time_step : int
            Daily timestep.
        year: : int
            Simulation year
        month : int
            Simulation month
        day : int
            Simulation day

        Returns
        -------
        None.

        """
        if self.create:
            # Check if it's a new year (time to update the dataset time values)
            if month == 1 and day == 1:
                # Get right dates  for data
                next_year_time = \
                    self.grid_coords['time'].sel(time=str(year))

                # Update the time coordinate in self.data except for
                # maximum soil moisture
                if self.variable_name == "smax":
                    self.data[self.variable_name][:, :] = array
                else:
                    self.data = self.data.reindex(time=next_year_time)

            # reset counter to zero after each year
            if self.variable_name == "smax":
                mod_time_step = None
            else:
                mod_time_step = time_step % len(self.data['time'])
                if self.variable_name == "get_neighbouring_cells_map":
                    fill_date = self.data.time[mod_time_step]
                    self.data[self.variable_name].loc[{"time": fill_date}] = array
                else:
                    self.data[self.variable_name][mod_time_step, :, :] = array
