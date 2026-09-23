"""Add separate Scaling/Hanasaki calibration grids without resetting values.

By default, use WaterGAP_2.3_global_parameters_with_reservoir_and_multipliers_nocal.nc
as the base. Choose --in-place or --output explicitly. Existing Scaling and
Hanasaki parameter values are preserved. All unrelated
NetCDF variables, attributes, encodings and dimensions are preserved.
"""

import argparse
import os
from pathlib import Path
import shutil
import tempfile

from netCDF4 import Dataset
import numpy as np

from model.reservoir_parameters import (
    HANASAKI_DEFAULTS, HANASAKI_PARAMETER_COMMENTS, RESERVOIR_PARAMETER_DESCRIPTIONS,
)


BASE_PARAMETER_FILE = Path(
    "model/WaterGAP_2.3_global_parameters_with_reservoir_and_multipliers_nocal.nc")


def update_reservoir_parameters(source, destination):
    """Update a copy atomically; the source may also be the destination."""
    source, destination = Path(source), Path(destination)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".nc",
                                     delete=False) as stream:
        temporary = Path(stream.name)
    try:
        shutil.copy2(source, temporary)
        with Dataset(temporary, "r+") as ds:
            template = ds.variables["gamma"]
            land = np.isfinite(np.ma.filled(template[:], np.nan))
            for name, description in RESERVOIR_PARAMETER_DESCRIPTIONS.items():
                if name not in ds.variables:
                    default = (HANASAKI_DEFAULTS[int(name[1]) - 1]
                               if name.endswith("_hanasaki") else 1.0)
                    variable = ds.createVariable(
                        name, "f8", template.dimensions, fill_value=np.nan)
                    variable[:] = np.where(land, default, np.nan)
                    if "coordinates" in template.ncattrs():
                        variable.coordinates = template.coordinates
                variable = ds.variables[name]
                variable.long_name = description
                variable.units = "-"
                if name in HANASAKI_PARAMETER_COMMENTS:
                    variable.comment = HANASAKI_PARAMETER_COMMENTS[name]
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=BASE_PARAMETER_FILE)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--in-place", action="store_true")
    target.add_argument("--output", type=Path)
    args = parser.parse_args()
    destination = args.input if args.in_place else args.output
    update_reservoir_parameters(args.input, destination)
    print(f"Updated reservoir parameters: {destination}")


if __name__ == "__main__":
    main()
