# Standalone IIS diagnostic for reality_access (2026-07-21).
# Reproduces the exact reality_access setup from run.py (selected_case='reality_access',
# i=1 reusing the on-disk TD cache where the infeasibility is already reproducible),
# but calls solve_esom(iis_diagnostic=False) instead of the normal solve_esom().
# This is a read-only diagnostic: it stops right after the solve and does NOT call
# get_year_results()/prints_esom() on the infeasible model, since no output of a
# rejected/infeasible run should be interpreted as a scenario result.
#
# run.py itself is left untouched (solve_esom() there keeps its default
# iis_diagnostic=False), so normal (feasible) runs are unaffected by this file.

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
save_hourly = ['Resources', 'Exchanges', 'Assets', 'Storage', 'Curt']

# Reuse the on-disk TD cache (i=1): the infeasibility is already reproducible with it,
# no need to regenerate the typical days.
i = 1

config = {'case_study': case_study,
          'comment': 'floors_zero_test',
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
    'log_file': str(my_model.cs_dir / 'log_floors_zero_test.txt'),
    'presolve': 200,
    'times': 1,
    'gentimes': 1,
    'cplex_options': ' '.join(reality_cplex),
}
my_model.set_esom(ampl_path=ampl_path, ampl_options=reality_ampl_options)

print('=== STARTING IIS DIAGNOSTIC SOLVE (iisfind=1) ===')
my_model.solve_esom(iis_diagnostic=False)

out_dir = my_model.cs_dir / 'outputs'
out_dir.mkdir(parents=True, exist_ok=True)
if my_model.esom.iis_cons is not None:
    my_model.esom.iis_cons.to_csv(out_dir / 'IIS_constraints.csv', index=False)
    print(f"Saved {len(my_model.esom.iis_cons)} IIS constraints to {out_dir / 'IIS_constraints.csv'}")
if my_model.esom.iis_vars is not None:
    my_model.esom.iis_vars.to_csv(out_dir / 'IIS_variables.csv', index=False)
    print(f"Saved {len(my_model.esom.iis_vars)} IIS variables to {out_dir / 'IIS_variables.csv'}")

my_model.esom.ampl.close()
print('=== IIS DIAGNOSTIC DONE ===')
