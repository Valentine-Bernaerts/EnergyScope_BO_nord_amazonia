# Inventory

Factual inventory of the repository: what runs, in what order, what it reads, what it writes,
and what an outside user needs. Measured on Windows 11, AMPL 20250811 + CPLEX 22.1.2,
Python 3.13.9 (Anaconda), 32 GB RAM (31.5 GB usable), laptop, on 2026-09-16.

---

## 1. Execution order

Three entry points, all run from the repository root.

| # | Command | Produces |
|---|---|---|
| 1 | `python scripts/run.py <case>` | solves one case, writes `case_studies/C1_C2_C3_C4_C5/<study>/` |
| 2 | `python scripts/solve.py <group> [--only all\|pass1\|pass2] [--skip-pass1 a,b] [--dry-run]` | two-pass campaign over a group of cases, with recalibration between the passes |
| 3 | `python scripts/calibrate_share_dispersion.py <case_study> <year> <data_scenario>` | rewrites `share_dispersion` in `Data/<year>/<scenario>/C{1..5}/Misc.json` **in place** |

### 1.1 What `run.py` writes

For case `<case>` with study directory `<study>`, under
`case_studies/C1_C2_C3_C4_C5/<study>/`:

| Path | Content |
|---|---|
| `indep.dat`, `reg_*.dat` | the AMPL data files generated from `Data/` for this run |
| `ESMC_model_AMPL.mod`, `ESMC_obj_TotalCost.mod` | model and objective, copied in by the framework |
| `outputs/TotalCost.csv` | total annual system cost, M EUR/y |
| `outputs/Cost_breakdown.csv` | `C_inv`, `C_maint`, `C_op` per technology/resource |
| `outputs/Assets.csv` | installed capacity `F`, bounds `f_min`/`f_max`, annual production `F_year` |
| `outputs/Gwp_breakdown.csv` | `GWP_constr`, `GWP_op`, `CO2_net` |
| `outputs/Year_balance.csv` | annual flow of every technology on every layer |
| `outputs/Resources.csv` | `R_year_local`, `R_year_exterior`, `R_year_import`, `R_year_export` |
| `outputs/Solve_info.csv` | `ampl_elapsed_time`, `solve_elapsed_time`, `solve_result_num` |
| `outputs/Objective.csv`, `Curt.csv`, `Sto_assets.csv`, `Exchanges_year.csv`, `Exch_freight.csv`, `Transfer_capacity.csv` | secondary results |
| `outputs/regional_results/` | the same tables broken down per cluster C1..C5 |
| `log.txt` *or* `run_logs/<study>_log.txt` | the CPLEX log (not tracked) |

`solve_result_num` is the only reliable success test. **The pipeline writes complete,
normal-looking output files even when the solve was rejected**; `0` means optimal.

### 1.2 Shared state between runs

`case_studies/C1_C2_C3_C4_C5/00_td_dat/` holds the typical-day clustering
(`TD_of_days_16.out`, `data_16.dat`, `e_ts16.txt`, `log_16.txt`). Every run with
`reuse_td = False` re-runs the k-medoid clustering and **overwrites this directory**.
Consequences:

- runs must be strictly sequential; two concurrent runs corrupt the cache;
- `late_access_2050_sens_battom` (`reuse_td = True`) reads the cache instead of re-clustering,
  so it must run immediately after a case built on the same `Data/2050/late_access/` time
  series, otherwise it inherits the wrong typical days.

### 1.3 Dependency order

The order below is the one the results were produced in. The chaining is **historical, not
live**: the derived values are already written into `Data/`, so a re-solve in this order
reproduces the results without regenerating anything.

1. **2025** — `reality`, `reality_phase2`, `reality_access`, `access_transition`, `sufficiency`.
   `access_transition` shares `Data/2025/reality_access/` with `reality_access` and has no
   `share_dispersion` of its own.
2. **2035** — `no_transition_2035`, `early_access_2035`, `late_access_2035`.
3. **2050** — `no_transition_2050`, `early_access_2050`, `late_access_2050`.
   `Data/2050/*/C*/Technologies.csv` carries an `f_min` chained from each scenario's solved
   2035 `Assets.csv`; the chaining is done by `bolivia-energy-data/analyse data ramp/2050/`,
   not by this repository.
