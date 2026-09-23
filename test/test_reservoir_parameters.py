"""Reservoir parameter defaults and equation-based calibration checks."""

import inspect
from pathlib import Path
import tempfile
import unittest

import numpy as np
import xarray as xr

from add_reservoir_parameters_to_watergap_params import update_reservoir_parameters
from model.reservoir_parameters import (
    add_reservoir_defaults, HANASAKI_DEFAULTS, RESERVOIR_PARAMETER_DESCRIPTIONS,
)
from model.lateralwaterbalance.reservoir_release_hanasaki import hanasaki_res_reslease
from model.lateralwaterbalance.routing import river_routing
from test.test_reservoir_operation import reservoir_fixture, routing_fixture


def release_fixture():
    values = reservoir_fixture()
    return {name: values[name] for name in
            inspect.signature(hanasaki_res_reslease.py_func).parameters
            if name in values}


class TestReservoirParameterFiles(unittest.TestCase):
    def test_existing_values_preserved_and_default_mask(self):
        ds = xr.Dataset({
            'gamma': (('lat', 'lon'), [[2., np.nan]]),
            'P1_scaling': (('lat', 'lon'), [[.3, np.nan]]),
            'P2_scaling': (('lat', 'lon'), [[.6, np.nan]]),
            'P1_hanasaki': (('lat', 'lon'), [[.7, np.nan]]),
        })
        add_reservoir_defaults(ds)
        for name, expected in [('P1_scaling', .3), ('P2_scaling', .6),
                               ('P3_scaling', 1.), ('P1_hanasaki', .7),
                               ('P2_hanasaki', .5), ('P3_hanasaki', .5)]:
            np.testing.assert_array_equal(ds[name], [[expected, np.nan]])
        original = ds.copy(deep=True)
        add_reservoir_defaults(ds)
        xr.testing.assert_identical(ds, original)

    def test_file_update_preserves_values_and_is_repeatable(self):
        ds = xr.Dataset({
            'gamma': (('lat', 'lon'), [[2., np.nan]], {'units': '-'}),
            'other': (('lat', 'lon'), [[7., 8.]], {'units': 'km3'}),
            **{f'P{i}_scaling': (('lat', 'lon'), [[i / 10, np.nan]])
               for i in range(1, 7)},
        }, coords={'lat': [1.], 'lon': [2., 3.]}, attrs={'source': 'original'})
        with tempfile.TemporaryDirectory() as tmp:
            source, dest = Path(tmp) / 'source.nc', Path(tmp) / 'updated.nc'
            ds.to_netcdf(source)
            original_bytes = source.read_bytes()
            update_reservoir_parameters(source, dest)
            self.assertEqual(source.read_bytes(), original_bytes)
            with xr.open_dataset(dest) as updated:
                migrated = updated.load()
            xr.testing.assert_identical(migrated[['gamma', 'other']], ds[['gamma', 'other']])
            for i in range(1, 7):
                np.testing.assert_array_equal(migrated[f'P{i}_scaling'], [[i / 10, np.nan]])
            for i, expected in enumerate(HANASAKI_DEFAULTS, 1):
                np.testing.assert_array_equal(migrated[f'P{i}_hanasaki'], [[expected, np.nan]])
            for name in RESERVOIR_PARAMETER_DESCRIPTIONS:
                self.assertEqual(migrated[name].attrs['units'], '-')
            update_reservoir_parameters(dest, dest)
            with xr.open_dataset(dest) as repeated:
                xr.testing.assert_identical(repeated, migrated)


