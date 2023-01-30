# -*- coding: utf-8 -*-

# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================

"""Leaf Area Index Class."""

# =============================================================================
# This module computes leaf area index for each grid cell in parallell
# by calling a vectorised leaf  area index function from the
# parallel_leaf_area_index_module. vectorised functions peforms elementwise
# computations on all arrays at onces.
# See https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html
# Leaf area index in computed based on section 4.2.3 of
# (Müller Schmied et al. (2021)).
# =============================================================================

import numpy as np
from core.verticalwaterbalance import parallel_leaf_area_index
from core.utility import check_negative_precipitation as check


class LeafAreaIndex:
    """Compute leaf area index.

    Parameters
    ----------
    climate_forcing : array
        Input forcing to caluclate leaf area index
    static_data : array and csv
        Land_cover  class (array)  based on [1]_.
        Humid-arid calssification(array) based on [1]_.
        CSV formatted table that contains maximum leaf area index (-), Fraction
        of deciduous plants per lancover type (-), Reduction factor for
        evergreen plants per land cover type (-).  This stated parameters are
        used used to compute  miniimum leaf area_index (-).

        The parameters in the csv table are  taken from [2]_.

        References.

        .. [1] Müller Schmied, H., Cáceres, D., Eisner, S., Flörke, M.,
                    Herbert, C., Niemann, C., Peiris, T. A., Popat, E.,
                    Portmann, F. T., Reinecke, R., Schumacher, M., Shadkam, S.,
                    Telteu, C.E., Trautmann, T., & Döll, P. (2021).
                    The global water resources and use model WaterGAP v2.2d:
                    model description and evaluation. Geoscientific Model
                    Development, 14(2), 1037–1079.
                    https://doi.org/10.5194/gmd-14-1037-2021

        .. [2] Müller Schmied, H., Müller, R., Sanchez-Lorenzo, A., Ahrens, B.,
                    and Wild, M.: Evaluation of radiation components in a
                    global freshwater model with station-based observations,
                    Water, 8, 450, https://doi.org/10.3390/w8100450,2016b
    date : datetime64
        Date to select specific days

    Methods
    -------
    get_daily_leaf_area_index:
        Vectorized daily leaf area index.
    """

    def __init__(self, climate_forcing, static_data, date):
        self.climate_forcing = climate_forcing
        self.static_data = static_data
        self.date = date

        # =====================================================================
        # Distribute maximum and minimum Leaf area index over all grid cells
        # together with inital days per land cover
        # =====================================================================

        # Actual name: canopy model paramters (Table)
        parameters_lai = self.static_data.canopy_model_parameters

        def minimum_leaf_area_index(max_leaf_area_index, frac_decid_plant,
                                    red_factor_evergreen):
            """
            Compute minimum one-sided Leaf Area Index.

            Parameters
            ----------
            max_leaf_area_index : array
                Maximum one-sided leaf area index per lancover type. Units: (-)
            frac_decid_plant : aaray
                Fraction of deciduous plants per lancover type. Units: (-)
            red_factor_evergreen : TYPE
                Reduction factor for evergreen plants per land cover type.
                Units: (-)

            Returns
            -------
            min_leaf_area_index : array
                Minimum one-sided leaf area index per lancover type. Units: (-)

            """
            min_leaf_area_index = 0.1 * frac_decid_plant + (1 - frac_decid_plant) * \
                red_factor_evergreen * max_leaf_area_index
            return min_leaf_area_index

        for i in range(len(parameters_lai)):
            parameters_lai.loc[i, 'min_leaf_area_index'] = \
                minimum_leaf_area_index(
                    parameters_lai.loc[i, 'max_leaf_area_index'],
                    parameters_lai.loc[i, 'frac_decid_plant'],
                    parameters_lai.loc[i, 'red_factor_evergreen'])

        # Land cover type over all grid cell
        land_cover = self.static_data.land_cover

        # Initial days per land-cover type over all grid cell, Units: day
        self.initial_days = np.zeros((land_cover.shape))
        self.initial_days.fill(np.nan)
        for i in range(len(parameters_lai)):
            self.initial_days[land_cover[:, :] == parameters_lai.loc[i, 'Number']] = \
                parameters_lai.loc[i, 'initial_days']

        # Maximum Leaf area index over all grid cell,  Units: (-)
        self.max_leaf_area_index = np.zeros((land_cover.shape))
        self.max_leaf_area_index.fill(np.nan)
        for i in range(len(parameters_lai)):
            self.max_leaf_area_index[land_cover[:, :] == parameters_lai.loc[i, 'Number']] = \
                parameters_lai.loc[i, 'max_leaf_area_index']

        # Minimum Leaf area index  over all grid cell, Units: (-)
        self.min_leaf_area_index = np.zeros((land_cover.shape))
        self.min_leaf_area_index.fill(np.nan)
        for i in range(len(parameters_lai)):
            self.min_leaf_area_index[land_cover[:, :] == parameters_lai.loc[i, 'Number']] = \
                parameters_lai.loc[i, 'min_leaf_area_index']

    def get_daily_leaf_area_index(self, days, growth_status,
                                  cum_precipitation):
        """
        Compute leaf area index.

        Parameters
        ----------
        days : array
            Days since start of leaf area index profile (counter for days with
            growing conditions), Units: day.
            This variable gets updated per time step.
        growth_status : array
            Growth status per grid cell shows whether a specific land cover
            is (not) growing (value=0) or fully grown (value=1).
            Initially all landcovers are not growing
            This variable gets updated per time step..
        cum_precipitation : array
             cummulative precipitation per time step. unit( mm/d)

        Returns
        -------
        Outputs (tuple of arrays) from the get_daily_leaf_area_index are.
            0 = daily leaf area index,
            1 = days since start,
            2 = growth status,
            3 = cumulative precipitation
        ouput(1-3)  get updated per time step.
        """
        # =====================================================================
        # # Loading in climate forcing
        # =====================================================================
        #  Actual name: Air tempeature, Units: K
        temperature = self.climate_forcing.temperature.sel(time=str(self.date))
        temperature = temperature.tas.values

        #  Actual name: Precipitation, Units:  kg m-2 s-1
        precipitation = self.climate_forcing.precipitation.sel(
            time=str(self.date))

        #   Units conversion 1 kg m-2 s-1 = 86400 mmd-1
        to_mm_per_day = 86400
        precipitation = precipitation.pr.values * to_mm_per_day

        #  Checking negative precipittaion
        check.check_neg_precipitation(precipitation)

        # =====================================================================
        # # Loading in static variables
        # =====================================================================
        # Actual name: Land cover , Units: (-)
        land_cover = self.static_data.land_cover

        # Humid-arid calssification based on Müller Schmied et al. 2021
        humid_arid = self.static_data.humid_arid

        # =====================================================================
        # Empty variable to store Leaf_area index, Units: (-)
        # =====================================================================
        temp_leaf_area_index = np.zeros(land_cover.shape)

        # The function below computes the parallelized leaf area index logic
        daily_leaf_area_index = \
            parallel_leaf_area_index.vectorized_leaf_area_index(
                temperature, growth_status, days, self.initial_days,
                cum_precipitation, precipitation, temp_leaf_area_index,
                self.min_leaf_area_index, self.max_leaf_area_index,
                land_cover, humid_arid)

        return daily_leaf_area_index

    # @staticmethod
    # def user_defined_lai(*args, **kwargs):
    #     """
    #     Calculate user defined lai.

    #     Returns
    #     -------
    #     results : TYPE
    #         DESCRIPTION.

    #     """
    #     # Please delete and write your function here
    #     args = None
    #     kwargs = None
    #     results = "do stuff here" + args + kwargs

    #     return results
