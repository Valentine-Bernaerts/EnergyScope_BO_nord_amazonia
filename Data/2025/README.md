# How the catalogues under `Data/` are actually produced

Established 2026-08-17 by auditing every `Technologies.csv` against the notebook that is supposed
to generate it. Read this before rerunning any notebook in `bolivia-energy-data/analyse data ramp/`.

## The trap this file exists to prevent

**For the 2025 horizon, no script copies notebook output into `Data/`.** The notebooks write to
`analyse data ramp/<scenario>/output_energyscope/C{k}/Technologies.csv`; the copy into
`Data/2025/<scenario>/C{k}/` is manual and has historically been *partial* — some columns were
copied, others were edited straight into `Data/` and never propagated back.

The consequence: a notebook can be months behind the catalogue it nominally produces, and rerunning
it silently overwrites good values with stale ones. That happened. On 2026-08-17 the
`reality_access` and `sufficiency` notebooks still wrote the superseded independent-breakeven
dispersed-demand figures (3.44 GWh total) while `Data/` had been on the greedy-tree figures
(0.532 GWh total) since that morning — a factor of 8.7. Both notebooks have since been repointed.

**For 2035 and 2050 the opposite is true**: `analyse data ramp/2035/technologies.ipynb` and
`.../2050/technologies.ipynb` write **directly into `Data/2035/*` and `Data/2050/*`**, and also
reprint `reg_*.dat` into `case_studies/C1_C2_C3_C4_C5/`. Running them is a deployment, not a
dry run. Never run them while a solve series is in flight.

## Who writes what

| Notebook | Writes to | Reaches `Data/` how |
|---|---|---|
| `analyse data ramp/reality/technologies.ipynb` | `reality/output_energyscope/` | manual copy |
| `analyse data ramp/reality_access/technologies.ipynb` | `reality_access/output_energyscope/` | manual copy |
| `analyse data ramp/sufficiency/technologies.ipynb` | `sufficiency/output_energyscope/` | manual copy |
| `analyse data ramp/2035/technologies.ipynb` | `Data/2035/<scenario>/` **directly**, + `case_studies/.../reg_*.dat` | direct write |
| `analyse data ramp/2050/technologies.ipynb` | `Data/2050/<scenario>/` **directly**, + `case_studies/.../reg_*.dat` | direct write |

## Columns a 2025 notebook really produces

Only these. Everything else in the file is inherited from the base
(`analyse data ramp/data/Technologies.csv`, the SA-PA reference by Pablo Jimenez Zabalaga) or from
the previous scenario in the chain, and is **not** authored by the notebook.

| Column / rows | Produced by | Source |
|---|---|---|
| `f_min` of `PV_HS`, `HS_DIESEL`, `BATT_HS` | sufficiency, reality_access | `analyse_GIS_projections/output/share_dispersion_final_BC.csv` — brownfield credit on the off-grid fleet dispersed Source-B households already own |
| `f_max_prod` of `PV_HS` and `HS_DIESEL` (dual cap) | sufficiency, reality_access | `analyse_GIS_projections/output/2024/cluster_summary.csv`, column `demande_dispersee_GWh` |
| `f_min` of `GENSET_DIESEL` | sufficiency | AETN 2024, Cuadro VI-1, MW active |
| `f_min` of `STOVE_WOOD`, `STOVE_LPG` | sufficiency | Census 2024 cooking practices × field-study energy intensities |
| `f_min` of `PV_UTILITY` | sufficiency | AETN 2024 — Cobija only, 5.10 MW |
| `f_min` of the `POPULATION_SCALED` list | sufficiency | SA-PA base value × cluster household share |
| `fmin_perc`/`fmax_perc` of `LED_*`, `f_max` of `CONVENTIONAL_*` | sufficiency | LED-only lighting rule |
| `f_min_prod` of `GENSET_DIESEL`, `DEC_DIRECT_ELEC`, `DEC_BOILER_GAS` | reality_access | hardcoded parameters — `F_year` dispatch of the solved reality run, not recomputable upstream |

## Columns maintained by hand in `Data/`, with no notebook behind them

Do not expect any notebook to reproduce these. No script in either repository writes them.

