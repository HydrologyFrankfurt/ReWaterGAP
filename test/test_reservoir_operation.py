"""Synthetic checks for reservoir configuration, inputs, and both algorithms."""

import copy
import inspect
import importlib.util
from types import SimpleNamespace
from unittest.mock import patch
import json
from pathlib import Path
import tempfile
import unittest
import sys

import numpy as np
import xarray as xr

from model.lateralwaterbalance.routing import river_routing
from controller.reservoir_options import reservoir_options
from controller.reservoir_inputs import load_reservoir_inputs
from misc.get_reservoir_start_month import find_reservoir_start_month
from model.lateralwaterbalance.reservoir_regulated_lakes import (
    reservoir_regulated_lake_water_balance)
from model.lateralwaterbalance.reservoir_release_scaling import scaling_res_reslease
from model.lateralwaterbalance.reservoir_release_hanasaki import hanasaki_res_reslease


def reservoir_fixture():
    """One reservoir, with zero evaporation/abstraction and no downstream demand."""
    return dict(
        rout_order=np.array([[0, 0]]), routflow_looper=0,
        outflow_cell=np.array([[0, 0]]), storage=5., stor_capacity=10.,
        precipitation=0., openwater_pot_evap=0., aridity=0,
        drainage_direction=1, inflow_to_swb=.01,
        groundwater_recharge_constant=0., reservior_area=np.array([[1.]]),
        reduction_exponent_res=1., areal_corr_factor=1., res_start_month=7,
        simulation_momth_day=np.array([7, 1]), k_release=.1, reservoir_type=2,
        allocation_coeff=np.zeros((1, 5)), monthly_demand=np.zeros((1, 1)),
        mean_annual_demand=np.zeros((1, 1)), mean_annual_inflow=100.,
        glolake_area=0., accumulated_unsatisfied_potential_netabs_sw=0.,
        accumulated_unsatisfied_potential_netabs_glolake=0., num_days_in_month=31,
        all_reservoir_and_regulated_lake_area=np.ones((1, 1)),
        reg_lake_redfactor_firstday=1., minstorage_volume=1e-15,
        res_inflow_past_30days=np.zeros(30), counter_for_mean_30days=0,
        P1_res=1., P2_res=1., P3_res=1., P4_res=.4, P5_res=.9, P6_res=1.)


def routing_fixture():
    p={name:np.zeros((1,1)) for name in inspect.signature(river_routing.py_func).parameters}
    for name in ['rout_order','outflow_cell']:
        p[name]=np.array([[0,0]],dtype=np.int64)
    p.update(neigbourcells=np.zeros((1,16),dtype=np.int64),
             neighbourcells_outflowcell=np.zeros((1,16),dtype=np.int64),
             neighbouring_cells_map=np.zeros((1,1,2),dtype=np.int64),
             allocation_coeff=np.zeros((1,5)), current_mon_day=np.array([7,1]),
             res_inflow_past_30days=np.zeros((30,1,1)),
             counter_for_mean_30days=np.zeros((1,1),dtype=np.int32))
    for name in ['subtract_use_option','neighbouringcell_option','delayed_use_option']:
        p[name]=False
    p['reservoir_operation']=True
    p['num_days_in_month']=31
    for name,value in dict(drainage_direction=1.,glores_storage=5.,glores_capacity=10.,
         glores_area=1., surface_runoff=.01, gw_dis_coeff=.01, swb_outflow_coeff=.01,
         reduction_exponent_lakewet=1.,reduction_exponent_res=1.,lake_out_exp=1.,wetland_out_exp=1.,
         areal_corr_factor=1.,stat_corr_fact=1.,river_length=1.,river_bottom_width=.01,
         roughness=.03,roughness_multiplier=1.,river_slope=.001,
         glores_startmonth=7.,k_release=.1,glores_type=2.,mean_annual_inflow_res=100.,
         all_reservoir_and_regulated_lake_area=1., reg_lake_redfactor_firstday=1.,
         landwaterfrac_excl_glolake_res=1.,cell_area=100.,
         P1_reservoir=1.,P2_reservoir=1.,P3_reservoir=1.,P4_reservoir=.4,P5_reservoir=.9,P6_reservoir=1.).items():
        p[name][:]=value
    return p


