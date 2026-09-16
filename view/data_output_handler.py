# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
"""Buffer selected daily outputs or aggregate monthly outputs during simulation."""

import datetime as dt

import numpy as np
import pandas as pd
import xarray as xr

from misc import watergap_version
from view import output_var_info as var_info


MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def next_model_day(date):
    """Exclusive interval end in the model's fixed 365-day calendar."""
    result = date + pd.Timedelta(days=1)
    if result.month == 2 and result.day == 29:
        result += pd.Timedelta(days=1)
    return result


class OutputVariable:
    """One output frequency, with at most one year of output in memory."""

    def __init__(self, variable_name, create, grid_coords, frequency="Daily"):
        if frequency not in {"Daily", "Monthly"}:
            raise ValueError(f"Unsupported output frequency: {frequency}")
        self.variable_name = variable_name
        self.create = create
        self.frequency = frequency
        self.aggregation = var_info.monthly_aggregation(variable_name)
        if not create:
            return
        self.grid_coords = grid_coords
        self._dates = pd.DatetimeIndex(grid_coords["time"].values)
        self._dates = self._dates[~((self._dates.month == 2) & (self._dates.day == 29))]
        self._month = None
        self._accumulator = None
        self._count = 0
        self._initialize_year(self._dates[0].year)

    def _initialize_year(self, year):
        """Allocate only requested output time steps; never daily monthly buffers."""
        self._year = year
        dates = self._dates[self._dates.year == year]
        coords = {name: self.grid_coords[name].values for name in ("lat", "lon")}
        dims = ["lat", "lon"]
        if self.variable_name != "smax":
            times = (dates.to_period("M").unique().to_timestamp()
                     if self.frequency == "Monthly" else dates)
            coords = {"time": times, **coords}
            dims.insert(0, "time")
            self._time_index = {date: index for index, date in enumerate(times)}
        if self.variable_name == "get_neighbouring_cells_map":
            dims.append("dim2")
            coords["dim2"] = np.arange(2)
            data = np.zeros(tuple(len(coords[d]) for d in dims), dtype=np.int32)
        else:
            data = np.full(tuple(len(coords[d]) for d in dims), np.nan,
                           dtype=np.float32)
        self.data = xr.Dataset({self.variable_name: (dims, data)}, coords=coords)
        info = var_info.modelvars[self.variable_name]
        attrs = {
            "standard_name": self.variable_name,
            "long_name": info["long"],
            "units": info["unit"],
            "unit_conversion_info": (
                "If the variable needs conversion to volumetric units (L³ T⁻¹ or L³), "
                "use watergap22e_continentalarea.nc4 (water density is 1 kg per dm³);"
                "otherwise, conversion is not needed."),
        }
        if self.frequency == "Monthly" and self.variable_name != "smax":
            attrs["aggregation"] = self.aggregation
            if self.aggregation == "last":
                attrs["comment"] = "Cell indices from the last simulated day of each month"
                attrs["cell_methods"] = "time: point"
            else:
                attrs["cell_methods"] = f"time: {self.aggregation}"
            if self.aggregation == "sum":
                attrs["units"] = "kg m-2"
            bounds = []
            for time in times:
                month_dates = dates[(dates.year == time.year) & (dates.month == time.month)]
                bounds.append([month_dates[0], next_model_day(month_dates[-1])])
            self.data["time_bnds"] = (("time", "bnds"),
                                      np.asarray(bounds, dtype="datetime64[ns]"))
            self.data.time.attrs["bounds"] = "time_bnds"
        self.data[self.variable_name].attrs = attrs
        self.data.attrs = {
            "title": "WaterGAP " + watergap_version.__version__ + " model output",
            "institution": watergap_version.__institution__,
            "contact": "nyenah@em.uni-frankfurt.de",
            "model_version": "WaterGAP " + watergap_version.__version__,
            "reference": watergap_version.__reference__,
            "license": "LGPL-3.0",
            "output_frequency": self.frequency.lower(),
            "Creation_date": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def finalize_month(self):
        """Flush a full or partial month, preserving missing cells as NaN."""
        if self._month is None:
            return
        result = self._accumulator
        if self.aggregation == "mean":
            result = result / self._count
        index = self._time_index[self._month]
        self.data[self.variable_name].values[index] = result
        self.data["time_bnds"].values[index] = [
            self._first_date.to_datetime64(),
            next_model_day(self._last_date).to_datetime64(),
        ]
        self._month = None
        self._accumulator = None
        self._count = 0

    def write_daily_output(self, array, year, month, day):
        """Consume one model day, retaining it only if daily output is selected."""
        if not self.create or (month == 2 and day == 29):
            return
        date = pd.Timestamp(year=year, month=month, day=day)
        if self._year != year:
            self.finalize_month()
            self._initialize_year(year)
        if self.variable_name == "smax":
            self.data[self.variable_name].values[:] = array
        elif self.frequency == "Daily":
            self.data[self.variable_name].values[self._time_index[date]] = array
        else:
            month_start = date.replace(day=1)
            if self._month != month_start:
                self.finalize_month()
                self._month = month_start
                self._first_date = date
                self._accumulator = np.array(array, dtype=np.float64, copy=True)
            elif self.aggregation == "last":
                self._accumulator[:] = array
            else:
                self._accumulator += array
            self._count += 1
            self._last_date = date
            if day == MONTH_LENGTHS[month - 1] or date == self._dates[-1]:
                self.finalize_month()
