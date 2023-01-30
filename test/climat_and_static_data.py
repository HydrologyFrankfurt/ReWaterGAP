# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 17:12:04 2022.

@author: nyenah
"""
import glob
import pandas as pd
import xarray as xr
import numpy as np


class ClimateForcing:
    """Handles climate forcing data."""

    def __init__(self, simulate=False, neg_prec=False):
        """
        Get filepath for real data or simulate data if simulate option is true.

        Parameters
        ----------
        simulate : bool, optional
            Simulate input data. The default is False.
        neg_prec : bool, optional
            use negative precipiation. The default is False.

        Returns
        -------
        None.

        """
        # ==============================================================
        # path to climate forcing netcdf data
        # ==============================================================
        in_path = './input_data/climate_forcing/'

        precipitation_path = (in_path + 'precipitation/*.nc')
        longwave_radiation_path = (in_path + 'rad_longwave/*.nc')
        shortwave_radiation_path = (in_path + 'rad_shortwave/*.nc')
        temperature_path = (in_path + 'temperature/*.nc')

        # ==============================================================
        # Loading in climate forcing
        # ==============================================================
        if simulate is False:
            try:
                # load real data from directory
                #  Actual name: Precipitation, Unit:  kg m-2 s-1
                self.precipitation = xr.open_mfdataset(
                                            glob.glob(precipitation_path),
                                            chunks={'time': 365})

                #  Actual name: Downward longwave radiation  Unit: Wm−2
                self.down_longwave_radiation = xr.open_mfdataset(
                                            glob.glob(longwave_radiation_path),
                                            chunks={'time': 365})

                #  Actual name: Downward shortwave radiation  Unit: Wm−2
                self.down_shortwave_radiation = xr.open_mfdataset(
                                            glob.glob(shortwave_radiation_path),
                                            chunks={'time': 365})

                # #  Actual name: Air temperature, Unit: K
                self.temperature = xr.open_mfdataset(
                                            glob.glob(temperature_path),
                                            chunks={'time': 365})
            except FileNotFoundError:
                print("input file not found")
        else:
            # simulating data with valid ranges
            lon = np.arange(-179.75, 179.80, 0.5)*-1
            lat = np.arange(-89.75, 89.80, 0.5)*-1
            time = np.array([np.datetime64('1901-01-01')])

            if neg_prec is True:
                pr = np.random.uniform(-5, 90, size=(1, 360, 720))
                self.precipitation = \
                    xr.Dataset(data_vars={'pr': (['time', 'lat', 'lon'], pr)},
                               coords={'lon': lon,  'lat': lat, 'time': time})
            else:
                pr = np.random.uniform(0, 90, size=(1, 360, 720))
                self.precipitation = \
                    xr.Dataset(data_vars={'pr': (['time', 'lat', 'lon'], pr)},
                               coords={'lon': lon,  'lat': lat, 'time': time})

            rlds = np.random.uniform(40, 200, size=(1, 360, 720))
            self.down_longwave_radiation = \
                xr.Dataset(data_vars={'rlds': (['time', 'lat', 'lon'], rlds)},
                           coords={'lon': lon,  'lat': lat, 'time': time})

            rsds = np.random.uniform(0, 300, size=(1, 360, 720))
            self.down_shortwave_radiation = \
                xr.Dataset(data_vars={'rsds': (['time', 'lat', 'lon'], rsds)},
                           coords={'lon': lon,  'lat': lat, 'time': time})

            tas = np.random.uniform(220, 310, size=(1, 360, 720))
            self.temperature = \
                xr.Dataset(data_vars={'tas': (['time', 'lat', 'lon'], tas)},
                           coords={'lon': lon,  'lat': lat, 'time': time})


class StaticData:
    """Handles static data."""

    def __init__(self):
        """
        Get file path.

        Return
        ------
        Static data

        """
        in_path = './input_data/static_input/'
        # ==============================================================
        # path to climate forcing netcdf data
        # ==============================================================
        land_cover_path = (in_path + 'watergap_22d_landcover.nc4')

        humid_arid_path = (in_path + 'watergap_22e_aridhumid.nc4')

        canopy_model_parameters_path = \
            (in_path + 'canopy_model_parameters.csv')

        gtopo30_elevation_path = (in_path + 'watergap_22e_v001_elevrange.nc4')

        soil_static_files_path = (in_path + 'soil_storage/*')
        # ==============================================================
        # Loading in climate forcing
        # ==============================================================
        try:
            # Actual name: Land cover , Unit: (-)
            land_cover = xr.open_dataset(land_cover_path,
                                         decode_times=False)
            self.land_cover = land_cover.landcover[0].values

            # Humid-arid calssification based on Müller Schmied et al. 2021
            humid_arid = xr.open_dataset(humid_arid_path,
                                         decode_times=False)
            self.humid_arid = humid_arid.aridhumid[0].values

            # Canopy model paramters (Table)
            self.canopy_model_parameters = \
                pd.read_csv(canopy_model_parameters_path)

            # Elevations according to GTOPO30 (U.S. Geological Survey, 1996)
            gtopo30_elevation = xr.open_dataset(gtopo30_elevation_path,
                                                decode_times=False)
            self.gtopo30_elevation = gtopo30_elevation.elevrange.values

            self.soil_static_files = \
                xr.open_mfdataset(soil_static_files_path,
                                  decode_times=False)

        except FileNotFoundError:
            print("input file not found")

    def soil_static_data(self):
        """
        Update land area fraction.

        Returns
        -------
        None.

        """
        # Built up area, units = (-)
        builtup_area = self.soil_static_files.builtup_area.values

        # Total available water content, units = mm
        total_avail_water_content = self.soil_static_files.tawc.values

        # Drainage direction of the grid cell, units = (-)
        drainage_direction = self.soil_static_files.ldd.values

        # Maxumum ground water recharge = mm
        max_groundwater_recharge = self.soil_static_files.rgmax.values/100

        # Soil texture, units= (-)
        soil_texture = self.soil_static_files.texture.values

        # Corrected Missipi only groundwater recharge factor, units= (-)
        gw_recharge_factor_corr = \
            self.soil_static_files.gw_factor_corr.values

        # Uncorrected groundwater recharge factor, units= (-)
        gw_recharge_factor_uncorr = \
            self.soil_static_files.gw_factor_uncorr.values

        # Groundwater recharge factor, units= (-)
        groundwater_recharge_factor = \
            np.where(gw_recharge_factor_corr > 0,
                     gw_recharge_factor_corr *
                     gw_recharge_factor_uncorr,
                     gw_recharge_factor_uncorr)

        return builtup_area, total_avail_water_content, drainage_direction,\
            max_groundwater_recharge, soil_texture, groundwater_recharge_factor
