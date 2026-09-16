# Acknowledging authorship

In the academic spirit of collaboration, the source code should be appropriately acknowledged in the resulting scientific disseminations.
You may cite it as follows:

- [1], for general reference to the EnergyScope project and the EnergyScope modeling framework
- [2], for reference to the origins of the EnergyScope project or to the first online version of the calculator energyscope.ch
- [3], for reference to the energyscope MILP modeling framework
- [4], for reference to the Belgian version
- [5], for reference to the extension to a Multi-Cell version
- [6], for reference to the energyscope Multi-Cell for Western EU energy system (v1)
- [7], for the current code

Bugs related to the upstream EnergyScope code can be reported to paolo.thiran@gmail.com.

# Content

This folder contains an adaptation of EnergyScope MultiCell, the multi-regional extension of the whole energy system model EnergyScope, applied to the Norte Amazónica (BNA) region of the Bolivian Amazon. Other releases are available @ the EnergyScope project repository: https://github.com/energyscope/EnergyScope

The region is modelled as five clusters: C1 (Beni/Ixiamas), C2 (Bolpebra), C3 (Riberalta, Guayaramerín, Puerto Gonzalo Moreno), C4 (Central Pando) and C5 (Cobija). They group towns and rural communities that are not connected to the national grid (SIN), with the exception of a limited SIN import into C1. The model is used to assess the cost of the current system, the cost of universal electricity access, and the evolution of cost and emissions towards 2035 and 2050 under different access trajectories.

The input data are produced in a companion repository, https://github.com/Valentine-Bernaerts/bolivia-energy-data, and documented in `Data/2025/README.md`. The `README.md` files found in `Data/2035/`, `Data/2050/` and in the three `Data/2025/<scenario>/` folders are notes inherited from the upstream model and describe European data sources, not the data of this repository. The `Data/` catalogue committed here is self-contained: the companion repository is not required to solve a scenario, only to run parts of the analysis notebooks. `scripts/analyse_resultats.ipynb` reads `analyse_GIS_projections/output/2024/cluster_summary.csv` and `projections/output/backtest_clusters_2024.csv`; `scripts/analyse_projections.ipynb` reads `projections/output/menages_projetes.csv`, `projections/output/split_abc_projete.csv`, `analyse data ramp/2050/output_energyscope_2050/vintage_registry.csv` and `exctraction of data/output/CSV_final.csv`. `scripts/analyse_sankey.ipynb` does not use it.

This work supports the master's thesis "Energy Transition Pathways for Isolated Regions in the Global South: A Case Study of Bolivia's Northern Amazon", Master of Science in Energy Engineering, University of Liège, academic year 2025-2026.

Description of the repository:

- ./Data/ : input catalogue, organised by horizon (2025, 2035, 2050), then by scenario, then by cluster C1 to C5. CSV and JSON files.
- ./esmc/ : the model package. `esmc/energy_model/` holds the AMPL model, `esmc/preprocessing/` the typical-day clustering, `esmc/postprocessing/` the result readers and the Sankey builder.
- ./scripts/ : entry points and analysis notebooks.
- ./case_studies/ : solved results, one folder per scenario.
- ./Docs/ and ./Documentation/ : documentation of the upstream EnergyScope Multi-Cell model and of its previous versions.
- ./paths.py : repository root, AMPL path, and path to the companion repository.
- ./environment.yml, ./setup.py : Python environment and package definition.
- ./LICENSE : license file
- ./NOTICE : authors acknowledgment and references
- ./README.md : this file

Contents of ./scripts/ :

- run.py : solves one scenario. The entry point.
- scenarios.py : declarative definition of the 22 scenarios.
- solve.py : the two-pass campaign that produced the published results, with the calibration of `share_dispersion` between the passes. It rewrites `Data/**/Misc.json`. Not to be re-run, see below.
- calibrate_share_dispersion.py : produced the `share_dispersion` values in `Data/`. Not to be re-run, see below.
- colors.py : colour palette shared by the notebooks.
- analyse_resultats.ipynb : comparison of the 2025 scenarios, cost decomposition, hourly dispatch.
- analyse_projections.ipynb : demographic projections, access trajectories, cost and emission pathways.
- analyse_sankey.ipynb : annual energy flows of the current system.

