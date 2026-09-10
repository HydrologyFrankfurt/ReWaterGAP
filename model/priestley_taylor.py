"""Select independently calibrated Priestley-Taylor coefficients by climate."""

import numpy as np


def select_pt_coeff(parameters, humid_arid):
    """Return the PET coefficient grid (0 = humid, 1 = arid/semi-arid).

    Both split fields must be supplied together. Older parameter files with
    only ``pt_coeff_humid_arid`` remain usable without changing their values.
    When both formats exist, the split fields take precedence.
    """
    split_fields = ("pt_coeff_humid", "pt_coeff_arid")
    present = [name in parameters for name in split_fields]
    if any(present):
        if not all(present):
            raise ValueError("Supply both pt_coeff_humid and pt_coeff_arid")
        return np.where(
            humid_arid == 0, parameters.pt_coeff_humid.values,
            np.where(humid_arid == 1, parameters.pt_coeff_arid.values, np.nan))
    if "pt_coeff_humid_arid" in parameters:
        return parameters.pt_coeff_humid_arid.values.copy()
    raise ValueError("Missing Priestley-Taylor coefficients: supply "
                     "pt_coeff_humid and pt_coeff_arid")