4. **Brazil** — `early_access_brazil_2050`. Its `ELECTRICITY` `avail_exterior` split between C3
   and C5 was derived from `no_transition_2050`'s solved `GENSET_DIESEL` production and is
   frozen in `Data/2050/early_access_brazil/C{3,5}/Resources.csv`.
5. **Sensitivities** — the eight single-variable runs, then the two `_sensitivity_DEC_SOLAR_fmax0`
   runs. Each inherits its parent's catalogue and `share_dispersion`; none is recalibrated.

### 1.4 The two-pass calibration, and why re-running it is not idempotent

`solve.py` implements: force `share_dispersion = 0` in `Data/<year>/<scenario>/C*/Misc.json`
→ solve every scenario (pass 1) → recompute `share_dispersion` from each scenario's **pass-1**
`Year_balance.csv` and `Resources.csv` → solve again (pass 2).

Pass 2 overwrites the pass-1 outputs in the same directory. Recomputing the calibration from
what is on disk after pass 2 therefore cannot reproduce the stored values: local electricity
supply is measured on a different solve. Measured drift between the stored values and a
recalibration from the final solves: +0.1 % to +10.4 % relative, worst case
`early_access_brazil_2050` / C4 (stored `0.00175800`, recomputed `0.00194101`).

**Re-running `python scripts/solve.py campaign` on a repository whose `Data/` is already
calibrated silently changes `Data/**/Misc.json` and therefore the model inputs.** To reproduce
the published results, solve each case once with `run.py` and leave `Data/` alone.

`Data/` is consequently a **frozen input**: it is the authentic state that produced the published
results, and the repository provides no path to regenerate it. Both scripts that can write to it
carry a `DO NOT RUN` banner in their module docstring:
`scripts/calibrate_share_dispersion.py` and `scripts/solve.py`.

### 1.5 Wording for the README

Verbatim text to carry into the README:

> ### `Data/` is frozen
>
> `Data/` is the input state that produced the results published in this repository. It is not
> regenerated by anything here, and it must not be regenerated.
>
> One parameter, `share_dispersion` in `Data/<year>/<scenario>/C{1..5}/Misc.json`, was derived
> from a solve rather than from a data source. The derivation is a two-pass procedure: every
> scenario was first solved with `share_dispersion = 0` to measure its local electricity supply,
> the parameter was calibrated from that first solve, and every scenario was then solved again.
> The second solve overwrote the first in the same output directory, so the input to the
> calibration no longer exists on disk. Running the calibration again measures a different local
> supply and produces different values — between +0.1 % and +10.4 % away from the frozen ones,
> the largest gap being on cluster C4 of `early_access_brazil_2050` (frozen `0.00175800`,
> recomputed `0.00194101`).
>
> `scripts/calibrate_share_dispersion.py` is therefore kept as documentation of a completed step,
> not as a step of the pipeline: no notebook writes `share_dispersion`, and it cannot be recovered
> from the CSV inputs, so deleting the script would leave the value unexplainable.
> `scripts/solve.py`, which calls it, is kept on the same basis. **Neither should be run.** Both
> carry the warning in their own docstring.
>
> To re-solve any case against the frozen inputs, use `python scripts/run.py <case>`. It never
> writes to `Data/`.

---

## 2. The 22 cases

Declared in `scripts/scenarios.py`; `python scripts/run.py <name>` with no valid name prints
the list. All 22 have outputs committed under `case_studies/C1_C2_C3_C4_C5/`.

Clusters: C1 Beni/Ixiamas, C2 Bolpebra, C3 Riberalta/Guayaramerin/Puerto, C4 Central Pando,
C5 Cobija.

### 2.1 Central cases (12)

