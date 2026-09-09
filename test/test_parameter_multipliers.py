"""Regression tests for the optional C++ calibration multipliers.

Run with: python -m unittest test.test_parameter_multipliers
Uses small synthetic inputs; no climate/static input files are required.
"""

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import xarray as xr

from model.parameter_multipliers import (MULTIPLIER_DESCRIPTIONS,
                                         add_multiplier_defaults)
from model.verticalwaterbalance.waterbalance_vertical_init import VerticalWaterBalance


def vertical_fixture():
    """Five land cells and one ocean cell, with different land-cover classes."""
    shape = (2, 3)
    cover = np.array([[2., 10., 12.], [2., 10., np.nan]])
    def grid(value):
        return np.where(np.isnan(cover), np.nan, value)
    values = dict(gamma=2., pt_coeff_humid_arid=1.26,
                  max_canopy_storage_coefficient=.3, adiabatic_lapse_rate=.006,
                  snow_freeze_temp=273.15, snow_melt_temp=273.15,
                  runoff_frac_builtup=.5, max_daily_pet=15.,
                  critcal_gw_precipitation=12.5, areal_corr_factor=1.,
                  snow_albedo_thresh=3., openwater_albedo=.08)
    params = add_multiplier_defaults(xr.Dataset(
        {k: (("lat", "lon"), grid(v)) for k, v in values.items()}))
    table = pd.DataFrame(dict(
        Number=[2, 10, 12], rooting_depth=[4., 1., 1.],
        albedo=[.07, .25, .23], snow_albedo=[.3, .7, .376],
        emissivity=[.9956, .9932, .9813], **{"degree-day": [3., 5., 4.]},
        max_leaf_area_index=[6., 3., 4.], frac_decid_plant=[.2, .5, .8],
        red_factor_evergreen=[.5, .5, .5], initial_days=[5., 5., 5.]))
    soil_inputs = [grid(.1), grid(100.), grid(1.), grid(3.), grid(20.),
                   grid(.6), grid(1.), grid(.2)]
    static = SimpleNamespace(
        land_surface_water_fraction=xr.Dataset(
            {"contfrac": (("lat", "lon"), grid(100.))}),
        rout_order=pd.DataFrame(np.argwhere(~np.isnan(cover)),
                               columns=["Lat_index_routorder", "Lon_index_routorder"]),
        canopy_snow_soil_parameters=table, land_cover=cover, humid_arid=grid(1.),
        gtopo30_elevation=np.zeros((101,) + shape),
        soil_static_data=lambda: soil_inputs)
    dates = np.arange(np.datetime64("2001-01-01"), np.datetime64("2001-02-10"))
    def forcing(name, value, units):
        data = np.broadcast_to(grid(value), (len(dates),) + shape).copy()
        return xr.Dataset({name: (("time", "lat", "lon"), data,
                                  {"units": units})}, coords={"time": dates})
    climate = SimpleNamespace(
        precipitation=forcing("pr", 20., "mm/day"),
        temperature=forcing("tas", 278.15, "K"),
        down_shortwave_radiation=forcing("rsds", 200., "W m-2"),
        down_longwave_radiation=forcing("rlds", 300., "W m-2"))
    return SimpleNamespace(static_data=static, climate_forcing=climate,
                           lat_length=2, lon_length=3), params, grid


def step(model, grid, date="2001-01-01"):
    model.calculate(np.datetime64(date), grid(1.), grid(1.), grid(0.),
                    grid(0.), grid(1.))
    return {k: v.copy() for k, v in model.fluxes.items()}


