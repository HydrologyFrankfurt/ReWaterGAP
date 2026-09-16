"""Regression checks for online monthly aggregation and NetCDF output."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import xarray as xr

import controller
from controller.output_options import output_selections
from view.data_output_handler import OutputVariable
from view.output_var_info import modelvars, monthly_aggregation


def model_dates(start, end):
    dates = pd.date_range(start, end)
    return dates[~((dates.month == 2) & (dates.day == 29))]


def coordinates(start, end):
    return xr.Dataset(coords={"time": model_dates(start, end),
                              "lat": [1.], "lon": [2., 3.]}).coords


def writer(config, start, end, output_dir, calibration=False):
    cm = SimpleNamespace(config_file={"FilePath": {"outputDir": str(output_dir)}},
                         output_options=output_selections(config),
                         start=start, end=end, run_calib=calibration)
    spec = importlib.util.spec_from_file_location(
        "output_writer_test", Path(__file__).parents[1] / "view/createandwrite.py")
    module = importlib.util.module_from_spec(spec)
    with patch.object(controller, "configuration_module", cm, create=True):
        spec.loader.exec_module(module)
    # Include extra forcing days: the output must stop at the configured end.
    return module, module.CreateandWritetoVariables(coordinates(start, end[:4] + "-12-31"))


class TestOutputFrequency(unittest.TestCase):
    def test_legacy_and_independent_selections(self):
        groups = [{"LateralWaterBalanceFluxes": {"streamflow": True}}]
        legacy = output_selections({"OutputVariable": groups})
        self.assertTrue(legacy["Daily"]["LateralWaterBalanceFluxes"]["streamflow"])
        self.assertFalse(any(legacy["Monthly"].values()))
        monthly = output_selections({"OutputVariable": {"Monthly": groups}})
        self.assertFalse(any(monthly["Daily"].values()))
        self.assertEqual(monthly["Monthly"], legacy["Daily"])
        with self.assertRaisesRegex(ValueError, "true or false"):
            output_selections({"OutputVariable": [{"LateralWaterBalanceFluxes":
                                                   {"streamflow": "false"}}]})

    def test_365_day_totals_means_missing_and_partial_months(self):
        dates = model_dates("2020-01-30", "2020-03-02")
        for name, method in [("qrd", "sum"), ("dis", "mean"), ("tws", "mean")]:
            with self.subTest(name=name):
                var = OutputVariable(name, True, coordinates(str(dates[0]), str(dates[-1])), "Monthly")
                self.assertEqual(var.data.sizes["time"], 3)
                arrays = []
                for i, date in enumerate(dates):
                    values = np.array([[float(i + 1), np.nan]])
                    arrays.append(values)
                    var.write_daily_output(values, date.year, date.month, date.day)
                daily = xr.DataArray(np.array(arrays), dims=("time", "lat", "lon"),
                                     coords={"time": dates})
                expected = getattr(daily.resample(time="MS"), method)(skipna=False)
                np.testing.assert_allclose(var.data[name].values, expected.values)
                self.assertEqual(var.data[name].attrs["cell_methods"], f"time: {method}")
                np.testing.assert_array_equal(var.data.time_bnds.values,
                    np.array([["2020-01-30", "2020-02-01"],
                              ["2020-02-01", "2020-03-01"],
                              ["2020-03-01", "2020-03-03"]], dtype="datetime64[ns]"))

    def test_year_reset_after_conversion(self):
        var = OutputVariable("qrd", True, coordinates("2019-12-30", "2020-01-02"), "Monthly")
        for date in pd.date_range("2019-12-30", "2020-01-02"):
            var.write_daily_output([[2., np.nan]], date.year, date.month, date.day)
            if date == pd.Timestamp("2019-12-31"):
                np.testing.assert_allclose(var.data.qrd.values[0, 0, 0], 4.)
                var.data.qrd.values[:] *= 100  # Previous year's output unit conversion.
        np.testing.assert_allclose(var.data.qrd.values[0, 0, 0], 4.)
        self.assertEqual(var.data.sizes["time"], 1)
        self.assertEqual(var.data.time.values[0], np.datetime64("2020-01-01"))

    def test_every_year_has_365_days_and_february_has_28(self):
        # Even if a caller supplies Gregorian coordinates/days, omit February 29.
        coords = xr.Dataset(coords={"time": pd.date_range("2020-01-01", "2020-12-31"),
                                    "lat": [1.], "lon": [2., 3.]}).coords
        daily = OutputVariable("qrd", True, coords)
        monthly = OutputVariable("qrd", True, coords, "Monthly")
        for date in pd.date_range("2020-01-01", "2020-12-31"):
            for var in (daily, monthly):
                var.write_daily_output([[1., 1.]], date.year, date.month, date.day)
        self.assertEqual(daily.data.sizes["time"], 365)
        self.assertEqual(monthly.data.qrd.values[1, 0, 0], 28.)
        self.assertEqual(monthly.data.qrd.values[:, 0, 0].sum(), 365.)

    def test_static_and_categorical_outputs(self):
        coords = coordinates("2020-02-27", "2020-02-28")
        static = OutputVariable("smax", True, coords, "Monthly")
        mapping = OutputVariable("get_neighbouring_cells_map", True, coords, "Monthly")
        for day in (27, 28):
            static.write_daily_output([[100., 200.]], 2020, 2, day)
            mapping.write_daily_output(np.full((1, 2, 2), day), 2020, 2, day)
        self.assertNotIn("time", static.data.dims)
        np.testing.assert_array_equal(static.data.smax.values, [[100., 200.]])
        np.testing.assert_array_equal(mapping.data.get_neighbouring_cells_map.values,
                                      np.full((1, 1, 2, 2), 28))
        self.assertEqual(mapping.data.get_neighbouring_cells_map.dtype, np.int32)

    def test_all_variables_have_aggregation(self):
        for name in modelvars:
            self.assertIn(monthly_aggregation(name), {"mean", "sum", "last"})
        self.assertEqual(monthly_aggregation("netrad"), "mean")
        self.assertEqual(monthly_aggregation("river-velocity"), "mean")
        self.assertEqual(monthly_aggregation("atotusegw"), "sum")

    def test_online_conversion_and_written_files(self):
        groups = [
            {"VerticalWaterBalanceFluxes": {"groundwater_recharge_diffuse": True,
                                            "net_rad": True}},
            {"VerticalWaterBalanceStorages": {"maximum_soil_moisture": True}},
            {"LateralWaterBalanceFluxes": {"streamflow": True, "total_runoff": True,
                                           "river_velocity": True}},
            {"LateralWaterBalanceStorages": {"total_water_storage": True}},
        ]
        config = {"OutputVariable": {"Daily": groups, "Monthly": groups}}
        with tempfile.TemporaryDirectory() as directory:
            module, out = writer(config, "2020-02-28", "2020-03-02", directory)
            for date in model_dates("2020-02-28", "2020-03-02"):
                value = np.array([[float(date.day), np.nan]])
                out.verticalbalance_write_daily_var(
                    [{"smax": value * 0 + 100}, {"qrd": value, "netrad": value * 10}],
                    date.year, date.month, date.day)
                out.lateralbalance_write_daily_var(
                    [{"tws": value}, {"dis": value, "qtot": value, "river-velocity": value}],
                    date.year, date.month, date.day)
            out.base_units(np.array([[200., 200.]]), xr.DataArray([[50., 50.]]))
            # Use the serial branch to exercise real NetCDF writes without process mocks.
            with patch.object(module.platform, "system", return_value="Darwin"):
                out.save_netcdf_parallel("2020-03-02")
            self.assertEqual(len(list(Path(directory).glob("*.nc"))), 13)
            for name in ("qrd", "netrad", "dis", "qtot", "river-velocity", "tws"):
                with xr.open_dataset(Path(directory) / f"{name}_2020-03-02.nc") as daily, \
                     xr.open_dataset(Path(directory) / f"{name}_2020-03.nc") as monthly:
                    method = monthly_aggregation(name)
                    expected = getattr(daily[name].resample(time="MS"), method)(skipna=False)
                    if method == "sum":
                        expected *= 86400
                        self.assertEqual(monthly[name].attrs["units"], "kg m-2")
                    np.testing.assert_allclose(monthly[name].values, expected.values, rtol=2e-6)
                    self.assertEqual(monthly.sizes["time"], 2)
                    self.assertEqual(daily.sizes["time"], 3)
            with xr.open_dataset(Path(directory) / "netrad_2020-03.nc") as ds:
                self.assertEqual(ds.netrad.attrs["units"], "W m-2")
                self.assertAlmostEqual(ds.netrad.values[0, 0, 0], 280.)
            with xr.open_dataset(Path(directory) / "river-velocity_2020-03.nc") as ds:
                self.assertAlmostEqual(ds["river-velocity"].values[0, 0, 0], 28. * 1000 / 86400)
            with xr.open_dataset(Path(directory) / "tws_2020-03.nc") as ds:
                self.assertAlmostEqual(ds.tws.values[0, 0, 0], 28. * 1e4)

    def test_monthly_only_has_no_daily_buffers_or_files(self):
        config = {"OutputVariable": {"Monthly": [
            {"LateralWaterBalanceFluxes": {"streamflow": True}}]}}
        with tempfile.TemporaryDirectory() as directory:
            module, out = writer(config, "2020-02-01", "2020-02-28", directory)
            self.assertFalse(out.lb_fluxes)
            var = out.monthly["LateralWaterBalanceFluxes"]["dis"]
            self.assertEqual(var.data.sizes["time"], 1)
            for day in range(1, 29):
                out.lateralbalance_write_daily_var([{}, {"dis": [[1., 2.]]}], 2020, 2, day)
            out.base_units(np.ones((1, 2)), xr.DataArray([[100., 100.]]))
            with patch.object(module.platform, "system", return_value="Darwin"):
                out.save_netcdf_parallel("2020-02-28")
            self.assertEqual([p.name for p in Path(directory).iterdir()], ["dis_2020-02.nc"])
            _, calibration = writer(config, "2020-02-01", "2020-02-28", directory, True)
            self.assertEqual(set(calibration.lb_fluxes), {"dis", "pot_cell_runoff"})
            self.assertFalse(any(calibration.monthly.values()))

    def test_write_errors_propagate(self):
        with tempfile.TemporaryDirectory() as directory:
            module, _ = writer({}, "2020-01-01", "2020-01-01", directory)
            with self.assertRaises((PermissionError, FileNotFoundError)):
                module.write_to_netcdf((xr.Dataset({"a": ("x", [1.])}), {},
                                       str(Path(directory) / "missing" / "test.nc")))



if __name__ == "__main__":
    unittest.main()