The notebooks display their figures inline and do not save them. `analyse_sankey.ipynb` writes its Sankey input files and diagram into `case_studies/C1_C2_C3_C4_C5/norte_amazonia_reality_2025/outputs/regional_results/`. Sections that produce a figure of the thesis are labelled as such; sections labelled complementary or cross-check are not in the thesis.

# License:

Copyright (C) <2018-2019> <Ecole Polytechnique Fédérale de Lausanne (EPFL), Switzerland and Université catholique de Louvain (UCLouvain), Belgium>

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License

# How to run the model

The model is coded in AMPL, uses the CPLEX solver, and is driven from Python. Both AMPL and CPLEX require a license. This fork has no GLPK code path.

1. Install AMPL and CPLEX.

2. Clone/download the content of this folder.

3. Create the Python environment:

```
conda env create -f environment.yml
conda activate energyscope
```

4. Point the scripts to your AMPL installation. `paths.py` looks for it in this order: the `ENERGYSCOPE_AMPL_PATH` environment variable, then `~/AMPL` if that folder exists, then the `ampl` executable on your `PATH`. The companion repository is looked for next to this one, or at `ENERGYSCOPE_BED_PATH`.

5. Solve a scenario:

```
python scripts/run.py <case>
```

The 22 cases are declared in `scripts/scenarios.py`. Twelve reference cases: `reality`, `reality_phase2`, `reality_access`, `sufficiency` and `access_transition` for 2025; `no_transition_2035`, `late_access_2035` and `early_access_2035`; `no_transition_2050`, `late_access_2050` and `early_access_2050`; and `early_access_brazil_2050`. Ten sensitivity cases change a single parameter of a reference case: `no_transition_2050_sens_diesel20`, `early_access_2050_sens_nodecsolar`, `late_access_2050_sens_nodecsolar`, `late_access_2050_sens_battom`, `early_access_brazil_2050_sens_price003`, `early_access_brazil_2050_sens_price009`, `early_access_brazil_2050_sens_vol923`, `early_access_brazil_2050_sens_vol1857`, `reality_access_sens_nodecsolar` and `sufficiency_sens_nodecsolar`. Running `python scripts/run.py` with an unknown name prints the list.

A single case takes about 7 to 42 minutes to solve on a 32 GB laptop, one case at a time.

The 2050 cases inherit installed capacity from the solved 2035 cases, and the Brazilian import case derives its import split from a solved `no_transition_2050`. Both are already written into `Data/`, so the published cases can be solved in any order, one at a time: every run rewrites the shared typical-day cache in `case_studies/C1_C2_C3_C4_C5/00_td_dat/`. The one exception is `late_access_2050_sens_battom`, which reuses that cache and must directly follow `late_access_2050` or `late_access_2050_sens_nodecsolar`. After every run, check that `solve_result_num` is `0` in `outputs/Solve_info.csv`: the output files are written even when the solve fails.

**A note on `Data/`.** The `share_dispersion` parameter in `Data/**/Misc.json` was calibrated once, from the outputs of a first solving pass that the final pass then overwrote. Re-running that calibration against the published outputs cannot recover those values and shifts them by up to 10.4 %. `Data/` as published is the input that produced the results of the thesis, and `scripts/calibrate_share_dispersion.py` is kept as the record of how the values were derived, not as a step to repeat. Both it and `scripts/solve.py` carry a warning to that effect.

6. Check the output files, written to `case_studies/C1_C2_C3_C4_C5/<study>/outputs/`, where `<study>` is the folder declared for the case in `scripts/scenarios.py` (for example `norte_amazonia_reality_2025`):