class TestMultipliers(unittest.TestCase):
    def test_defaults_preserve_mask_and_existing_values(self):
        ds = xr.Dataset({"gamma": (("lat", "lon"), [[1., np.nan]])})
        add_multiplier_defaults(ds)
        for name in MULTIPLIER_DESCRIPTIONS:
            np.testing.assert_array_equal(ds[name], [[1., np.nan]])
        ds.root_depth_multiplier.values[0, 0] = 2.
        add_multiplier_defaults(ds)
        self.assertEqual(ds.root_depth_multiplier.values[0, 0], 2.)

    def test_static_scaling_and_lai_minimum(self):
        forcing, params, grid = vertical_fixture()
        baseline = VerticalWaterBalance(forcing, SimpleNamespace(global_params=params))
        for name in ("root_depth_multiplier", "LAI_mult", "degree_day_factor_mult",
                     "rg_max_mult", "gw_factor_mult"):
            params[name].values[:] = grid(2.)
        scaled = VerticalWaterBalance(forcing, SimpleNamespace(global_params=params))
        for name in ("max_soil_water_content", "degreeday", "max_groundwater_recharge"):
            np.testing.assert_array_equal(getattr(scaled, name), getattr(baseline, name) * 2.)
        np.testing.assert_array_equal(scaled.groundwater_recharge_factor, grid(.95))
        np.testing.assert_array_equal(scaled.lai_param.max_leaf_area_index,
                                      baseline.lai_param.max_leaf_area_index * 2.)
        # Evergreen class: 0.1 * 0.2 + 0.8 * 0.5 * (6 * 2) = 4.82.
        self.assertAlmostEqual(scaled.lai_param.min_leaf_area_index[0, 0], 4.82)
        # Reinitializing must not compound multipliers or change static inputs.
        repeated = VerticalWaterBalance(forcing, SimpleNamespace(global_params=params))
        np.testing.assert_array_equal(repeated.max_groundwater_recharge,
                                      scaled.max_groundwater_recharge)

    def test_precipitation_and_land_only_radiation(self):
        forcing, params, grid = vertical_fixture()
        base = VerticalWaterBalance(forcing, SimpleNamespace(global_params=params))
        baseline = step(base, grid)
        params.net_radiation_mult.values[:] = grid(2.)
        params.precip_mult.values[:] = grid(.5)
        changed = VerticalWaterBalance(forcing, SimpleNamespace(global_params=params))
        result = step(changed, grid)
        np.testing.assert_array_equal(result["daily_precipitation"], grid(10.))
        np.testing.assert_array_equal(result["netrad"], baseline["netrad"] * 2.)
        np.testing.assert_array_equal(result["openwater_PET"], baseline["openwater_PET"])
        step(changed, grid, "2001-01-02")
        np.testing.assert_array_equal(changed.fluxes["daily_precipitation"], grid(10.))
        np.testing.assert_array_equal(forcing.climate_forcing.precipitation.pr[0], grid(20.))

    def test_nonunity_root_snow_and_recharge_affect_fluxes(self):
        for multiplier, output in [("root_depth_multiplier", "surface_runoff"),
                                   ("degree_day_factor_mult", "snm"),
                                   ("gw_factor_mult", "groundwater_recharge"),
                                   ("rg_max_mult", "groundwater_recharge")]:
            with self.subTest(multiplier=multiplier):
                results = []
                for value in (1., .5):
                    forcing, params, grid = vertical_fixture()
                    params[multiplier].values[:] = grid(value)
                    model = VerticalWaterBalance(forcing, SimpleNamespace(global_params=params))
                    model.soil_water_content[:] = grid(90.)
                    model.snow_water_storage[:] = grid(100.)
                    model.snow_water_storage_subgrid[:] = grid(100.)
                    results.append(step(model, grid)[output])
                self.assertFalse(np.array_equal(results[0], results[1], equal_nan=True))


class RoutingBoundary(Exception):
    """Stop the coordinator after monthly loading, before routing begins."""


def load_lateral(path):
    # Configuration normally parses command-line arguments at import time.
    import controller
    config = SimpleNamespace(SUBTRACT_USE=True, DELAYED_USE=False)
    spec = importlib.util.spec_from_file_location("multiplier_lateral_test", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"controller.configuration_module": config}), \
            patch.object(controller, "configuration_module", config, create=True):
        spec.loader.exec_module(module)
    return module


def abstraction_fixture():
    class State(SimpleNamespace):
        @property
        def get_river_prop(self):
            raise RoutingBoundary
    source = xr.Dataset({k: (("time", "lat", "lon"), [[[31.e9, -62.e9]]])
                         for k in ("pnag", "pnas", "atotusegw", "atotusesw",
                                   "pirrwwsw", "pirrusesw")},
                        coords={"time": [np.datetime64("2001-01-01")]})
    params = xr.Dataset({k: (("lat", "lon"), [[2., .5]]) for k in
                         ("net_abstraction_surfacewater_mult",
                          "net_abstraction_groundwater_mult")})
    received = []
    def aggregate(lake, reservoir, netabs):
        received.append(netabs.copy())
        return netabs.copy()
    state = State(cell_area=np.ones((1, 2)), parameters=params,
                  potential_net_abstraction=source, actual_net_abstraction=source,
                  glolake_area=np.zeros((1, 2)), glores_area=np.zeros((1, 2)),
                  get_aggr_func=SimpleNamespace(aggregate_riparian_netpotabs=aggregate,
                                                glwdunits=np.ones((1, 2))))
    return state, received


def abstraction_step(module, state, day=1, run_calib=False):
    args = [np.ones((1, 2)) for _ in range(9)]
    with unittest.TestCase().assertRaises(RoutingBoundary):
        module.LateralWaterBalance.calculate(
            state, *args, np.datetime64(f"2001-01-{day:02d}"),
            [np.datetime64("2001-01-01")], np.zeros((1, 2)),
            np.zeros((1, 2)), run_calib)


class TestAbstractionMultipliers(unittest.TestCase):
    def test_scaling_before_aggregation_and_no_daily_compounding(self):
        path = Path(__file__).resolve().parents[1] / "model/lateralwaterbalance/waterbalance_lateral.py"
        module = load_lateral(path)
        for run_calib in (False, True):
            state, received = abstraction_fixture()
            abstraction_step(module, state, run_calib=run_calib)
            np.testing.assert_array_equal(received[0], [[62.e9, -31.e9]])
            np.testing.assert_array_equal(state.potential_net_abstraction_gw, [[2., -1.]])
            np.testing.assert_array_equal(state.potential_net_abstraction_sw, [[2., -1.]])
            np.testing.assert_array_equal(state.monthly_potential_net_abstraction_sw, [[62., -31.]])
            abstraction_step(module, state, day=2, run_calib=run_calib)
            self.assertEqual(len(received), 1)
            np.testing.assert_array_equal(state.potential_net_abstraction_sw, [[2., -1.]])
            np.testing.assert_array_equal(state.potential_net_abstraction.pnas[0], [[31.e9, -62.e9]])


if __name__ == "__main__":
    unittest.main()
