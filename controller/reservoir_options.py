"""Configuration for reservoir release algorithms and forcing inputs."""

from pathlib import Path


def reservoir_options(config):
    """Read explicit options, retaining scaling for older configurations."""
    simulation = config['RuntimeOptions'][0]['SimulationOption']
    options = simulation.get('ReservoirOperation', {})
    algorithm = options.get('res_operation_algorithm', 'scaling').lower()
    if algorithm not in ('scaling', 'hanasaki'):
        raise ValueError('res_operation_algorithm must be scaling or hanasaki')
    calibration = config['RuntimeOptions'][5]
    calibration = calibration.get('CalibrateWaterGAP',
                                  calibration.get('Calibrate WaterGAP', {}))
    forcing = options.get('reservoir_forcing',
                          calibration.get('calib_forcing', 'gswp3-era5'))
    forcing = forcing.lower().replace('gswp3-', '').replace('gswp3_', '')
    if forcing not in ('era5', 'w5e5'):
        raise ValueError('reservoir_forcing must be era5 or w5e5')
    default_root = (Path(config['FilePath']['inputDir']['static_land_data']) /
                    'reservoir_regulated_lake')
    routing_root = Path(options.get('reservoir_routing_data_path', default_root))
    return algorithm, forcing, routing_root
