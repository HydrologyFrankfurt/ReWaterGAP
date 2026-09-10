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

Reservoir operation is selected in `Config_ReWaterGAP.json`, under
`RuntimeOptions[0].SimulationOption.ReservoirOperation`:

```json
"ReservoirOperation": {
  "res_operation_algorithm": "scaling",
  "reservoir_forcing": "era5",
  "reservoir_routing_data_path": "input_data/static_input/reservoir_regulated_lake"
}
```

Set `res_operation_algorithm` to `scaling` or `hanasaki`.
Reservoirs must still be enabled with `AntNat_opts.res_opt`.
The default for older configurations is `scaling`.

- `scaling` uses `P1_reservoir` through `P6_reservoir` for successive pairs of
  months, and the existing reservoir inputs from the configured static input
  directory. It uses mean annual inflow and a rolling 30-day inflow history;
  changing `reservoir_forcing` does not change this algorithm's input files.
- `hanasaki` uses the chosen `era5` or `w5e5` inflow, demand, and start-month
  files from `reservoir_routing_data_path/reservoir_routing_<forcing>/`.
  It does not require or use `P1_reservoir` through `P6_reservoir`.

Forcing is explicit and is never inferred from the parameter filename. Reservoir
capacity, type, start year, outflow assignments, and lake/reservoir areas continue
to come from your configured static inputs, preserving local reservoir changes.
Hanasaki's three forcing-dependent grids are upstream global climatologies;
they are not recalibrated for locally added reservoirs. The monthly inflow files
are used only for preprocessing and are excluded from runtime loading. Missing
forcing files or mismatched coordinates produce errors instead of falling back
to another forcing.

The scaling routing call now passes P4 for July-August and keeps the updated
inflow counter. Earlier code passed P5 twice and discarded the counter, so this
correction can change scaling results. New restart files preserve the inflow
history and counter. Older restart files lack that information and initialize
it to zero. Hanasaki continues to preserve its release coefficient in restarts.

The upstream start-month utility can be run explicitly, for example:

```bash
python misc/get_reservoir_start_month.py --forcing era5 \
  --input-dir input_data/static_input/reservoir_regulated_lake/reservoir_routing_era5
```

It writes the start-month file in that directory; use `--output-dir` to write
elsewhere. It handles dry seasons spanning December-January and defaults to
January when there is no dry season. Importing the utility never writes files.

The upstream `CalibrateWaterGAP` configuration spelling and climate-path
forwarding for standard regionalization are supported. Older configurations
using `Calibrate WaterGAP` remain readable; external optimizers can continue
using `run_calib: false`.
