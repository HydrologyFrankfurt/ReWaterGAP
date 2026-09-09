"""Cell-specific C++ WaterGAP calibration multipliers (dimensionless)."""

import numpy as np
import xarray as xr


MULTIPLIER_DESCRIPTIONS = {
    "root_depth_multiplier": "Rooting depth multiplier",
    "net_radiation_mult": "Land net radiation multiplier",
    "LAI_mult": "Maximum leaf area index multiplier",
    "degree_day_factor_mult": "Snowmelt degree-day factor multiplier",
    "gw_factor_mult": "Groundwater recharge factor multiplier",
    "rg_max_mult": "Maximum groundwater recharge multiplier",
    "net_abstraction_surfacewater_mult": "Surface water net abstraction multiplier",
    "net_abstraction_groundwater_mult": "Groundwater net abstraction multiplier",
    "precip_mult": "Precipitation multiplier",
}


def add_multiplier_defaults(parameters):
    """Support older parameter files with unity defaults on the gamma land mask.

    Existing multiplier fields, including calibrated values, are preserved.
    The dataset is updated in memory; its source file is not modified.
    """
    for name, description in MULTIPLIER_DESCRIPTIONS.items():
        if name not in parameters:
            parameters[name] = xr.full_like(parameters.gamma, 1.0,
                                            dtype=np.float64).where(
                                                parameters.gamma.notnull())
            parameters[name].attrs = {"long_name": description, "units": "-"}
    return parameters