| # | `run.py` name | `Data/` read | Study directory | What it represents |
|---|---|---|---|---|
| 1 | `reality` | `2025/reality` | `norte_amazonia_reality_2025` | Dispatch of the real 2025 system. Diesel and C1's SIN import uncapped, no home battery, no new supply. |
| 2 | `reality_phase2` | `2025/reality` | `norte_amazonia_reality_2025_phase2` | Same system, but utility PV and grid batteries may be built; `f_min` stays brownfield, wind and hydro off. |
| 3 | `reality_access` | `2025/reality_access` | `norte_amazonia_reality_access_2025` | Real 2025 system carrying universal-access demand; home-system floors baked into `Technologies.csv`. |
| 4 | `access_transition` | `2025/reality_access` | `norte_amazonia_access_transition_2025` | `reality_access` plus supply-side unlock, with the frozen 2025 diesel/gas fleet released. |
| 5 | `sufficiency` | `2025/sufficiency` | `norte_amazonia_sufficiency_2025` | Universal sufficiency demand on the 2025 system; observed home fleet applied as a floor only. |
| 6 | `no_transition_2035` | `2035/no_transition` | `norte_amazonia_no_transition_2035` | 2035 demand, supply frozen at the existing fleet (`f_max = f_min` on PV_UTILITY and BATT_LI). |
| 7 | `late_access_2035` | `2035/late_access` | `norte_amazonia_late_access_2035` | 2035, supply transition unlocked, access reached on the late calendar. |
| 8 | `early_access_2035` | `2035/early_access` | `norte_amazonia_early_access_2035` | 2035, supply transition unlocked, access reached on the early calendar. |
| 9 | `no_transition_2050` | `2050/no_transition` | `norte_amazonia_no_transition_2050` | 2050 demand, supply still frozen. |
| 10 | `late_access_2050` | `2050/late_access` | `norte_amazonia_late_access_2050` | 2050, late access calendar, supply unlocked. |
| 11 | `early_access_2050` | `2050/early_access` | `norte_amazonia_early_access_2050` | 2050, early access calendar, supply unlocked. |
| 12 | `early_access_brazil_2050` | `2050/early_access_brazil` | `norte_amazonia_early_access_brazil_2050` | `early_access_2050` with the Brazilian interconnection open to C3 and C5 (113.8 GWh/y). |

### 2.2 Sensitivities (10)

Each is its parent case with exactly one parameter changed, in its own study directory.
None recalibrates `share_dispersion`.

| # | `run.py` name | Parent | The single change |
|---|---|---|---|
| 13 | `no_transition_2050_sens_diesel20` | `no_transition_2050` | `GENSET_DIESEL` lifetime 20 y instead of 30 y (Plan Electrico Referencial 2035). |
| 14 | `early_access_2050_sens_nodecsolar` | `early_access_2050` | `DEC_SOLAR` blocked (`f_min = f_max = 0`); `TS_DEC` untouched. |
| 15 | `late_access_2050_sens_nodecsolar` | `late_access_2050` | idem, on the late calendar. |
| 16 | `late_access_2050_sens_battom` | `late_access_2050` | `BATT_LI` `c_maint` = 10.647 M EUR/GWh/y (NREL ATB 2.5 %/y of the 2025 `c_inv`) against the catalogue's 0.658. **Reuses the typical days.** |
| 17 | `early_access_brazil_2050_sens_price003` | `early_access_brazil_2050` | Brazilian import price 0.03 M EUR/GWh instead of 0.0593; applied in memory, `Resources_indep.csv` untouched. |
| 18 | `early_access_brazil_2050_sens_price009` | `early_access_brazil_2050` | same, at 0.09 M EUR/GWh. |
| 19 | `early_access_brazil_2050_sens_vol923` | `early_access_brazil_2050` | Brazilian import volume 92.3 GWh/y instead of 113.8; the C3/C5 split is preserved exactly. |
| 20 | `early_access_brazil_2050_sens_vol1857` | `early_access_brazil_2050` | same, at 185.7 GWh/y. |
| 21 | `reality_access_sens_nodecsolar` | `reality_access` | `DEC_SOLAR` blocked. Writes to `_sensitivity_DEC_SOLAR_fmax0/reality_access/` (manuscript figure 21). |
| 22 | `sufficiency_sens_nodecsolar` | `sufficiency` | `DEC_SOLAR` blocked. Writes to `_sensitivity_DEC_SOLAR_fmax0/sufficiency/` (manuscript figure 21). |

`scripts/solve.py` does **not** cover cases 1, 2, 21 and 22: its `campaign` group holds 10 cases
and its `sens` group holds 8. Those four are run with `run.py` directly.

---

