"""Separate gridded calibration parameters for reservoir release algorithms."""

import numpy as np
import xarray as xr


SCALING_MONTHS = (
    "January-February", "March-April", "May-June", "July-August",
    "September-October", "November-December",
)
HANASAKI_DEFAULTS = (0.85, 0.5, 0.5)
RESERVOIR_PARAMETER_DESCRIPTIONS = {
    **{f"P{i}_scaling": f"Scaling release multiplier for {months}"
       for i, months in enumerate(SCALING_MONTHS, 1)},
    "P1_hanasaki": "Capacity multiplier used to calculate the annual reservoir release coefficient",
    "P2_hanasaki": "Irrigation-reservoir parameter controlling provisional release",
    "P3_hanasaki": "Capacity-to-annual-inflow ratio threshold selecting the reservoir release equation",
}
HANASAKI_PARAMETER_COMMENTS = {
    "P1_hanasaki": (
        "Annual release coefficient = storage at the start of the operational "
        "year / (this parameter * reservoir capacity), except under the "
        "low-storage safeguard. This parameter does not change physical capacity."),
    "P2_hanasaki": (
        "Used only for irrigation reservoirs. Selects the provisional-release "
        "equation by comparing mean annual demand with this parameter times "
        "mean annual inflow; also scales provisional release in the high-demand branch."),
    "P3_hanasaki": (
        "Compares reservoir capacity divided by mean annual inflow volume with "
        "this threshold. At or above it, release equals the annual release "
        "coefficient times provisional release. Below it, release blends that "
        "value with daily inflow using (capacity-to-inflow ratio / threshold)^2. "
        "Annual inflow volume is calculated over 365 days."),
}


def add_reservoir_defaults(parameters):
    """Default missing Scaling and Hanasaki grids in memory.

    Explicit new fields always take precedence. Existing calibrated values and
    masks are preserved; defaults use the gamma land mask. Source files are not
    modified by this function.
    """
    for name, description in RESERVOIR_PARAMETER_DESCRIPTIONS.items():
        if name in parameters:
            continue
        default = (HANASAKI_DEFAULTS[int(name[1]) - 1]
                   if name.endswith("_hanasaki") else 1.0)
        parameters[name] = xr.full_like(
            parameters.gamma, default, dtype=np.float64).where(
                parameters.gamma.notnull())
        parameters[name].attrs = {"long_name": description, "units": "-"}
        if name in HANASAKI_PARAMETER_COMMENTS:
            parameters[name].attrs["comment"] = HANASAKI_PARAMETER_COMMENTS[name]
    return parameters
