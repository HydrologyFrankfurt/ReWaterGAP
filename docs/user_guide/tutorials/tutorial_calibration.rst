.. _tutorial_calibration:

Calibration 
###########

.. contents:: 
    :depth: 3
    :backlinks: entry

Rational : 
The calibration scheme forces simulated long-term average river discharge to match the observed value within a maximum permitted deviation of ± 10%
Calibration follows a four-step scheme with specific calibration status (CS) according to Müller Schmied et al., 2021, 2023:
CS1 – adjust the basin-wide uniform parameter γ (Müller Schmied et al., 2021, their Eq. 18) in the range of [0.1–5.0] to match mean annual observed streamflow within ±1 %.
CS2 – adjust γ as for CS1 but within 10 % uncertainty range (90 %–110 % of observations).
CS3 – as for CS2 but apply the areal correction factor, CFA (adjusts runoff and, to conserve the mass balance, actual evapotranspiration as the counterpart of each grid cell within the range of [0.5–1.5]), to match mean annual observed streamflow with 10 % uncertainty.
CS4 – as for CS3 but apply the station correction factor, CFS (multiplies streamflow in the cell where the gauging station is located by an unconstrained factor), to match mean annual observed streamflow with 10 % uncertainty to avoid error propagate ion to the downstream basin.

Step-by-step guide to calibrating the WaterGAP model .

Preparing climate and water use data. 
Please see tutorials on where to download climate forcing and water use data.  (https://hydrologyfrankfurt.github.io/ReWaterGAP/user_guide/tutorials.html#id34). 
Run WaterGAP to compute actual NAs and NAg (standard anthropogenic run)
# use uncalibrated  aparamaters Gamma = 2,  CFA and CFS =1
 (describe the setup to run it)
The above described steps is done for 1509  streamflow stations which corresponds to 1509 calibration station ( the upstream cells )

Run  model to get actual abstraction (Nas and Nag)
Calibrate 1509 station with calibration scheme using Nas and Nag from step 1
Standard anthropogenic run (neighbouring cell water supply is switched off)
 Regionalisation
calibrated gamma  values are regionalised to river basins without sufficient streamflow observations using a multiple linear see Müller Schmied et, al. (2021) .
Compute bankfulll flow (constant flow velocity = 1m/s  or 86.4 km/day) 
After estimating the maximum river storage with bankfull flow from step 4,  we  compute bankfulll flow (storage-based river velocity) 
Naturalised run to compute inflows into reservoirs 
Using reservoirs inflows from step 5 run  model to get actual abstraction (Nas and Nag)
Standard anthropogenic run 
Calibrate 1509 station with calibration scheme Nas and Nag from step 6
Standard anthropogenic run (neighbouring cell water supply is switched off)