## 3. `Data/`

`Data/<year>/<scenario>/` is one complete input catalogue per scenario. 567 tracked files,
81.7 MB.

```
Data/
  2025/  reality/  reality_access/  sufficiency/
  2035/  no_transition/  early_access/  late_access/
  2050/  no_transition/  early_access/  late_access/  early_access_brazil/
```

Each scenario folder contains:

| Path | Content |
|---|---|
| `C1/ … C5/` | per cluster: `Demands.csv`, `Resources.csv`, `Technologies.csv`, `Time_series.csv`, `Weights.csv`, `Storage_power_to_energy.csv`, `Misc.json` |
| `00_INDEP/` | shared across clusters: `Layers_in_out.csv`, `Resources_indep.csv`, `Storage_characteristics.csv`, `Storage_eff_in.csv`, `Storage_eff_out.csv`, `Misc_indep.json` |
| `01_EXCH/` | inter-cluster exchange: `Dist.csv`, `Network_exchanges.csv`, `Exchange_losses.csv`, `Lhv.csv`, `Misc_exch.json` |
| `02_REF_REGION/` | the reference region the clusters are derived from |

Extra files:

| Path | Content |
|---|---|
| `Data/2025/reality/source_A_grid_consumption_by_municipality.csv` | observed grid consumption per municipality |
| `Data/2025/reality/source_B_home_systems_reality.csv` | observed off-grid home systems |
| `Data/2025/sufficiency/share_dispersion_final_BC.csv` | home-system floors `f_min_PV_HS_GW`, `f_min_HS_DIESEL_GW`, `f_min_BATT_HS_GWh` per cluster; byte-identical copy of `bolivia-energy-data/analyse_GIS_projections/output/share_dispersion_final_BC.csv`, read by `scenarios.py` for the `sufficiency` case |
| `Data/2025/README.md` | which column of which `Technologies.csv` is produced by which notebook, and which are maintained by hand. Read this before regenerating anything. |
| `Data/2025/{reality,reality_access,sufficiency}/README.md`, `Data/2035/README.md`, `Data/2050/README.md` | five byte-identical copies of a note inherited from the upstream model (ENSPRESO, Belgian ESTD, Danish Energy Agency catalogue, EUR_2015 factor 0.958294). They describe European sources, not the BNA data. `Data/2025/README.md` is the only README documenting this repository's data. |

### Provenance

| Horizon | How `Data/` is produced |
|---|---|
| 2025 | `bolivia-energy-data/analyse data ramp/{reality,reality_access,sufficiency}/technologies.ipynb` writes to its own `output_energyscope/`; the copy into `Data/2025/` is **manual and historically partial**. Several columns are maintained directly in `Data/` with no notebook behind them (`Data/2025/README.md`, section "Columns maintained by hand"). |
| 2035, 2050 | `bolivia-energy-data/analyse data ramp/{2035,2050}/technologies.ipynb` writes **directly into `Data/2035/*` and `Data/2050/*`** and reprints `reg_*.dat` into `case_studies/`. Running them is a deployment, not a dry run. |
| all | Base catalogue: `analyse data ramp/data/Technologies.csv`, the SA-PA reference by Pablo Jimenez Zabalaga. |

`share_dispersion` in `Data/**/Misc.json` is not authored by any notebook: it is written by
`scripts/calibrate_share_dispersion.py` from a solve (see 1.4).

---

## 4. The three analysis notebooks

All three live in `scripts/`, resolve the repository root themselves, insert it at the front of
`sys.path` (another EnergyScope fork may be pip-installed under the same name `esmc`), and read
solved outputs only. **They do not run the solver and need neither AMPL nor CPLEX.**
Figures are displayed inline and not written to disk. Markdown headings carry
`[manuscript figure N]` when the cell produces a thesis figure, `[cross-check, not in the
manuscript]` or `[complementary, not in the manuscript]` when it does not.

### 4.1 `scripts/analyse_resultats.ipynb` — 2025 chapter

