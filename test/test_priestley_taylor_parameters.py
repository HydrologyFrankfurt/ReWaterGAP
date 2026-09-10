"""Regression tests for independently calibrated humid and arid PET."""

from types import SimpleNamespace
import unittest

import numpy as np
import xarray as xr

from model.priestley_taylor import select_pt_coeff
from model.verticalwaterbalance.waterbalance_vertical_init import VerticalWaterBalance
from test.test_parameter_multipliers import vertical_fixture, step


class TestPriestleyTaylorParameters(unittest.TestCase):
    def setUp(self):
        self.forcing, self.params, self.grid = vertical_fixture()
        self.climate = np.array([[0., 1., 0.], [1., 0., np.nan]])
        self.forcing.static_data.humid_arid = self.climate
        self.params.pt_coeff_humid_arid.values[:] = np.where(
            self.climate == 0, 1.26, self.grid(1.74))
        self.split = self.params.drop_vars("pt_coeff_humid_arid").copy(deep=True)
        for name, value in [("pt_coeff_humid", 1.26), ("pt_coeff_arid", 1.74)]:
            self.split[name] = (("lat", "lon"), self.grid(value))

    def run_step(self, parameters):
        model = VerticalWaterBalance(
            self.forcing, SimpleNamespace(global_params=parameters))
        return step(model, self.grid)

    def test_split_preserves_legacy_fluxes_and_storages(self):
        models = [VerticalWaterBalance(
            self.forcing, SimpleNamespace(global_params=p))
            for p in (self.params, self.split)]
        for date in ("2001-01-01", "2001-01-02"):
            expected = step(models[0], self.grid, date)
            actual = step(models[1], self.grid, date)
            for name in expected:
                np.testing.assert_array_equal(actual[name], expected[name])
            for name in ("canopy_storage", "snow_water_storage",
                         "snow_water_storage_subgrid", "soil_water_content"):
                np.testing.assert_array_equal(
                    getattr(models[0], name), getattr(models[1], name))

    def test_independent_coefficients_affect_only_their_climate(self):
        baseline = self.run_step(self.split)
        for name, climate in [("pt_coeff_humid", 0), ("pt_coeff_arid", 1)]:
            with self.subTest(parameter=name):
                changed = self.split.copy(deep=True)
                changed[name] *= 1.2
                actual = self.run_step(changed)
                active = self.climate == climate
                inactive = self.climate == 1 - climate
                # Land PET is included in total PET; open-water PET uses
                # the same selected coefficient. Radiation stays unchanged.
                for flux in ("potevap", "openwater_PET"):
                    self.assertTrue(np.all(baseline[flux][active] > 0))
                    np.testing.assert_allclose(
                        actual[flux][active], baseline[flux][active] * 1.2)
                for flux in baseline:
                    np.testing.assert_array_equal(
                        actual[flux][inactive], baseline[flux][inactive])
                np.testing.assert_array_equal(actual["netrad"], baseline["netrad"])

    def test_split_precedence_spatial_values_and_ocean_mask(self):
        parameters = self.split.copy(deep=True)
        parameters["pt_coeff_humid_arid"] = self.params.pt_coeff_humid_arid * 10
        parameters.pt_coeff_humid.values[0, 2] = 1.4
        # Even finite coefficients must not turn ocean into a land cell.
        parameters.pt_coeff_arid.values[1, 2] = 1.9
        np.testing.assert_array_equal(
            select_pt_coeff(parameters, self.climate),
            [[1.26, 1.74, 1.4], [1.74, 1.26, np.nan]])

    def test_incomplete_split_rejected_even_with_legacy_field(self):
        for name in ("pt_coeff_humid", "pt_coeff_arid"):
            parameters = self.params.copy(deep=True)
            parameters[name] = self.split[name]
            with self.assertRaisesRegex(ValueError, "Supply both"):
                select_pt_coeff(parameters, self.climate)
        with self.assertRaisesRegex(ValueError, "Missing"):
            select_pt_coeff(xr.Dataset(), self.climate)


if __name__ == "__main__":
    unittest.main()
