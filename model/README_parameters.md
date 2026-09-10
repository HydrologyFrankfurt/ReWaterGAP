The parameter file `WaterGAP_2.3_global_parameters_gswp3_era5_with_reservoir_and_multipliers.nc`
stores two independently adjustable Priestley-Taylor coefficients:

| Variable | Initial value on every land cell | Active classification |
| --- | --- | --- |
| `pt_coeff_humid` | 1.26 | Humid (`aridhumid == 0`) |
| `pt_coeff_arid` | 1.74 | Arid/semi-arid (`aridhumid == 1`) |

Both variables are dimensionless `(lat, lon)` grids with ocean cells masked.
The classification comes from `watergap_22e_aridhumid.nc4` in the configured
static input directory. The vertical water balance selects the appropriate
coefficient during initialization and uses it for both land and open-water PET.
The initial effective coefficient grid is identical to the previous combined
`pt_coeff_humid_arid` grid.

An external optimizer can assign separate bounds to these two variable names
and write candidate values into each grid within the calibration area. Only
cells of the corresponding climate class respond to each parameter. If a
calibration area contains only one class, only that class's coefficient affects
its PET. Bounds are defined by the optimizer; the model does not impose new
calibration ranges. Initialize a new model instance for each candidate, as with
the other parameters resolved during initialization. Normal simulations invoked
by an external optimizer can keep `run_calib: false`.

Older NetCDF files containing only `pt_coeff_humid_arid` remain supported and
retain their existing spatial values. Both new fields must be supplied together;
if both new fields and the old field exist, the new fields take precedence.
The updated file above contains only the two new fields.