class TestReservoirAlgorithms(unittest.TestCase):
    def test_routing_selects_algorithm_and_uses_july_p4(self):
        results = []
        for algorithm in (0, 1):
            p = routing_fixture()
            p['res_operation_algorithm'] = algorithm
            result = river_routing(**p)
            self.assertGreater(result[27].item(), 0.)
            self.assertAlmostEqual(result[4].item() + result[27].item(), 5.)
            self.assertEqual(result[40].item(), int(algorithm == 0))
            results.append(result[27].item())
            # July must use P4, while Hanasaki is independent of all P values.
            p = routing_fixture()
            p['res_operation_algorithm'] = algorithm
            p['P4_reservoir'] *= 2
            changed = river_routing(**p)
            self.assertAlmostEqual(changed[27].item(), results[-1] * (2 if algorithm == 0 else 1))
        self.assertNotEqual(*results)

    def test_scaling_matches_release_and_advances_history(self):
        p = reservoir_fixture()
        reference_history = np.zeros(30)
        for day in range(35):
            reference, counter = scaling_res_reslease(
                p['storage'] + p['inflow_to_swb'], p['stor_capacity'],
                p['simulation_momth_day'], p['mean_annual_inflow'],
                p['inflow_to_swb'], reference_history, day,
                1., 1., 1., .4, .9, 1.)
            result = reservoir_regulated_lake_water_balance(**p, res_operation_algorithm=0)
            self.assertAlmostEqual(result[1], reference * 86400 / 1e9)
            self.assertAlmostEqual(result[0] + result[1], p['storage'] + p['inflow_to_swb'])
            self.assertEqual(result[7], counter)
            self.assertTrue(np.isfinite(result[3]))
            np.testing.assert_array_equal(p['res_inflow_past_30days'], reference_history)
            p['storage'] = result[0]
            p['counter_for_mean_30days'] = result[7]
            p['inflow_to_swb'] += .001

    def test_hanasaki_matches_reference_and_preserves_scaling_history(self):
        p = reservoir_fixture()
        for reservoir_type in (1, 2):
            p['reservoir_type'] = reservoir_type
            reference, coefficient = hanasaki_res_reslease(
                p['storage'] + p['inflow_to_swb'], p['stor_capacity'],
                p['res_start_month'], p['simulation_momth_day'], p['k_release'],
                p['reservoir_type'], p['rout_order'], p['outflow_cell'], 0,
                p['reservior_area'], p['allocation_coeff'], p['monthly_demand'],
                p['mean_annual_demand'], p['mean_annual_inflow'], p['inflow_to_swb'],
                31, p['all_reservoir_and_regulated_lake_area'])
            result = reservoir_regulated_lake_water_balance(**p, res_operation_algorithm=1)
            self.assertAlmostEqual(result[1], reference * 86400 / 1e9)
            self.assertEqual(result[3], coefficient)
            self.assertEqual(result[7], 0)
            np.testing.assert_array_equal(p['res_inflow_past_30days'], np.zeros(30))
            p['P4_res'] = 99.
            changed = reservoir_regulated_lake_water_balance(**p, res_operation_algorithm=1)
            np.testing.assert_array_equal(result, changed)