| | |
|---|---|
| Reads | `case_studies/C1_C2_C3_C4_C5/norte_amazonia_{reality_2025, reality_2025_phase2, reality_access_2025, access_transition_2025, sufficiency_2025}/outputs/` and `_sensitivity_DEC_SOLAR_fmax0/{reality_access,sufficiency}/outputs/` |
| Also reads | `bolivia-energy-data/analyse_GIS_projections/output/2024/cluster_summary.csv`; `bolivia-energy-data/projections/output/backtest_clusters_2024.csv` |
| Produces | inline figures only |
| Also reads | `case_studies/C1_C2_C3_C4_C5/norte_amazonia_sufficiency_2025/outputs/hourly_results/{F_t,Storage_power,R_t_exterior,Exchanges}.csv` — figure 17 only. These four files are the only `hourly_results/` content committed. |
| Manuscript figures | **15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 29, 33, 35** |

Figure map: 15 current system vs universal access by cluster · 16 decomposition of the annual
cost of universal access · 17 hourly electric dispatch vs demand · 18 electricity production by
cluster and technology · 19 hot water by technology and cluster · 20 cost decomposition by
cluster · 21 effect of blocking the solar water heater · 22 annual electricity production, five
2025 scenarios · 23 the three steps from the current system to universal sufficiency · 24 the
five scenarios compared, annual cost · 25 annual cost against emissions · 29 normalised weights
of the twelve clustering variables · 33 deviation of the predicted 2024 population from the
census · 35 BNA households by electricity source, 2024 census.

### 4.2 `scripts/analyse_projections.ipynb` — 2035/2050 chapter

| | |
|---|---|
| Reads | `case_studies/C1_C2_C3_C4_C5/norte_amazonia_{no_transition,early_access,late_access}_{2035,2050}/outputs/`, `norte_amazonia_early_access_brazil_2050/outputs/`, `norte_amazonia_reality_2025/outputs/` |
| Also reads | `bolivia-energy-data/projections/output/{menages_projetes.csv, split_abc_projete.csv}`; `bolivia-energy-data/analyse data ramp/2050/output_energyscope_2050/vintage_registry.csv`; `bolivia-energy-data/exctraction of data/output/CSV_final.csv` |
| Produces | inline figures only |
| Manuscript figures | **11, 12, 26, 27, 28** |

Figure map: 11 population and households diverge · 12 access rate by cluster under the two
trajectories · 26 annual cost of the seven projection runs (reconstructed, not LP raw) ·
27 regional PV_UTILITY capacity · 28 cost and emission trajectories. A final section prints key
figures for cross-checking against the chapter text.

### 4.3 `scripts/analyse_sankey.ipynb` — current-system Sankey

| | |
|---|---|
| Reads | `case_studies/C1_C2_C3_C4_C5/norte_amazonia_reality_2025/outputs/` |
| Also reads | nothing outside the repository |
| Produces | `case_studies/**/regional_results/input2sankey_{C1..C5,Total}.csv` and `generated_sankey_Total.html` — regenerated, git-ignored |
| Manuscript figures | **14** |

Uses `esmc.postprocessing.draw_sankey`. The section "Flow totals per layer" is a cross-check,
not a manuscript figure.

---

## 5. Prerequisites

| | |
|---|---|
| Python | 3.13 (results and notebook outputs produced with 3.13.9, Anaconda) |
| Packages | `numpy` 2.3.5, `pandas` 2.3.3, `scikit-learn` 1.7.2, `matplotlib` 3.10.6, `seaborn` 0.13.2, `plotly` 6.3.0, `gitpython` 3.1.45, `setuptools_scm`, `ipykernel` 6.31.0, `nbconvert` 7.16.6, `amplpy` 0.16.0 |
| Environment file | `environment.yml` (`conda env create -f environment.yml`, environment name `energyscope`) |
| Package install | `pip install -e .` (`setup.py`, package `esmc`) — optional; the scripts insert the repository root into `sys.path` themselves |
| Solver | AMPL (tested: 20250811, 64-bit) with CPLEX (tested: 22.1.2) |
| Licences | AMPL and CPLEX each require a licence. Free academic licences exist for both. Tested with an AMPL academic licence file at `~/AMPL/ampl.lic`. |
| RAM | measured on 32 GB. The AMPL process reached 10.2 GB during `reality` (five clusters, 16 typical days); the Python process adds a few hundred MB. 16 GB is not tested. |

### Where AMPL is looked up

`paths.py`:

1. `ENERGYSCOPE_AMPL_PATH` if set;
2. else `~/AMPL` if that directory exists;
3. else `None`, which tells `amplpy` that `ampl` is on `PATH`.

### Configuration knobs

| Environment variable | Default | Effect |
|---|---|---|
| `ENERGYSCOPE_AMPL_PATH` | `~/AMPL` or `PATH` | AMPL installation directory |
| `ENERGYSCOPE_BED_PATH` | `../bolivia-energy-data` | the `bolivia-energy-data` repository |

Number of typical days is fixed at 16 in `scripts/run.py` (`tds = 16`). CPLEX option sets are in
`CPLEX` in `scripts/scenarios.py`: `reality` and `projection` use dual simplex with a 172800 s
time limit; `sufficiency` uses the barrier without crossover (`baropt`, `crossover=0`,
`comptol=1e-4`).

---

## 6. Dependency on `bolivia-energy-data`

Expected as a sibling directory of this repository, or pointed at by `ENERGYSCOPE_BED_PATH`.
`paths.bolivia_file()` raises a `FileNotFoundError` naming the missing file and the expected
repository location.

| File | Read by | For |
|---|---|---|
| `analyse_GIS_projections/output/{2024,2035,2050}/cluster_summary.csv`, column `demande_dispersee_GWh` | `scripts/calibrate_share_dispersion.py` | the dispersed-demand target of the `share_dispersion` calibration. `2024` is used for the 2025 horizon. |
| `analyse_GIS_projections/output/2024/cluster_summary.csv` | `scripts/analyse_resultats.ipynb` | grid-extension infrastructure figures |
| `projections/output/backtest_clusters_2024.csv` | `scripts/analyse_resultats.ipynb` | manuscript figure 33 |
| `projections/output/menages_projetes.csv`, `projections/output/split_abc_projete.csv` | `scripts/analyse_projections.ipynb` | manuscript figures 11 and 12 |
| `analyse data ramp/2050/output_energyscope_2050/vintage_registry.csv` | `scripts/analyse_projections.ipynb` | 2050 vintage-aware capacity registry |
| `exctraction of data/output/CSV_final.csv` | `scripts/analyse_projections.ipynb` | historical demand series |

### What works without it

| | Needs `bolivia-energy-data`? |
|---|---|
| `python scripts/run.py <case>` — any of the 22 | **No.** Everything it reads is under `Data/`, including `share_dispersion_final_BC.csv`, which is vendored into `Data/2025/sufficiency/`. |
| `python scripts/solve.py <group>` | **Yes**, for the calibration step between the two passes. `--only pass1` and `--only pass2` avoid it. |
| `scripts/analyse_sankey.ipynb` | **No.** |
| `scripts/analyse_resultats.ipynb` | **Partly.** Everything up to the 2025 figures runs; figure 33 and the infrastructure cells fail. |
| `scripts/analyse_projections.ipynb` | **Partly.** Figures 11, 12 and part of 26–28 fail. |

`bolivia-energy-data` is also where `Data/2035/*` and `Data/2050/*` are generated from, but
those catalogues are committed here, so regenerating them is not needed to reproduce the results.

### 6.1 Provenance audit of `Data/` against `bolivia-energy-data`

164 file pairs checked on 2026-09-16, read-only. 97 byte-identical, 67 differing. Every
difference is in `Data/2025/`; `Data/2035/` and `Data/2050/` still match their source exactly.
All 50 `Demands.csv` files are byte-identical at every horizon.

