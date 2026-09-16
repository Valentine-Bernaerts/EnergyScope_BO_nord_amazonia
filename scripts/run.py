# Norte Amazonica (BNA) multi-cell run, 5 clusters: C1 (Beni/Ixiamas), C2 (Bolpebra),
# C3 (Riberalta/Guayaramerin/Puerto), C4 (Central Pando), C5 (Cobija).
#
#     python scripts/run.py <case>        # default: reality
#
# What each case changes is declared in scripts/scenarios.py.
# Requires AMPL with the CPLEX solver; both need a licence.

import numpy as np
from pathlib import Path

# additional line for VS studio
import sys

import pandas as pd

# this repository must come first: another EnergyScope fork is pip-installed under the same name
ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / 'scripts')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from esmc import Esmc
from esmc.common import bo_country_code, CSV_SEPARATOR
from paths import AMPL_PATH, RUN_LOGS
from scenarios import CASES, ampl_options, apply_case

selected_case = sys.argv[1] if len(sys.argv) > 1 else 'reality'
if selected_case not in CASES:
    raise SystemExit("unknown case '%s'\nvalid cases:\n  %s"
                     % (selected_case, '\n  '.join(CASES)))
case = CASES[selected_case]
year, scenario, case_study = case.year, case.data, case.study

# defining cases
cases = [case_study]

# costs_opt = {'ref': 1534711.614}

no_imports = ['GASOLINE', 'DIESEL', 'LFO', 'JET_FUEL', 'GAS', 'COAL', 'H2', 'AMMONIA', 'METHANOL']

# number of typical days (check that tse<0.22)
tds = 16

print('Nbr_TDs', tds)

# specify ampl_path (set None if ampl is in Path environment variable or the path to ampl if not)
ampl_path = AMPL_PATH

# info to switch off unused constraints
#gwp_limit_overall = None
gwp_limit_overall = None
re_share_primary = None
f_perc = True

save_hourly = ['Resources', 'Exchanges', 'Assets', 'Storage', 'Curt']

i = 0
if case.reuse_td:
    i = 1

