# Standalone feasopt diagnostic for reality_access (2026-07-21).
# The iisfind conflict refiner is pathological here (it reports the genuinely
# infeasible reality_access LP as feasible, with CPLEX's own tolerance-violation
# warnings) so it cannot produce a usable IIS constraint list. This script instead:
#   1. Reproduces the plain, un-relaxed infeasible solve (i=1, cached TDs, no
#      iisfind/feasopt options) -- same config that reproducibly returns
#      solve_result_num=200.
#   2. Calls OptiProbl.run_feasopt() directly (CPLEX feasopt=2: minimal relaxation
#      that restores feasibility), passing the FULL constraint-name universe
#      instead of a pre-computed IIS list (none exists, since iisfind never
#      flagged a conflict on this model).
#   3. Reports every constraint whose relaxed body violates its original bound
#      (delta_lb/delta_ub > 0), sorted by delta descending -- the minimal set of
#      constraints (and by how much) that must relax for reality_access to solve.
#
# Read-only diagnostic: does not call get_year_results()/prints_esom() on either
# the infeasible or the feasopt-relaxed model, since neither is a valid scenario
# result to report as output.

import sys
from pathlib import Path

sys.path.insert(0, r'C:\Valen\Tfe\EnergyScope_BO_nord_amazonia')
from esmc import Esmc

year = 2025
scenario = 'reality_access'
case_study = f'norte_amazonia_reality_access_{year}'

tds = 16
ampl_path = r'C:\Users\valen\AMPL'
gwp_limit_overall = None
re_share_primary = None
f_perc = True

# Reuse the on-disk TD cache (i=1): infeasibility is already reproducible with it,
# no need to regenerate typical days for this diagnostic.
i = 1

config = {'case_study': case_study,
          'comment': 'feasopt_diagnostic',
          'regions_names': ['C1', 'C2', 'C3', 'C4', 'C5'],
          'gwp_limit_overall': gwp_limit_overall,
          're_share_primary': re_share_primary,
          'f_perc': f_perc,
          'year': year,
          'scenario': scenario}

my_model = Esmc(config, nbr_td=tds)

current_project = Path(__file__).parents[1]
my_model.project_dir = current_project
my_model.dat_dir = current_project / 'case_studies' / my_model.space_id / '00_td_dat'
my_model.cs_dir = current_project / 'case_studies' / my_model.space_id / my_model.case_study
my_model.dat_dir.mkdir(parents=True, exist_ok=True)
my_model.cs_dir.mkdir(parents=True, exist_ok=True)

my_model.read_data_indep()
my_model.init_regions()

ft_to_drop = ['BIOMASS_TO_GASOLINE', 'BIOMASS_TO_DIESEL', 'BIOWASTE_TO_GASOLINE', 'BIOWASTE_TO_DIESEL',
              'POWER_TO_GASOLINE', 'POWER_TO_DIESEL', 'H2_TO_GASOLINE', 'H2_TO_DIESEL']
my_model.ref_region.data['Technologies'] = my_model.ref_region.data['Technologies'].drop(index=ft_to_drop)
my_model.data_indep['Layers_in_out'] = my_model.data_indep['Layers_in_out'].drop(index=ft_to_drop)
for r_code, region in my_model.regions.items():
    region.data['Technologies'] = region.data['Technologies'].drop(index=ft_to_drop)

# --- Reality access overrides (identical to run.py's norte_amazonia_reality_access_2025 branch) ---
for r_code, region in my_model.regions.items():
    if 'DIESEL' in region.data['Resources'].index:
        region.data['Resources'].loc['DIESEL', 'avail_exterior'] = 1e6
if 'C1' in my_model.regions:
    if 'ELECTRICITY' in my_model.regions['C1'].data['Resources'].index:
        my_model.regions['C1'].data['Resources'].loc['ELECTRICITY', 'avail_exterior'] = 1e6

if i == 0:
    my_model.init_ta(algo='kmedoid', ampl_path=ampl_path)
else:
    my_model.init_ta(algo='read', ampl_path=ampl_path)

my_model.print_td_data()
my_model.print_data(indep=True)

reality_cplex = ['timelimit 172800', 'display=2']
reality_ampl_options = {
    'show_stats': 3,
    'log_file': str(my_model.cs_dir / 'log_feasopt_diagnostic.txt'),
    'presolve': 200,
    'times': 1,
    'gentimes': 1,
    'cplex_options': ' '.join(reality_cplex),
}
my_model.set_esom(ampl_path=ampl_path, ampl_options=reality_ampl_options)

print('=== STEP 1: plain solve (expect infeasible, no iisfind/feasopt) ===')
my_model.solve_esom(iis_diagnostic=False)
print('solve_result_num (plain) =', my_model.esom.ampl.getValue('solve_result_num'))

print('=== STEP 2: feasopt=2 minimal-relaxation resolve ===')
all_conname_df = my_model.esom.ampl.getData('_conname').toPandas()
all_conname = all_conname_df['_conname'].tolist()
print(f'Total constraints in model: {len(all_conname)}')

feasopt_df = my_model.esom.run_feasopt(con_names=all_conname)
print('solve_result_num (feasopt) =', my_model.esom.ampl.getValue('solve_result_num'))

violated = feasopt_df[(feasopt_df['delta_lb'] > 1e-9) | (feasopt_df['delta_ub'] > 1e-9)].copy()
violated['delta'] = violated[['delta_lb', 'delta_ub']].max(axis=1)
violated = violated.sort_values('delta', ascending=False)

out_dir = my_model.cs_dir / 'outputs'
out_dir.mkdir(parents=True, exist_ok=True)
violated.to_csv(out_dir / 'feasopt_relaxed_constraints.csv', index=False)
print(f"Saved {len(violated)} relaxed constraints to {out_dir / 'feasopt_relaxed_constraints.csv'}")
print(violated.to_string())

my_model.esom.ampl.close()
print('=== FEASOPT DIAGNOSTIC DONE ===')