class TestReservoirConfiguration(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path('Config_ReWaterGAP.json').read_text())

    def test_explicit_selection_ignores_parameter_filename(self):
        options = self.config['RuntimeOptions'][0]['SimulationOption']['ReservoirOperation']
        options.update(res_operation_algorithm='hanasaki', reservoir_forcing='w5e5')
        self.assertEqual(reservoir_options(self.config)[:2], ('hanasaki', 'w5e5'))

    def test_legacy_config_defaults_to_scaling(self):
        del self.config['RuntimeOptions'][0]['SimulationOption']['ReservoirOperation']
        section = self.config['RuntimeOptions'][5]
        section['Calibrate WaterGAP'] = section.pop('CalibrateWaterGAP')
        del section['Calibrate WaterGAP']['calib_forcing']
        self.assertEqual(reservoir_options(self.config)[:2], ('scaling', 'era5'))

    def test_invalid_choices_fail(self):
        for field, value in (('res_operation_algorithm', 'invalid'),
                             ('res_operation_algorithm', 'hanaski'),
                             ('reservoir_forcing', 'invalid')):
            config = copy.deepcopy(self.config)
            config['RuntimeOptions'][0]['SimulationOption']['ReservoirOperation'][field] = value
            with self.assertRaises(ValueError):
                reservoir_options(config)

    def test_standard_calibration_preserves_algorithm_settings(self):
        # Configuration editing does not require the optional sklearn pipeline.
        import calibration
        merge = SimpleNamespace()
        spec = importlib.util.spec_from_file_location('reservoir_calibration_test',
                                                      'run_calibration.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'calibration.merge_parameters': merge}), \
                patch.object(calibration, 'merge_parameters', merge, create=True):
            spec.loader.exec_module(module)
        simulation = self.config['RuntimeOptions'][0]['SimulationOption']
        expected = copy.deepcopy(simulation['ReservoirOperation'])
        module.CalibrateStations().update_config_values(simulation)
        self.assertEqual(simulation['ReservoirOperation'], expected)


class TestReservoirInputs(unittest.TestCase):
    def test_forcing_selection_keeps_geometry_and_scaling_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / 'reservoir_regulated_lake'
            base.mkdir()
            coords = dict(time=[0], lat=[1.], lon=[2.])
            original = xr.Dataset({
                k: (('time', 'lat', 'lon'), [[[value]]]) for k, value in
                [('mean_inflow', 10.), ('mean_nus', 20.), ('startmonth', 3.),
                 ('reservoir_type', 2.), ('reservoir_capacity', 999.)]}, coords=coords)
            original.to_netcdf(base / 'original.nc')
            # Scaling must not need a forcing directory.
            xr.testing.assert_identical(
                load_reservoir_inputs(root, 'scaling', 'era5', base), original)
            for forcing, value in [('era5', 100.), ('w5e5', 200.)]:
                directory = base / f'reservoir_routing_{forcing}'
                directory.mkdir()
                names = dict(mean_inflow=f'watergap_22e_{forcing}_mean_inflow.nc4',
                             mean_nus=f'watergap_22e_{forcing}_mean_nus.nc4',
                             startmonth=('watergap_22e_era5_startmonth.nc' if forcing == 'era5'
                                         else 'watergap_22e_startmonth_w5e5.nc'))
                for variable, filename in names.items():
                    ds = original[[variable]].copy(deep=True)
                    ds[variable].values[:] = value if variable != 'startmonth' else 7.
                    ds.to_netcdf(directory / filename)
                # A preprocessing file is deliberately unreadable by NetCDF.
                (directory / f'watergap_22e_{forcing}_monthly_mean_inflow.nc4').write_text('ignored')
                result = load_reservoir_inputs(root, 'hanasaki', forcing, base)
                self.assertEqual(result.mean_inflow.item(), value)
                self.assertEqual(result.startmonth.item(), 7.)
                xr.testing.assert_identical(result.reservoir_capacity, original.reservoir_capacity)
                wrong_grid = original[['mean_inflow']].assign_coords(lon=[3.])
                wrong_grid.to_netcdf(directory / names['mean_inflow'])
                with self.assertRaises(ValueError):
                    load_reservoir_inputs(root, 'hanasaki', forcing, base)
                original[['mean_inflow']].to_netcdf(directory / names['mean_inflow'])
                (directory / names['mean_nus']).unlink()
                with self.assertRaisesRegex(FileNotFoundError, forcing):
                    load_reservoir_inputs(root, 'hanasaki', forcing, base)


class TestReservoirStartMonth(unittest.TestCase):
    def test_wraparound_separate_dry_spells_and_no_dry_months(self):
        monthly = np.full((12, 1, 5), 20.)
        monthly[[10, 11, 0, 1], 0, 0] = 0.  # November-February
        monthly[[1, 2, 3, 6, 8, 9], 0, 1] = 0.  # February-April wins
        monthly[:, 0, 2] = 10.  # No dry season: January
        monthly[:, 0, 3] = np.nan
        annual = np.array([[10., 10., 10., 10., 0.]])
        result = find_reservoir_start_month(monthly, annual, np.full((1, 5), np.nan))
        np.testing.assert_array_equal(result, [[11., 2., 1., np.nan, 1.]])


class TestReservoirRestart(unittest.TestCase):
    def test_serialized_scaling_history_resumes_same_release(self):
        from test.test_parameter_multipliers import load_lateral
        lateral = load_lateral(Path('model/lateralwaterbalance/waterbalance_lateral.py'))
        spec = importlib.util.spec_from_file_location(
            'reservoir_restart_test', 'model/utility/restart_watergap.py')
        restart = importlib.util.module_from_spec(spec)
        with patch('misc.cli_args.parse_cli', return_value=SimpleNamespace(debug=False)):
            spec.loader.exec_module(restart)
        p = reservoir_fixture()
        p['res_inflow_past_30days'][:12] = np.arange(12) * .001
        p['counter_for_mean_30days'] = 12
        with tempfile.TemporaryDirectory() as tmp:
            writer = restart.RestartState(tmp)
            values = {name: np.zeros((1, 1)) for name in
                      inspect.signature(writer.savestate).parameters}
            values.update(date='2001-07-01', glores_storage=np.array([[p['storage']]]),
                          k_release=np.array([[p['k_release']]]),
                          res_inflow_past_30days=p['res_inflow_past_30days'][:, None, None],
                          counter_for_mean_30days=np.array([[12]], dtype=np.int32))
            writer.savestate(**values)
            saved = writer.load_restart_info('2001-07-01')['lat_bal_states']
            state = SimpleNamespace(res_inflow_past_30days=np.zeros((30, 1, 1)),
                                    counter_for_mean_30days=np.zeros((1, 1), dtype=np.int32))
            lateral.LateralWaterBalance.update_latbal_for_restart(state, saved)
            resumed = copy.deepcopy(p)
            resumed['storage'] = state.glores_storage.item()
            resumed['k_release'] = state.k_release.item()
            resumed['res_inflow_past_30days'] = state.res_inflow_past_30days[:, 0, 0]
            resumed['counter_for_mean_30days'] = state.counter_for_mean_30days.item()
            np.testing.assert_array_equal(
                reservoir_regulated_lake_water_balance(**p),
                reservoir_regulated_lake_water_balance(**resumed))
            # Old snapshots remain readable and start with empty history.
            saved.pop('res_inflow_past_30days')
            saved.pop('counter_for_mean_30days')
            state.res_inflow_past_30days[:] = 0
            state.counter_for_mean_30days[:] = 0
            lateral.LateralWaterBalance.update_latbal_for_restart(state, saved)
            self.assertEqual(state.counter_for_mean_30days.item(), 0)
            np.testing.assert_array_equal(state.res_inflow_past_30days, np.zeros((30, 1, 1)))


if __name__ == '__main__':
    unittest.main()