for c in cases:

    print(c)

    # define configuration
    config = {'case_study': c,
              'comment': 'none',
              'regions_names': ['C1', 'C2', 'C3', 'C4', 'C5'],  # 8 full regions needs ~16GB RAM
              'gwp_limit_overall': gwp_limit_overall,
              're_share_primary': re_share_primary,
              'f_perc': f_perc,
              'year': year,
              'scenario': scenario}

    # initialize EnergyScope Multi-cells framework
    my_model = Esmc(config, nbr_td=tds)

    # use this repo's paths, not the template repo's
    current_project = ROOT
    my_model.project_dir = current_project
    my_model.dat_dir = current_project / 'case_studies' / my_model.space_id / '00_td_dat'
    my_model.cs_dir = current_project / 'case_studies' / my_model.space_id / my_model.case_study
    my_model.dat_dir.mkdir(parents=True, exist_ok=True)
    my_model.cs_dir.mkdir(parents=True, exist_ok=True)

    # read the indep data
    my_model.read_data_indep()

    # initialize the different regions and reads their data
    my_model.init_regions()

    #mod_path = [my_model.cs_dir / 'ESMC_model_AMPL_BAU.mod',
    #            my_model.cs_dir / 'ESMC_obj_TotalCost_BAU.mod']

    # update some data
    ft_to_drop = ['BIOMASS_TO_GASOLINE', 'BIOMASS_TO_DIESEL', 'BIOWASTE_TO_GASOLINE', 'BIOWASTE_TO_DIESEL',
                  'POWER_TO_GASOLINE', 'POWER_TO_DIESEL', 'H2_TO_GASOLINE', 'H2_TO_DIESEL']
    my_model.ref_region.data['Technologies'] = my_model.ref_region.data['Technologies'].drop(index=ft_to_drop)
    my_model.data_indep['Layers_in_out'] = my_model.data_indep['Layers_in_out'].drop(index=ft_to_drop)
    # force to be 100% renewable
    for r_code, region in my_model.regions.items():
        # fossil-free
        # region.data['Resources'].loc[no_imports, 'avail_exterior'] = 0

        # drop FT GASOLINE and FT DIESEL for clarity
        region.data['Technologies'] = region.data['Technologies'].drop(index=ft_to_drop)

    # according to scenario change some inputs
    if c.startswith('low_demand'):
        obj = costs_opt['low_demand']
        # read low demand
        ld_all = pd.read_csv(my_model.project_dir / 'Data' / 'exogenous_data' / 'regions' / 'Low_demands_2050.csv',
                             header=0, index_col=[0, 1], sep=CSV_SEPARATOR) * 1000
        for r_code, region in my_model.regions.items():
            # update demand in each region
            region.data['Demands'].update(ld_all.loc[(r_code, slice(None)), :].droplevel(level=0, axis=0))
            # no short haul flights
            region.data['Misc']['share_short_haul_flights_min'] = 0
            region.data['Misc']['share_short_haul_flights_max'] = 1e-4
    elif c.startswith('nuc'):
        obj = costs_opt['nuc']
        # read nuclear projections
        nuc_all = pd.read_csv(my_model.project_dir / 'Data' / 'exogenous_data' / 'regions' / 'nuclear_2050.csv',
                              header=0, index_col=0, sep=CSV_SEPARATOR)
        for r_code, region in my_model.regions.items():
            # force to install nuclear
            region.data['Technologies'].loc['NUCLEAR_SMR', 'f_min'] = nuc_all.loc[r_code, 'Nuclear']
            region.data['Technologies'].loc['NUCLEAR_SMR', 'f_max'] = nuc_all.loc[r_code, 'Nuclear'] + 1e-4
    #else:
        #obj = costs_opt['ref']

    apply_case(case, my_model, current_project)

    # for near-optimal space exploration with epsilon optimality
    if 'epsilon' in c:
        my_model.data_indep['Misc_indep']['total_cost_optimum'] = obj
        my_model.data_indep['Misc_indep']['epsilon'] = 0.05

    if c.endswith('epsilon_onshore_re'):
        my_model.data_indep['Misc_indep']['power_density_won'] = 0.0088
        my_model.sets['ONSHORE_RE'] = ['PV_UTILITY', 'PT_POWER_BLOCK', 'ST_POWER_BLOCK', 'WIND_ONSHORE']
        mod_path = [my_model.cs_dir / 'ESMC_model_AMPL.mod',
                    my_model.cs_dir / 'epsilon_models' / 'epsilon_onshore_re.mod']
    elif c.endswith('epsilon_local_biomass'):
        my_model.sets['BIOMASS'] = ['WOOD', 'WET_BIOMASS', 'ENERGY_CROPS_2', 'BIOMASS_RESIDUES', 'BIOWASTE']
        mod_path = [my_model.cs_dir / 'ESMC_model_AMPL.mod',
                    my_model.cs_dir / 'epsilon_models' / 'epsilon_local_biomass.mod']
    elif c.endswith('epsilon_elec_grid'):
        mod_path = [my_model.cs_dir / 'ESMC_model_AMPL.mod',
                    my_model.cs_dir / 'epsilon_models' / 'epsilon_elec_grid.mod']

    # Initialize and solve the temporal aggregation algorithm:
    # if already run, set algo='read' to read the solution of the clustering
    # else, set algo='kmedoid' to run kmedoid clustering algorithm to choose typical days (TDs)
    if i==0:
        my_model.init_ta(algo='kmedoid', ampl_path=ampl_path)
    else:
        my_model.init_ta(algo='read', ampl_path=ampl_path)

    # Print the time related data of the energy system optimization model using the TDs to represent it
    my_model.print_td_data()

    # Print data
    my_model.print_data(indep=True)

    # Set the Energy System Optimization Model (ESOM) as an ampl formulated problem
    if 'epsilon' in c:
        mod_path[1].parent.mkdir(parents=True, exist_ok=True)
        my_model.set_esom(ampl_path=ampl_path, mod_path=mod_path)
    else:
        my_model.set_esom(ampl_path=ampl_path,
                          ampl_options=ampl_options(case, my_model, RUN_LOGS))

    # Solving the ESOM
    my_model.solve_esom()

    # Getting and printing year results
    my_model.get_year_results(save_hourly=save_hourly)
    my_model.prints_esom(inputs=True, outputs=True, solve_info=True, save_hourly=save_hourly)

    # delete ampl object to free resources
    my_model.esom.ampl.close()

    i+=1
