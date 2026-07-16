# Graph Report - .  (2026-06-12)

## Corpus Check
- 44 files · ~310,927 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 561 nodes · 1080 edges · 42 communities (32 shown, 10 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 162 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Demand & Time Series Scripts|Demand & Time Series Scripts]]
- [[_COMMUNITY_ESMC Concepts & Scenarios|ESMC Concepts & Scenarios]]
- [[_COMMUNITY_TD Error Analysis|TD Error Analysis]]
- [[_COMMUNITY_D3 Minified (JS)|D3 Minified (JS)]]
- [[_COMMUNITY_Sankey Visualization Pipeline|Sankey Visualization Pipeline]]
- [[_COMMUNITY_D3 Internal Symbols A|D3 Internal Symbols A]]
- [[_COMMUNITY_D3 Internal Symbols B|D3 Internal Symbols B]]
- [[_COMMUNITY_D3 Internal Symbols C|D3 Internal Symbols C]]
- [[_COMMUNITY_D3 Internal Symbols D|D3 Internal Symbols D]]
- [[_COMMUNITY_D3 Internal Symbols E|D3 Internal Symbols E]]
- [[_COMMUNITY_Esmc Solver Orchestration|Esmc Solver Orchestration]]
- [[_COMMUNITY_Sankey CSV Export|Sankey CSV Export]]
- [[_COMMUNITY_AMPL DAT Generation|AMPL DAT Generation]]
- [[_COMMUNITY_Sankey JS Core|Sankey JS Core]]
- [[_COMMUNITY_Data Aggregation Scripts|Data Aggregation Scripts]]
- [[_COMMUNITY_Temporal Aggregation (TD)|Temporal Aggregation (TD)]]
- [[_COMMUNITY_D3 Internal Symbols F|D3 Internal Symbols F]]
- [[_COMMUNITY_Geographic Postprocessing|Geographic Postprocessing]]
- [[_COMMUNITY_Color Logging|Color Logging]]
- [[_COMMUNITY_D3 Internal Symbols G|D3 Internal Symbols G]]
- [[_COMMUNITY_TA Rationale Notes|TA Rationale Notes]]
- [[_COMMUNITY_OptiProbl Getters|OptiProbl Getters]]
- [[_COMMUNITY_File Ordering Utility|File Ordering Utility]]
- [[_COMMUNITY_CSP Precalculation|CSP Precalculation]]
- [[_COMMUNITY_Aviation Distance Matrix|Aviation Distance Matrix]]
- [[_COMMUNITY_TD Grouping Methods|TD Grouping Methods]]
- [[_COMMUNITY_TD-to-Year Reconstruction|TD-to-Year Reconstruction]]
- [[_COMMUNITY_AMPL Set Accessors|AMPL Set Accessors]]
- [[_COMMUNITY_AMPL Init & Connection|AMPL Init & Connection]]
- [[_COMMUNITY_Demand Sum Utility|Demand Sum Utility]]
- [[_COMMUNITY_Bolivia Country Code|Bolivia Country Code]]
- [[_COMMUNITY_Named Space ID|Named Space ID]]
- [[_COMMUNITY_Sankey Value Generator|Sankey Value Generator]]
- [[_COMMUNITY_Sankey Value Reader|Sankey Value Reader]]

## God Nodes (most connected - your core abstractions)
1. `_()` - 191 edges
2. `n()` - 36 edges
3. `Esmc` - 34 edges
4. `t()` - 32 edges
5. `i()` - 26 edges
6. `OptiProbl` - 26 edges
7. `e()` - 24 edges
8. `Region` - 23 edges
9. `u()` - 22 edges
10. `TemporalAggregation` - 21 edges

## Surprising Connections (you probably didn't know these)
- `link()` --calls--> `xi()`  [INFERRED]
  esmc/postprocessing/draw_sankey/sankey.js → esmc/postprocessing/draw_sankey/d3.min.js
- `a_priori_error()` --conceptually_related_to--> `Typical Days temporal aggregation (k-medoid clustering)`  [INFERRED]
  esmc/postprocessing/td_analysis.py → esmc/preprocessing/temporal_aggregation.py
- `a_posteriori_error()` --conceptually_related_to--> `Typical Days temporal aggregation (k-medoid clustering)`  [INFERRED]
  esmc/postprocessing/td_analysis.py → esmc/preprocessing/temporal_aggregation.py
- `step1_in()` --conceptually_related_to--> `Typical Days temporal aggregation (k-medoid clustering)`  [INFERRED]
  esmc/preprocessing/preprocessing.py → esmc/preprocessing/temporal_aggregation.py
- `step2_in()` --conceptually_related_to--> `AMPL .dat file generation pipeline`  [INFERRED]
  esmc/preprocessing/preprocessing.py → esmc/preprocessing/dat_print.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Sankey visualization flow: CSV generation → region grouping → HTML rendering** — postprocessing_output_to_sankey_csv_write_sankey_file, postprocessing_output_to_sankey_csv_cell, postprocessing_essankey_drawsankey [EXTRACTED 0.95]