- ./TotalCost.csv : total annual cost of the system.
- ./Cost_breakdown.csv : cost of resources and technologies.
- ./Assets.csv : installed capacity of each technology, its bounds and its annual production.
- ./Gwp_breakdown.csv : GWP of resources and technologies.
- ./Year_balance.csv : year balance of resources and technologies.
- ./Resources.csv : resources summary over the year.
- ./Curt.csv : total curtailment.
- ./Sto_assets.csv : storage capacity, losses and annual energy flux.
- ./Exchanges_year.csv, ./Transfer_capacity.csv : yearly exchanges between clusters and line capacity.
- ./Exch_freight.csv : yearly freight exchanges.
- ./Solve_info.csv, ./Objective.csv : solver status and timings, and objective value.
- ./regional_results/ : the same quantities broken down by cluster, in a Regions column, without Solve_info.csv and Objective.csv, plus Exch_freight_border.csv. The Sankey input files are written here by `scripts/analyse_sankey.ipynb`.
- ./hourly_results/ : hourly data per typical day for production, resources, exchanges, curtailment and storage power, and the storage level over the year. Regenerated by a run and not committed, except the four files of `norte_amazonia_sufficiency_2025` that the hourly dispatch figure of `analyse_resultats.ipynb` reads.

# Previous versions and Authors:

- first release (v1, monthly MILP) of the EnergyScope (ES) model: https://github.com/energyscope/EnergyScope/tree/v1.0 .
- second release (v2, hourly LP) of the EnergyScope (ES) model: https://github.com/energyscope/EnergyScope/tree/v2.0 .
- first MultiCell release on a 3-cell ficitve case: https://github.com/pathiran22/EnergyScope/tree/Hernandez_Thiran_Multi_cell_2020
- EnergyScope MC for Western EU energy system (v1): https://github.com/16NoCo/EnergyScope/tree/Multi_cell_West-Eu_2021

Authors:

- Stefano Moret, Ecole Polytechnique Fédérale de Lausanne (Switzerland), moret.stefano@gmail.com
- Gauthier Limpens, Université catholique de Louvain (Belgium), gauthierLimpens@gmail.com
- Paolo Thiran, Université catholique de Louvain (Belgium), paolo.thiran@gmail.com
- Aurélia Hernandez, Université catholique de Louvain (Belgium).
- Noé Cornet, Université catholique de Louvain (Belgium).
- Pauline Eloy, Université catholique de Louvain (Belgium).

# References:

[1] G. Limpens, S . Moret, H. Jeanmart, F. Maréchal (2019). EnergyScope TD: a novel open-source model for regional energy systems and its application to the case of Switzerland. https://doi.org/10.1016/j.apenergy.2019.113729

[2] V. Codina Gironès, S. Moret, F. Maréchal, D. Favrat (2015). Strategic energy planning for large-scale energy systems: A modelling framework to aid decision-making. Energy, 90(PA1), 173–186. https://doi.org/10.1016/j.energy.2015.06.008

[3] S. Moret, M. Bierlaire, F. Maréchal (2016). Strategic Energy Planning under Uncertainty: a Mixed-Integer Linear Programming Modeling Framework for Large-Scale Energy Systems. https://doi.org/10.1016/B978-0-444-63428-3.50321-0

[4] Limpens, G. (2021). Generating energy transition pathways : application to Belgium.

[5] Hernandez, A., Thiran, P., Jeanmart, H., & Limpens, G. (2020). EnergyScope Multi-Cell : A novel open-source model for multi-regional energy systems and application to a 3-cell , low-carbon energy [UCLouvain]. http://hdl.handle.net/2078.1/thesis:25229

[6] Cornet, N., Eloy, P., Jeanmart, H., & Limpens, G. (2021). Energy Exchanges between Countries for a Future Low-Carbon Western Europe By merging cells in EnergyScope MC to handle wider regions.

[7] Thiran, P., Hernandez, A., Limpens, G., Prina, M. G., Jeanmart, H., & Contino, F. (2021). Flexibility options in a multi-regional whole-energy system : the role of energy carriers in the Italian energy transition. Proceedings of ECOS 2021 - The 34th International Conference on Efficiency, Cost, Optimization, Simulation and Environmental Impact of Energy Systems, Mc, 1–12.
