![Tests Status](https://github.com/HydrologyFrankfurt/ReWaterGAP/actions/workflows/unit_test.yaml/badge.svg) [![Pylint](https://github.com/HydrologyFrankfurt/ReWaterGAP/actions/workflows/lint.yaml/badge.svg)](https://github.com/HydrologyFrankfurt/ReWaterGAP/actions/workflows/lint.yaml) [![FAIR checklist badge](https://fairsoftwarechecklist.net/badge.svg)](https://fairsoftwarechecklist.net/v0.2?f=21&a=32113&i=12320&r=123) 

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)



# ReWaterGAP

# Documentation
Find the documentation [here](https://hydrologyfrankfurt.github.io/ReWaterGAP/).

# Project Description
WaterGAP is a global-scale hydrological simulation software for quantifying water flows and storages on all continents of the Earth. It is used to assess water availability and water stress for both humans and non-human biota.

WaterGAP has a leading role among global hydrological models. However, the research software, which has been modified by many PhD and postdoc researchers over more than 20 years, is still in a prototype state. It has never been refactored to fit a carefully planned software architecture, and software documentation is very limited. The software resembles a collection of “script-like” files that each have close to 10,000 lines of code without any separation of concerns. Therefore, it is currently not possible to hand the software to researchers from other groups to replicate and understand the results or to extend the product for their own research. Due to the complexity of global hydrological models and the importance of assessments and projections related to water resources, it is essential to have research software that is of a quality that enables the reproducibility of results.

The project goal is to rewrite the software with a modular structure using a modern programming language and providing extensive documentation.
Then, it will be possible for other researchers to run our global hydrological modelling software by themselves, to reproduce our results or investigate the impact of data and algorithm modifications on the results. The research community can compare algorithms, check the consistency and accuracy of our computational approach and find possible errors in the software more easily.

This project is done in cooperation between the Goethe University Frankfurt and the Ruhr-University Bochum.
For more information on the project and a more comprehensive description find the official project summary [here](https://www.uni-frankfurt.de/109439580/Towards_a_sustainable_utilization_of_the_global_hydrological_modelling_software_WaterGAP).

# Funding
ReWaterGap receives funding from the German Research Foundation (DFG). For further information, see the official project description
[here](https://gepris.dfg.de/gepris/projekt/443183317?language=en).

# The Team
- Principal investigator: [Prof. Dr. Petra Döll](https://www.uni-frankfurt.de/45217719/Univ__Prof__Dr__rer__nat__habil__Petra_D%C3%B6ll)
- Principal investigator: [Prof. Dr. Martina Flörke](https://www.hydrology.ruhr-uni-bochum.de/hydro/lehrstuhl/mitarbeiter/floerke.html.de)
- Lead software architect: [Dr. Robert Reinecke](https://github.com/rreinecke)
- Lead Programmer: [Emmanuel Nyenah](https://github.com/nyenah)
- Programming of reGWSWUSE: [Lasse Nissen](https://github.com/ln13foqy)
- Editing: [Leon Mühlenbruch](https://github.com/Leon-Muehlenbruch)

# Get in Touch
If you wish to reach out to us write us an [Email](mailto:Nyenah@em.uni-frankfurt.de) any time and we’ll gladly get back to you.

# Addition: Modular Evapotranspiration

A modified version of ReWaterGAP (https://github.com/HydrologyFrankfurt/ReWaterGAP), was built for a M.Sc. thesis at the University of Freiburg on how sensitive the WaterGAP global hydrological model is to the potential evapotranspiration (PET) formulation it uses. All credit for the model belongs to its authors (Nyenah et al. 2025; Müller Schmied et al. 2021).

## Additions made

In its standard implementation, WaterGAP computes PET with a single Priestley–Taylor formulation. The point of this thesis was to swap that formulation with several others and see how the model results react to it. Consequently this fork adds six additional PET options and makes them interchangeable via the `PET_implementation` block in the config file (`Config_ReWaterGAP.json`).Only one equation should be set to `true` at a time:

- `hargreaves_samani` — temperature-based
- `jensen_haise` — radiation-based
- `penman_monteith` — FAO-56 grass reference
- `penman_monteith_complete` — full Penman–Monteith with land-cover-specific resistances
- `priestley_taylor_parameterized` — Priestley–Taylor with a regionalized Alpha parameter
- `koeppen_regionalized` — picks a preferred formulation formulation per climate zone, from the ones mentioned above

The actual code changes are restricted to the config, the controller (config reading and static-data loading) and the vertical-water-balance / PET functions. Nothing in the established model logic was touched.

## Additional static inputs

Three additional static input files in `input_data/static_input/` are needed to run some of the PET equations:

`koeppen_zones_1991_2020_0p5.nc` holds the five Köppen–Geiger main zones (A–E), aggregated from the 30 sub-classes of Beck et al. (2023) onto the WaterGAP 0.5° grid.

`pt_alpha_aschonitis_0p5.nc` is the locally calibrated Priestley–Taylor alpha coefficient from Aschonitis et al. (2017). Their apts5 short-reference-crop grid was regridded to the WaterGAP land mask, with the few missing land cells nearest-filled.

`landcover_resistance_pm.csv` collects the per-IGBP-class parameters for the complete Penman–Monteith: roughness lengths and displacement height after Borak et al. (2025), with z0h = 0.1·z0m per the FAO-56 convention, and the bulk surface resistance after Kelliher et al. (1995).

## Additional inputs required, that are not part of this repository

The two Penman–Monteith options also need near-surface wind speed (`sfcWind`) and relative humidity (`hurs`). Those come from GSWP3-W5E5 (ISIMIP3a). They can be derived in the same way as the other climate data input, and added to two additional folders `sfcwind`and `hurs inside the `input_data/climate_forcing/` folder structure.

## References

**Model**

- Nyenah, E., et al. (2025): The process and value of reprogramming a legacy global hydrological model. *EGUsphere* [preprint], doi:10.5194/egusphere-2025-1096.
- Müller Schmied, H., et al. (2021): The global water resources and use model WaterGAP v2.2d: model description and evaluation. *Geosci. Model Dev.*, 14, 1037–1072, doi:10.5194/gmd-14-1037-2021.

**PET formulations**

- Priestley, C. H. B. & Taylor, R. J. (1972): On the assessment of surface heat flux and evaporation using large-scale parameters. *Mon. Weather Rev.*, 100, 81–92.
- Hargreaves, G. H. & Samani, Z. A. (1985): Reference crop evapotranspiration from temperature. *Appl. Eng. Agric.*, 1, 96–99.
- Hargreaves, G. H. & Allen, R. G. (2003): History and evaluation of Hargreaves evapotranspiration equation. *J. Irrig. Drain. Eng.*, 129, 53–63, doi:10.1061/(ASCE)0733-9437(2003)129:1(53).
- Jensen, M. E. & Haise, H. R. (1963): Estimating evapotranspiration from solar radiation. *J. Irrig. Drain. Div. ASCE*, 89, 15–41.
- Monteith, J. L. (1965): Evaporation and environment. *Symp. Soc. Exp. Biol.*, 19, 205–234.
- Allen, R. G., Pereira, L. S., Raes, D. & Smith, M. (1998): Crop evapotranspiration – Guidelines for computing crop water requirements. *FAO Irrigation and Drainage Paper 56*, FAO, Rome.
- Pimentel, R., et al. (2023): Which potential evapotranspiration formula to use in hydrological modeling world-wide? *Water Resour. Res.*, 59, e2022WR033447, doi:10.1029/2022WR033447.

**Static input data**

- Beck, H. E., et al. (2023): High-resolution (1 km) Köppen-Geiger maps for 1901–2099 based on constrained CMIP6 projections. *Sci. Data*, 10, 724, doi:10.1038/s41597-023-02549-6.
- Aschonitis, V. G., et al. (2017): High-resolution global grids of revised Priestley–Taylor and Hargreaves–Samani coefficients for assessing ASCE-standardized reference crop evapotranspiration and solar radiation. *Earth Syst. Sci. Data*, 9, 615–638, doi:10.5194/essd-9-615-2017.
- Borak, J. S., et al. (2025): Global climatologies of vegetation aerodynamic roughness for momentum. *Earth Space Sci.*, doi:10.1029/2023EA003027.
- Kelliher, F. M., et al. (1995): Maximum conductances for evaporation from global vegetation types. *Agric. For. Meteorol.*, 73, 1–16.