class TestHanasakiCalibration(unittest.TestCase):
    def test_annual_storage_coefficient_and_update_date(self):
        p = release_fixture()
        release, coefficient = hanasaki_res_reslease(**p, P1_hanasaki=.5)
        self.assertAlmostEqual(coefficient, 1.)  # 5 / (10 * 0.5)
        self.assertAlmostEqual(release, 100.)
        p['simulation_momth_day'] = np.array([7, 2])
        release, coefficient = hanasaki_res_reslease(**p, P1_hanasaki=.5)
        self.assertEqual(coefficient, p['k_release'])
        self.assertAlmostEqual(release, 10.)
        p['simulation_momth_day'] = np.array([7, 1])
        p['storage'] = .5
        self.assertEqual(hanasaki_res_reslease(**p, P1_hanasaki=.5)[1], .1)

    def test_irrigation_factor_changes_threshold_and_release(self):
        p = release_fixture()
        p['reservoir_type'] = 1
        p['mean_annual_demand'][:] = 60. * 31536000  # m3/year
        p['monthly_demand'][:] = 90. * 86400 * 31 / 1e9  # km3/month
        # Demand 60 m3/s exceeds 0.5*100, but is below 0.8*100.
        release, coefficient = hanasaki_res_reslease(**p, P2_hanasaki=.5)
        self.assertAlmostEqual(release, coefficient * .5 * 100 * (1 + 90 / 60))
        release, coefficient = hanasaki_res_reslease(**p, P2_hanasaki=.8)
        self.assertAlmostEqual(release, coefficient * (100 + 90 - 60))
        # Both .4 and .5 use the high-demand branch, with different factors.
        release, coefficient = hanasaki_res_reslease(**p, P2_hanasaki=.4)
        self.assertAlmostEqual(release, coefficient * .4 * 100 * (1 + 90 / 60))
        p['reservoir_type'] = 2
        self.assertEqual(hanasaki_res_reslease(**p, P2_hanasaki=.4),
                         hanasaki_res_reslease(**p, P2_hanasaki=.8))

    def test_capacity_threshold_blending_and_flow_units(self):
        p = release_fixture()
        # A capacity of 10 km3 and annual volume of 40 km3 gives c = 0.25.
        p['mean_annual_inflow'] = 40 * 1e9 / 31536000
        p['inflow_to_swb'] = .01  # km3/day
        for threshold in (.2, .25, .5, 1.):
            release, coefficient = hanasaki_res_reslease(**p, P3_hanasaki=threshold)
            weight = min(1., (.25 / threshold)**2)
            expected = (weight * coefficient * p['mean_annual_inflow'] +
                        (1 - weight) * .01 * 1e9 / 86400)
            self.assertAlmostEqual(release, expected)

    def test_invalid_hanasaki_values_fail_clearly(self):
        for name in ('P1_hanasaki', 'P2_hanasaki', 'P3_hanasaki'):
            for value in (0., -1., np.nan, np.inf):
                with self.subTest(name=name, value=value):
                    with self.assertRaisesRegex(ValueError, 'finite and strictly positive'):
                        hanasaki_res_reslease(**release_fixture(), **{name: value})

    def test_routing_uses_each_hanasaki_grid_only_for_hanasaki(self):
        for name, candidate in [('P1_hanasaki', .6), ('P2_hanasaki', .8),
                                ('P3_hanasaki', 1.)]:
            for algorithm in (0, 1):
                with self.subTest(name=name, algorithm=algorithm):
                    p = routing_fixture()
                    p['res_operation_algorithm'] = algorithm
                    p['glores_type'][:] = 1.
                    p['mean_annual_inflow_res'][:] = 1000.
                    p['mean_annual_demand_res'][:] = 1000. * 31536000
                    p['monthly_potential_net_abstraction_sw'][:] = 600. * 86400 * 31 / 1e9
                    baseline = river_routing(**p)[27].item()
                    # Routing mutates states; rebuild all inputs for the candidate.
                    changed = routing_fixture()
                    for field in ('res_operation_algorithm', 'glores_type',
                                  'mean_annual_inflow_res', 'mean_annual_demand_res',
                                  'monthly_potential_net_abstraction_sw'):
                        changed[field] = p[field]
                    changed[name][:] = candidate
                    result = river_routing(**changed)[27].item()
                    if algorithm == 1:
                        self.assertNotAlmostEqual(result, baseline)
                    else:
                        self.assertAlmostEqual(result, baseline)


if __name__ == '__main__':
    unittest.main()
