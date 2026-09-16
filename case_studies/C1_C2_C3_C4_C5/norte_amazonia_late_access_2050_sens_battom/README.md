# `norte_amazonia_late_access_2050_sens_battom` — BATT_LI fixed-O&M sensitivity

Single-variable sensitivity on `late_access` 2050, solved 2026-08-09 (`solve_result_num = 0`,
CPLEX 22.1.2 `optimal solution; objective 42.38479565`).

**The one variable.** `BATT_LI` `c_maint` = **10.647** M EUR/GWh/y instead of the catalogue's
0.658412583. Source: NREL ATB 2024, fixed O&M for utility-scale lithium storage = 2.5% of capital
cost per year, applied to the 2025 catalogue `c_inv` (0.025 x 425.88), so the value is the same at
2035 and 2050. Everything else is identical to `norte_amazonia_late_access_2050`, including the
typical days (the shared `00_td_dat/` cache was reused, not recomputed).

**`reg_technologies.dat` in this folder is the only file in the repository that still carries
10.647, and it must stay that way** — it is the solved input of this run. It differs from the
central run's `reg_technologies.dat` on exactly 5 lines (C1-C5 `BATT_LI` `c_maint`); every other
`.dat` is identical apart from a set-ordering line in `indep.dat`.

The value reached this run through the catalogue at solve time
(`NREL_ATB_C_MAINT_FRACTION` in `bolivia-energy-data/analyse data ramp/2050/technologies.ipynb`).
Both that constant and the four `Data/2050/*/02_REF_REGION/Technologies.csv` files have since been
reverted to 0.658412583, so the central 2050 runs reproduce their published figures. To reproduce
*this* run, `scripts/run.py` now applies 10.647 as an in-memory override under
`selected_case = 'late_access_2050_sens_battom'`.

**Result.** Reconstructed cost 53.064 -> 57.093 M EUR/y (+4.029, +7.59%); LP raw 38.356 -> 42.385;
vintage adjustment unchanged at 14.708. Battery fleet 0.40503 -> 0.40024 GWh (-1.18%), i.e. the
optimiser absorbs 99.6% of the shock rather than building less storage. Locked-supply gap vs
`no_transition` closes from 67.951 to 63.923 M EUR/y.