| Class | Files | State | Size of the gap |
|---|---|---|---|
| A. `f_max` unblocked to `1e15` | `2025/reality_access/C{1..5}`, `2025/sufficiency/C{1..5}`, `2025/reality/C4` — `Technologies.csv` | **intentional**, `Data/` is authoritative | the notebook writes `0.0`, `Data/` writes `1e15` on `PV_UTILITY`, `BATT_LI`, `DEC_SOLAR`, `TS_DEC_DIRECT_ELEC`, `TS_DEC_BOILER_GAS` (+ the C4 pipelines). Documented in `Data/2025/README.md`, "Columns maintained by hand". 3 to 13 cells per file. |
| B. `Technologies.csv`, 2035 and 2050, all 40 files | source carries 8 extra descriptive columns (`Category`, `Subcategory`, `Technologies name`, `c_inv`, `c_maint`, `gwp_constr`, `lifetime`, `Comment`) | **current** | numerically identical on the 7 shared parameter columns, all 272 rows |
| C. `HS_DIESEL` `f_min_prod` / `f_max_prod` | `2025/reality/C{1,2,3,5}/Technologies.csv` | rounding | 2 cells each, 0.01–0.02 % (e.g. C1 `0.6595` → `0.6594`) |
| D. **`Time_series.csv` reprofiled upstream** | `2025/sufficiency/C{1..5}`, `2025/reality/C4` — 6 files | **`Data/` is one generation behind** | annual sums identical to 15 digits; only the hourly *shape* moved. `ELECTRICITY` up to 5.7–6.4 % on a single hour, `SPACE_COOLING` up to 54 % (sufficiency C3) and 99.99 % (C2, C5). 8760 to 16425 cells per file. |
| E. `Resources.csv` | `2025/sufficiency/C{1..5}` | **`Data/` is behind** | 4–5 cells: `WOOD` `avail_exterior` source `1e15` → `Data/` `0`; `GAS` `1` → `0`; `GASOLINE` `1` → `1e6` |
| F. `Misc.json` `share_dispersion` | `2025/sufficiency/C{1,3,4}` | **expected** | source holds the pass-1 zero, `Data/` holds the calibrated value (C1 `0.011343298`, C3 `0.001402990`, C4 `0.008029039`). C2 and C5 differ in formatting only, both `0`. |
| G. `Network_exchanges.csv` | `2025/sufficiency/01_EXCH` | `Data/` edited by hand | 14 cells on `tc_min` / `tc_max` |

Dates, for the classes where `Data/` is behind:

| File | source date | `Data/` date | Gap |
|---|---|---|---|
| `Data/2025/sufficiency/C{1..5}/Time_series.csv` | 2026-06-19 | 2026-05-25 | source 25 days newer |
| `Data/2025/reality/C4/Time_series.csv` | 2026-07-14 | 2026-06-19 | source 25 days newer |
| `Data/2025/sufficiency/C{1..5}/Resources.csv` | 2026-06-20 | 2026-06-11 | source 9 days newer |
| `Data/2025/reality/C{1,2,4,5}/Technologies.csv` | 2026-08-04 | 2026-07-27 | source 8 days newer |
| `Data/2035/*`, `Data/2050/*` | 2026-08-03 / 2026-08-18 | 2026-08-18 | current |

Class D is the one that matters. The hourly `ELECTRICITY` and `SPACE_COOLING` profiles of the
2025 catalogues were re-derived in `bolivia-energy-data` after `Data/2025/` was last copied, while
`Data/2035/` and `Data/2050/` were brought onto the new profile. The 2025 horizon therefore runs
on the older shape. Annual energy is unchanged, so this is a reprofiling, not a rescaling: it
moves the typical-day clustering and the hourly dispatch, not the totals. Consistent with the
freeze decision in 1.4, nothing was changed.

---

## 7. Measured runtime per case

Full campaign of 2026-09-16, one run at a time, `python scripts/run.py <case>` with `Data/`
left untouched. Wall clock includes AMPL model generation, k-medoid clustering of the typical
days (except case 16, which reuses them) and the CPLEX solve.