- **TD clustering pipeline: data grouping → weighting → k-medoid optimization → t_h_td mapping** — preprocessing_temporal_aggregation_temporalaggregation, preprocessing_temporal_aggregation_kmedoid_clustering, preprocessing_temporal_aggregation_generate_t_h_td [EXTRACTED 0.95]
- **Full EnergyScope run: step1_in → set_ampl → run_ampl → step2_in → OptiProbl** — preprocessing_preprocessing_run_esmc, preprocessing_preprocessing_step1_in, preprocessing_preprocessing_step2_in [EXTRACTED 0.95]
- **ESMC core pipeline: Esmc orchestrates Region data and OptiProbl to form an end-to-end optimization workflow** — utils_esmc_esmc, utils_region_region, utils_opti_probl_optiprobl [INFERRED 0.95]
- **run.py orchestrates full simulation: init -> TA -> print -> solve -> results** — scripts_run_run, utils_esmc_esmc_init_ta, utils_esmc_esmc_solve_esom, utils_esmc_esmc_get_year_results [EXTRACTED 1.00]
- **Data preprocessing trio: EUD computation, TS generation, and RES potential import feed into Data/ directory** — scripts_advanced_compute_eud, scripts_advanced_generate_ts, scripts_advanced_import_rep [INFERRED 0.85]

## Communities (42 total, 10 thin omitted)

### Community 0 - "Demand & Time Series Scripts"
Cohesion: 0.05
Nodes (22): Data preprocessing pipeline (EUD, TS, RES potentials), DataFrame, clean_indices(), Cleans the leading and trailing spaces in the index and columns names      Par, This file contains a class to define an energy system, Reads the technologies data of the region and stores it in the data attribute as, TODO update doc      The Region class defines a region with its nuts abbreviat, Reads the storage power to energy ratio of the region and stores it in the data (+14 more)

### Community 1 - "ESMC Concepts & Scenarios"
Cohesion: 0.06
Nodes (27): ESOM Pipeline (init -> print_data -> set_esom -> solve -> get_results), Norte Amazonia Sufficiency Scenario 2025, Typical Days temporal aggregation, DataFrame, run.py (main script), Esmc, Gets the assets and stores it into the results,         for storage assets, and, Get the year energy balance of each layer (+19 more)

### Community 2 - "TD Error Analysis"
Cohesion: 0.05
Nodes (48): a_posteriori_error(), a_priori_error(), abs_err(), abs_err_corr(), compute_all_ts_from_td(), compute_dc(), compute_de_tds(), compute_design_error() (+40 more)

### Community 3 - "D3 Minified (JS)"
Cohesion: 0.06
Nodes (21): _(), at(), dn(), fn(), fr(), ft(), gr(), hn() (+13 more)

### Community 4 - "Sankey Visualization Pipeline"
Cohesion: 0.09
Nodes (36): Sankey pipeline (CSV → per-region energy flow diagram), drawSankey(), genSankey(), hexToRGB(), main(), color_dict (energy carrier color map), commons (global config dict), plotting_names (energy carrier display names) (+28 more)

### Community 5 - "D3 Internal Symbols A"
Cohesion: 0.11
Nodes (33): ai(), bi(), ci(), di(), ei(), fi(), gu(), ii() (+25 more)

### Community 6 - "D3 Internal Symbols B"
Cohesion: 0.14
Nodes (32): a(), c(), d(), du(), e(), ea(), en(), f() (+24 more)

### Community 7 - "D3 Internal Symbols C"
Cohesion: 0.11
Nodes (20): au(), br(), bt(), cu(), de(), dt(), fu(), hu() (+12 more)

### Community 8 - "D3 Internal Symbols D"
Cohesion: 0.18
Nodes (18): ae(), b(), bn(), bu(), ee(), ie(), ir(), le() (+10 more)

### Community 9 - "D3 Internal Symbols E"
Cohesion: 0.18
Nodes (17): an(), be(), ct(), fe(), ge(), he(), je(), k() (+9 more)

### Community 10 - "Esmc Solver Orchestration"
Cohesion: 0.12
Nodes (9): Reads the results printed into csv and store them into results dictionnary, OptiProbl, Get the solving info (time and result) and stores it into t attribute, The OptiProbl class allows to set an optimization problem in ampl, solve it,, Function to extract the mentioned parameter and store it into self.inputs, Function to extract the mentioned variable and store it into self.outputs, Reads the outputs previously printed into csv files to recover a case study with, Ejecuta la optimización con AMPL, genera IIS si el modelo es infeasible, y aplic (+1 more)

### Community 11 - "Sankey CSV Export"
Cohesion: 0.21
Nodes (7): Cell, This script post-processes the results to get data for the sankey per region, Lee las demandas eléctricas regionales desde el archivo reg_demands.dat, read_regional_electricity_demand(), write_sankey_file(), generate_sankey(), read_and_process_data()

