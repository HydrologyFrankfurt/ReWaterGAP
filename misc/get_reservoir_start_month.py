# -*- coding: utf-8 -*-
"""
Generate forcing-specific reservoir start months from inflow climatology.

@author: nyenah
"""
import xarray as xr
import numpy as np
from numba import njit
from pathlib import Path


@njit(cache=True)
def find_reservoir_start_month(monthly_mean, annual_mean, dry_start):
    """
    Find the starting month of the longest dry period for each grid cell.

    A month is considered dry when

        monthly_mean < annual_mean

    Dry seasons spanning December-January are treated as continuous periods.
    Ties select the earliest start month in the calendar year.

    Parameters
    ----------
    monthly_mean : ndarray of float64
        Monthly climatological mean with shape (12, nlat, nlon).

    annual_mean : ndarray of float64
        Annual mean with shape (nlat, nlon).

    Returns
    -------
    ndarray of float
        Array of shape (nlat, nlon).

        Values:
            1-12 : Start month of the longest dry season
             1    : Default value when no dry months exist
    """


    nlat, nlon = annual_mean.shape
    for i in range(nlat):
        for j in range(nlon):
            if not np.isfinite(annual_mean[i, j]):
                dry_start[i, j] = np.nan
                continue
            if not np.all(np.isfinite(monthly_mean[:, i, j])):
                dry_start[i, j] = np.nan
                continue
            dry_start[i, j] = 1
            if annual_mean[i, j] <= 0:
                continue
            dry = monthly_mean[:, i, j] < annual_mean[i, j]
            longest_length = 0
            # Each run begins after a wet month, including across December.
            # Ties select the earliest start month in the calendar year.
            for month in range(12):
                if dry[month] and not dry[(month - 1) % 12]:
                    length = 0
                    while length < 12 and dry[(month + length) % 12]:
                        length += 1
                    if length > longest_length:
                        longest_length = length
                        dry_start[i, j] = month + 1
    return dry_start


def save_start_month_netcdf(start_month, monthly_mean_file, output_dir="."):
    """
    Save start month result as NetCDF.

    Output name depends on input dataset:
        ERA5 -> watergap_22e_era5_startmonth.nc
        W5E5 -> watergap_22e_startmonth_w5e5.nc
    """

    # Identify dataset type from filename
    filename = monthly_mean_file.lower()

    if "watergap_22e_era5" in filename:
        dataset_name = "era5"
    elif "watergap_22e_w5e5" in filename:
        dataset_name = "w5e5"
    else:
        raise ValueError(
            "Cannot identify dataset. Filename must contain 'era5' or 'w5e5'."
        )

    filename = (f"watergap_22e_{dataset_name}_startmonth.nc" if dataset_name == "era5"
                else "watergap_22e_startmonth_w5e5.nc")
    output_file = str(Path(output_dir) / filename)

    # Open original file to get coordinates
    with xr.open_dataset(monthly_mean_file, decode_times=False) as source:
        ds = source.load()

    # Create DataArray
    start_month = start_month[np.newaxis, :, :]
    da = xr.DataArray(
        start_month,
        dims=("time", "lat", "lon"),
        coords={
            "time":[-1.9e+03], #just to match old version
            "lat": ds.lat,
            "lon": ds.lon
        },
        name="startmonth"
    )

    # Add metadata
    da.attrs = {
        "long_name": "Reservoir start month",
        "description": (
            "Month when the longest continuous dry season begins. "
            "Dry months defined as monthly mean < annual mean."
        ),
        "units": "month"
    }

    # Save
    da.to_netcdf(output_file)

    print(f"Saved: {output_file}")

    return output_file


def main():
    """Generate start months explicitly; importing this module never writes files."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forcing', choices=['era5', 'w5e5'], required=True)
    parser.add_argument('--input-dir', type=Path, required=True,
                        help='Directory containing forcing-specific inflow climatology')
    parser.add_argument('--output-dir', type=Path,
                        help='Defaults to the input directory')
    args = parser.parse_args()
    monthly_path = args.input_dir / f'watergap_22e_{args.forcing}_monthly_mean_inflow.nc4'
    annual_path = args.input_dir / f'watergap_22e_{args.forcing}_mean_inflow.nc4'
    with xr.open_dataarray(monthly_path, decode_times=False) as source:
        monthly = source.load()
    with xr.open_dataarray(annual_path, decode_times=False) as source:
        annual = source.isel(time=0, drop=True).load()
    xr.align(monthly.isel(time=0, drop=True), annual, join='exact')
    start_month = find_reservoir_start_month(
        monthly.values, annual.values, np.full(annual.shape, np.nan))
    save_start_month_netcdf(start_month, str(monthly_path),
                            str(args.output_dir or args.input_dir))


if __name__ == '__main__':
    main()