| # | Case | `solve_result_num` | Duration [min] |
|---|---|---|---|
| 1 | `reality` | 0 | 9.9 |
| 2 | `reality_phase2` | 0 | 12.5 |
| 3 | `reality_access` | 0 | 10.4 |
| 4 | `access_transition` | 0 | 18.8 |
| 5 | `sufficiency` | 0 | 6.8 |
| 6 | `no_transition_2035` | 0 | 10.4 |
| 7 | `early_access_2035` | 0 | 13.3 |
| 8 | `late_access_2035` | 0 | 14.7 |
| 9 | `no_transition_2050` | 0 | 41.7 |
| 10 | `early_access_2050` | 0 | 18.2 |
| 11 | `late_access_2050` | 0 | 27.7 |
| 12 | `early_access_brazil_2050` | 0 | 13.3 |
| 13 | `early_access_2050_sens_nodecsolar` | 0 | 15.3 (1) |
| 14 | `late_access_2050_sens_nodecsolar` | 0 | 14.4 |
| 15 | `late_access_2050_sens_battom` | 0 | 13.3 (2) |
| 16 | `early_access_brazil_2050_sens_price003` | 0 | 13.1 |
| 17 | `early_access_brazil_2050_sens_price009` | 0 | 11.1 |
| 18 | `early_access_brazil_2050_sens_vol923` | 0 | 16.5 |
| 19 | `early_access_brazil_2050_sens_vol1857` | 0 | 12.0 |
| 20 | `no_transition_2050_sens_diesel20` | 0 | 10.1 |
| 21 | `reality_access_sens_nodecsolar` | 0 | 11.3 |
| 22 | `sufficiency_sens_nodecsolar` | 0 | 6.7 |

Range 6.7 to 41.7 min per case; 22 cases in 5.4 h of solving, run one at a time.

(1) Wall clock 303.7 min, of which 288.4 min (14:50 to 19:38) the machine was in standby
according to the Windows System log; 15.3 min is the active time.
(2) A first attempt was killed after 6 min by a planned Windows Update restart. The figure is the
successful rerun.

Outputs of all 22 cases were compared with the committed reference on `TotalCost.csv`,
`Cost_breakdown.csv`, `Assets.csv`, `Gwp_breakdown.csv`, `Year_balance.csv` and `Resources.csv`,
total and per cluster. TotalCost agrees to at most 1.1e-7 relative, except `sufficiency`
(9.7e-5) and `sufficiency_sens_nodecsolar` (1.3e-6), the two cases solved by barrier without
crossover at `comptol=1e-4`. No cost or emission value differs by more than 0.1 % of the case's
total cost. The larger relative differences are alternative optima of equal cost: throughput of
the zero-cost `HVAC_LINE`, `DEC_SOLAR`/`DEC_DIRECT_ELEC` and battery dispatch splits, and
fuel-storage sizes in the two barrier cases.

---

## 8. What would block an outside user

1. **AMPL and CPLEX licences.** Neither is installable from conda and neither ships with the
   repository. Without them nothing solves; the notebooks still run on the committed outputs.
2. **`bolivia-energy-data` is a separate repository** and is not vendored. Without it,
   `scripts/solve.py`'s calibration step and part of two notebooks fail. `run.py` is unaffected.
3. **Memory.** The AMPL process reached 10.2 GB on a 32 GB machine. Runs on 16 GB were not tested.
4. **`Data/**/Misc.json` is rewritten in place by the calibration.** Running
   `python scripts/solve.py campaign` on an already-calibrated `Data/` changes the model inputs
   and does not reproduce the published results (see 1.4). Back `Data/` up first.
5. **`00_td_dat/` is shared by every case.** Parallel runs corrupt it. There is no lock.
6. **`solve_result_num` must be checked after every run.** Complete-looking output files are
   written even when the solve was rejected.
7. **No test suite and no CI.** Correctness is established by comparing outputs against the
   committed reference.
8. **The 2025 catalogues are not reproducible from the notebooks.** Several columns of
   `Data/2025/**/Technologies.csv` are maintained by hand and the notebooks that nominally
   produce the others are known to be partly stale; re-running them overwrites good values
   (`Data/2025/README.md`).
9. **Long solves.** 6.7 to 41.7 min per case (section 7). The CPLEX time limit is set to 172800 s
   (48 h) per run. A machine that sleeps or restarts mid-run kills the solve; nothing resumes it.
10. **Hourly results are not published** except the four `sufficiency` files figure 17 reads
    (21.7 MB). Any other hourly analysis requires re-solving the case, which requires the licences.
11. **`Data/2025` is one generation behind `bolivia-energy-data`** on six `Time_series.csv`
    files (see 6.1, class D). This is a deliberate freeze, not an oversight, but anyone
    regenerating `Data/2025` from the notebooks will get a different hourly profile and
    different results.
10. **Windows paths.** Nothing in the code hardcodes a drive letter — `paths.py` derives the
    root from `__file__` — but the runtimes above and the AMPL lookup (`~/AMPL`) were measured
    on Windows.