### Community 12 - "AMPL DAT Generation"
Cohesion: 0.29
Nodes (13): AMPL .dat file generation pipeline, DataFrame, Path, ampl_syntax(), end_table(), newline(), print_df(), print_header() (+5 more)

### Community 13 - "Sankey JS Core"
Cohesion: 0.19
Nodes (5): computeNodeBreadths(), findAndMarkCycleBreaker(), link(), moveSinksRight(), scaleNodeBreadths()

### Community 14 - "Data Aggregation Scripts"
Cohesion: 0.22
Nodes (12): find_specific_folders(), main(), process_demands_csv(), process_resources_csv(), process_technologies_csv(), Process the Technologies.csv files from selected folders and create a summed ver, Save the summed results to CSV files in the output folder.          Args:, Find specific folders by name within the repository.          Args:         r (+4 more)

### Community 15 - "Temporal Aggregation (TD)"
Cohesion: 0.18
Nodes (8): Typical Days temporal aggregation (k-medoid clustering), generate_t_h_td (build hour-to-TD mapping matrix), Temporal aggregation class  This class defines the object TemporalAggregation, A class used to perform temporal aggregation on time series of multi-regional en, Weighting the normalized daily time series          The normalized daily conca, Multiplies 2 multiindexed pandas dataframes of different dimensions using numpy, Pivot the time series of each region in the daily format, TemporalAggregation

### Community 16 - "D3 Internal Symbols F"
Cohesion: 0.18
Nodes (12): gt(), it(), jt(), lt(), ne(), pt(), qt(), rt() (+4 more)

### Community 17 - "Geographic Postprocessing"
Cohesion: 0.21
Nodes (11): GeoDataFrame, GeoSeries, create_gdf_eu(), dist_regions(), get_lat_lon(), make_bbox(), Module with usefull functions for geographic analysis and plots  Author: Paolo, Make polygon from bbox coordinates https://stackoverflow.com/a/68741143/18253502 (+3 more)

### Community 19 - "D3 Internal Symbols G"
Cohesion: 0.22
Nodes (10): cn(), dr(), gn(), mn(), pr(), qn(), vn(), xn() (+2 more)

### Community 20 - "TA Rationale Notes"
Cohesion: 0.32
Nodes (4): Path, Parameters         ----------         dat_file          Returns         ---, Returns         -------, Reads the file containing the TD_of_days         By default, reads the followin

### Community 21 - "OptiProbl Getters"
Cohesion: 0.25
Nodes (4): Get the name of variables and parameters and the sets, Get the name of the LP optimization problem's variables, Get the name of the LP optimization problem's parameters, Prints the sets, parameters' names and variables' names of the LP optimization p

### Community 22 - "File Ordering Utility"
Cohesion: 0.38
Nodes (6): find_specific_folders(), main(), process_technology_files(), Process the Technologies.csv files and update the orden.csv template., Find specific folders by name within the repository.          Args:         r, Main function to execute the program.

### Community 23 - "CSP Precalculation"
Cohesion: 0.33
Nodes (6): compute_csp_ts(), generate_all_csp_ts(), Computes the time series of heat production of the CSP [GW_th] per unit of colle, Parameters     ----------     year : int, default: 2015         Representativ, PurePath, Series

### Community 24 - "Aviation Distance Matrix"
Cohesion: 0.40
Nodes (4): compute_av_demand(), compute_pkm(), Compute the pkm of the row, Computes the aviation demand in pkm for each region

## Knowledge Gaps
- **18 isolated node(s):** `GeoSeries`, `Series`, `PurePath`, `commons (global config dict)`, `color_dict (energy carrier color map)` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_()` connect `D3 Minified (JS)` to `D3 Internal Symbols A`, `D3 Internal Symbols B`, `D3 Internal Symbols C`, `D3 Internal Symbols D`, `D3 Internal Symbols E`, `D3 Internal Symbols F`, `D3 Internal Symbols G`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `Esmc` connect `ESMC Concepts & Scenarios` to `Demand & Time Series Scripts`, `TD Error Analysis`, `Sankey Visualization Pipeline`, `Esmc Solver Orchestration`, `Temporal Aggregation (TD)`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `OptiProbl` connect `Esmc Solver Orchestration` to `Demand & Time Series Scripts`, `ESMC Concepts & Scenarios`, `Sankey Visualization Pipeline`, `Temporal Aggregation (TD)`, `TA Rationale Notes`, `OptiProbl Getters`, `AMPL Set Accessors`, `AMPL Init & Connection`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `n()` (e.g. with `cu()` and `fu()`) actually correct?**
  _`n()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Esmc` (e.g. with `ESOM Pipeline (init -> print_data -> set_esom -> solve -> get_results)` and `TemporalAggregation`) actually correct?**
  _`Esmc` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `t()` (e.g. with `r()` and `en()`) actually correct?**
  _`t()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `i()` (e.g. with `en()` and `m()`) actually correct?**
  _`i()` has 3 INFERRED edges - model-reasoned connections that need verification._