**1. `f_max` unblocked to `1e15`.** On all five clusters: `PV_UTILITY`, `DEC_SOLAR`, `BATT_LI`,
`TS_DEC_DIRECT_ELEC`, `TS_DEC_BOILER_GAS`. On C4 additionally `GAS_PIPELINE`, `PLANE`,
`DIESEL_PIPELINE`, `GASOLINE_PIPELINE`, `LPG_PIPELINE`, `LFO_PIPELINE`, `JET_FUEL_PIPELINE`, and
`LNG_STORAGE` in the opposite direction (`0.0` in `Data/`, `1e15` in the notebook). The notebooks
write `0.0`, which would lock investment out of a scenario that is meant to be free to invest.
`Data/` is right here; the notebooks are wrong and are deliberately left alone.

**2. The population-scaled `f_min` block of C3.** See the anomaly below.

## Known anomaly: C3 carries C4's household share

`Data/2025/reality/C3/Technologies.csv` and `Data/2025/reality_access/C3/Technologies.csv` apply
the population-scaling rule with **C4's** household share instead of C3's. The documented rule is
`f_min = SA-PA base × cluster_households / total_households`. Cluster totals (Census 2024) are
C1 8 178, C2 802, C3 40 298, C4 15 752, C5 15 564, total 80 594.

`Data/2025/sufficiency` is **clean** — all five clusters match their notebook exactly on `f_min`.
Since the chain runs sufficiency → reality → reality_access, this localises the error to the
reality step: it was introduced when `reality/C3` was assembled, and `reality_access` inherited it
by construction. C1, C2, C4 and C5 are unaffected in all three scenarios.

The 17 affected rows in C3 are uniformly `15752 / 40298 = 0.390888` of the value the rule gives:
`IND_BOILER_WOOD`, `IND_BOILER_OIL`, `IND_BOILER_DIESEL`, `DEC_BOILER_GAS`, `DEC_DIRECT_ELEC`,
`DIESEL_STORAGE`, `JET_FUEL_STORAGE`, `GASOLINE_STORAGE`, `LPG_STORAGE`, `STOVE_NG`, `STOVE_OIL`,
`COMM_MACHINERY_DIESEL`, `AGR_MACHINERY_DIESEL`, `FISH_MACHINERY_DIESEL`, `FISH_MACHINERY_EL`,
plus `STOVE_WOOD` (ratio 0.823353) and `STOVE_LPG` (0.324922), which are not population-scaled but
computed per cluster from cooking data and therefore carry C4's cooking counts rather than a
rescaling of C3's.

Cross-check that pins it down: comparing `Data/2025/reality_access/C3` against the notebook's **C4**
output makes all 17 rows vanish, while the genuinely per-cluster values (`GENSET_DIESEL`, the
`f_min_prod` parameters, the SHS rows) then appear as differences — i.e. the C3 file was built on a
C4-scaled base and correctly overwritten afterwards for the cluster-specific rows only.

C3 is the largest cluster (Riberalta, Guayaramerín, Puerto Gonzalo Moreno). Its legacy-fleet floors
in `Data/` are therefore about 2.56× too small. **Documented, not corrected** — correcting it moves
the cost of every 2025 scenario and is a modelling decision, not a cleanup.

## Two classifications of dispersed households — only one is current

| | Communities dispersed | Total dispersed demand | Where |
|---|---|---|---|
| Independent break-even (superseded) | 253 / 697 | 4.607 GWh/y | `community_breakeven_detail_BC.csv`, column `dispersed` |
| Greedy tree with definitive rejection (**current**) | 71 / 697 | 0.532 GWh/y | `cluster_summary.csv`, column `demande_dispersee_GWh` |

`demande_dispersee_GWh` per cluster: 2024 → 0.1794 / 0 / 0.1107 / 0.2419 / 0 ·
2035 → 0.17 / 0 / 0.0976 / 0.1991 / 0 · 2050 → 0.1954 / 0 / 0.1132 / 0.1695 / 0.

Summing `HH` over the `dispersed` flag of `community_breakeven_detail_BC.csv` reproduces the
superseded classification. Do not use it.

## `share_dispersion` in `Misc.json`

Written by `EnergyScope/scripts/calibrate_share_dispersion.py` after the pass-1 solve. It is an **energy**
ratio, `target / (target + local supply excluding TECH_HS)`, never the household ratio published in
`share_dispersion_final_BC.csv`. C2 and C5 are forced to 0. Substituting one for the other is the
error that script exists to prevent.

## Before rerunning a notebook

1. Check what it writes (table above). For 2035/2050 that includes `Data/` and `case_studies/`.
2. Check no solve is running.
3. After running, diff the output against `Data/` and confirm that the only differences are the
   hand-maintained columns listed above — not new ones.
