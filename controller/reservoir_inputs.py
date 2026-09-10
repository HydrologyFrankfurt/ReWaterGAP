"""Load reservoir geometry and algorithm-specific inflow/demand climatology."""

from pathlib import Path

import xarray as xr


def load_reservoir_inputs(static_land_path, algorithm, forcing, routing_root):
    """Keep local geometry; Hanasaki replaces only forcing-dependent variables.

    Scaling uses the existing flat reservoir directory. For Hanasaki, monthly
    mean inflow is a preprocessing input and is not loaded by the simulation.
    """
    base = Path(static_land_path) / 'reservoir_regulated_lake'
    files = sorted(list(base.glob('*.nc')) + list(base.glob('*.nc4')))
    files = [p for p in files if 'monthly_mean_inflow' not in p.name]
    if not files:
        raise FileNotFoundError(f'No reservoir input files in {base}')
    with xr.open_mfdataset(files, decode_times=False) as source:
        result = source.load()
    if algorithm == 'scaling':
        return result
    if algorithm != 'hanasaki':
        raise ValueError('Unknown reservoir operation algorithm: ' + algorithm)
    directory = Path(routing_root) / f'reservoir_routing_{forcing}'
    names = {
        'mean_inflow': f'watergap_22e_{forcing}_mean_inflow.nc4',
        'mean_nus': f'watergap_22e_{forcing}_mean_nus.nc4',
        'startmonth': (f'watergap_22e_{forcing}_startmonth.nc' if forcing == 'era5'
                       else 'watergap_22e_startmonth_w5e5.nc'),
    }
    for variable, filename in names.items():
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f'Hanasaki {forcing} input not found: {path}')
        with xr.open_dataset(path, decode_times=False) as source:
            replacement = source[variable].load()
        # Do not silently align a reversed, shifted or differently sized grid.
        _, replacement = xr.align(result[variable], replacement, join='exact')
        result[variable] = replacement
    return result
