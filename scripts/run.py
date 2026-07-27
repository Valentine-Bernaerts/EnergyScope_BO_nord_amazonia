# Norte Amazónica 2025 — multi-cell run
# 5 clusters: C1 (Beni/Ixiamas), C2 (Bolpebra), C3 (Riberalta/Guayaramerín/Puerto),
#             C4 (Central Pando), C5 (Cobija)
# Scenario selected below (sufficiency / reality).
# Data folder is chosen automatically from the scenario: Data/2025/<scenario>/

import numpy as np
from pathlib import Path

# additional line for VS studio
import sys

import pandas as pd

sys.path.insert(0, r'C:\Valen\Tfe\EnergyScope_BO_nord_amazonia')
from esmc import Esmc
from esmc.common import bo_country_code, CSV_SEPARATOR

# Choose which case to run:
#   sufficiency / reality / reality_phase2 / reality_access
selected_case = 'sufficiency'

year = 2025

if selected_case == 'sufficiency':
    scenario = 'sufficiency'
    case_study = f'norte_amazonia_sufficiency_{year}'
elif selected_case == 'reality':
    scenario = 'reality'
    case_study = f'norte_amazonia_reality_{year}'
elif selected_case == 'reality_phase2':
    scenario = 'reality'
    case_study = f'norte_amazonia_reality_{year}_phase2'
elif selected_case == 'reality_access':
    scenario = 'reality_access'
    case_study = f'norte_amazonia_reality_access_{year}'
else:
    raise ValueError(f"Unknown selected_case '{selected_case}': "
                     "use 'sufficiency', 'reality', 'reality_phase2' "
                     "or 'reality_access'")

cases = [case_study]

no_imports = ['GASOLINE', 'DIESEL', 'LFO', 'JET_FUEL', 'GAS', 'COAL', 'H2', 'AMMONIA', 'METHANOL']

# number of typical days (check that tse<0.22)
tds = 16

print('Nbr_TDs', tds)

# specify ampl_path (set None if ampl is in Path environment variable or the path to ampl if not)
ampl_path = r'C:\Users\valen\AMPL'

# info to switch off unused constraints
#gwp_limit_overall = None
gwp_limit_overall = None
re_share_primary = None
f_perc = True

save_hourly = ['Resources', 'Exchanges', 'Assets', 'Storage', 'Curt']

# i = 0 regenerates the TD clustering (kmedoid); i = 1 reuses the cache in 00_td_dat/.
# That cache is shared across scenarios, so regenerate after switching scenario.
i = 0  # regenerate TD clustering for sufficiency (shared cache, must not reuse another scenario's)

for c in cases:

    print(c)

    config = {'case_study': c,
              'comment': 'none',
              'regions_names': ['C1', 'C2', 'C3', 'C4', 'C5'],  # 5 clusters (8 full regions needs ~16GB RAM)
              'gwp_limit_overall': gwp_limit_overall,
              're_share_primary': re_share_primary,
              'f_perc': f_perc,
              'year': year,
              'scenario': scenario}

    my_model = Esmc(config, nbr_td=tds)

    # use this repo's paths, not the template repo's
    current_project = Path(__file__).parents[1]
    my_model.project_dir = current_project
    my_model.dat_dir = current_project / 'case_studies' / my_model.space_id / '00_td_dat'
    my_model.cs_dir = current_project / 'case_studies' / my_model.space_id / my_model.case_study
    my_model.dat_dir.mkdir(parents=True, exist_ok=True)
    my_model.cs_dir.mkdir(parents=True, exist_ok=True)

    my_model.read_data_indep()
    my_model.init_regions()

    #mod_path = [my_model.cs_dir / 'ESMC_model_AMPL_BAU.mod',
    #            my_model.cs_dir / 'ESMC_obj_TotalCost_BAU.mod']

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


    # off-grid home systems: PV_HS / HS_DIESEL / BATT_HS, set explicitly per phase
    # share_dispersion_final_BC.csv stores f_min already in GW/GWh, no unit conversion needed
    HOME_TECHS = {'PV_HS': 'f_min_PV_HS_GW',
                  'HS_DIESEL': 'f_min_HS_DIESEL_GW',
                  'BATT_HS': 'f_min_BATT_HS_GWh'}

    if c == 'norte_amazonia_sufficiency_2025':
        # brownfield: real 2025 home fleet is a floor (f_min), f_max stays open
        # overrides the static Technologies.csv f_min, which is not regenerated when this CSV changes
        bc = pd.read_csv(my_model.project_dir / 'Data' / str(year) / scenario
                         / 'share_dispersion_final_BC.csv', index_col='Cluster')
        for r_code, region in my_model.regions.items():
            region.data['Misc']['share_dispersion'] = float(bc.loc[r_code, 'share_dispersion'])
            for tech, col in HOME_TECHS.items():
                if tech in region.data['Technologies'].index:
                    region.data['Technologies'].loc[tech, 'f_min'] = float(bc.loc[r_code, col])
                    region.data['Technologies'].loc[tech, 'f_max'] = 1e15

    # --- Reality: dispatch of the real 2025 system (both reality phases) ---
    if c in ('norte_amazonia_reality_2025', 'norte_amazonia_reality_2025_phase2'):
        # diesel is a purchased fuel; the historical caps are too tight, uncap them
        for r_code, region in my_model.regions.items():
            if 'DIESEL' in region.data['Resources'].index:
                region.data['Resources'].loc['DIESEL', 'avail_exterior'] = 1e6
        # C1's SIN import cap is historical, not physical -> uncap it too
        if 'C1' in my_model.regions:
            if 'ELECTRICITY' in my_model.regions['C1'].data['Resources'].index:
                my_model.regions['C1'].data['Resources'].loc['ELECTRICITY', 'avail_exterior'] = 1e6

        # BATT_HS is negligible in reality -> force to 0 and disable the pv_battery ratio check
        for r_code, region in my_model.regions.items():
            region.data['Misc']['pv_battery_ratio_enforced'] = 0
            if 'BATT_HS' in region.data['Technologies'].index:
                region.data['Technologies'].loc['BATT_HS', 'f_min'] = 0.0
                region.data['Technologies'].loc['BATT_HS', 'f_max'] = 0.0

    # --- Reality phase 2: same dispatch, but unlock utility PV + grid batteries ---
    if c == 'norte_amazonia_reality_2025_phase2':
        # f_min stays brownfield; wind/hydro stay off to match sufficiency
        for r_code, region in my_model.regions.items():
            region.data['Technologies'].loc['PV_UTILITY', 'f_max'] = 1e15
            region.data['Technologies'].loc['BATT_LI', 'f_max'] = 1e15

    # --- Reality access: real 2025 system + universal-access demand ---
    # f_min/f_max floors are baked into Data/2025/reality_access/*/Technologies.csv,
    # so pv_battery_ratio_enforced stays at its default (BATT_HS is a real floor here).
    if c == 'norte_amazonia_reality_access_2025':
        for r_code, region in my_model.regions.items():
            if 'DIESEL' in region.data['Resources'].index:
                region.data['Resources'].loc['DIESEL', 'avail_exterior'] = 1e6
        if 'C1' in my_model.regions:
            if 'ELECTRICITY' in my_model.regions['C1'].data['Resources'].index:
                my_model.regions['C1'].data['Resources'].loc['ELECTRICITY', 'avail_exterior'] = 1e6

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

    if i==0:
        my_model.init_ta(algo='kmedoid', ampl_path=ampl_path)
    else:
        my_model.init_ta(algo='read', ampl_path=ampl_path)

    my_model.print_td_data()
    my_model.print_data(indep=True)

    if c == 'norte_amazonia_sufficiency_2025':
        # same defaults as set_esom's implicit ampl_options, log kept outside the repo cwd
        suff_cplex = ['baropt', 'predual=-1', 'barstart=4', 'comptol=1e-4', 'crossover=0',
                      'timelimit 172800', 'bardisplay=1', 'display=2']
        suff_log_dir = my_model.project_dir.parent / 'run_logs'
        suff_log_dir.mkdir(parents=True, exist_ok=True)
        suff_ampl_options = {
            'show_stats': 3,
            'log_file': str(suff_log_dir / f'{c}_log.txt'),
            'presolve': 200,
            'times': 1,
            'gentimes': 1,
            'cplex_options': ' '.join(suff_cplex),
        }
        my_model.set_esom(ampl_path=ampl_path, ampl_options=suff_ampl_options)
    elif c in ('norte_amazonia_reality_2025', 'norte_amazonia_reality_2025_phase2',
             'norte_amazonia_reality_access_2025'):
        # brownfield lock-down shrinks the LP to ~400K vars after presolve;
        # dual simplex (no baropt) avoids barrier degeneracy on the tightly-fixed constraints
        reality_cplex = ['timelimit 172800', 'display=2']
        reality_ampl_options = {
            'show_stats': 3,
            'log_file': str(my_model.cs_dir / 'log.txt'),
            'presolve': 200,
            'times': 1,
            'gentimes': 1,
            'cplex_options': ' '.join(reality_cplex),
        }
        my_model.set_esom(ampl_path=ampl_path, ampl_options=reality_ampl_options)
    elif 'epsilon' in c:
        mod_path[1].parent.mkdir(parents=True, exist_ok=True)
        my_model.set_esom(ampl_path=ampl_path, mod_path=mod_path)
    else:
        my_model.set_esom(ampl_path=ampl_path)

    my_model.solve_esom()
    my_model.get_year_results(save_hourly=save_hourly)
    my_model.prints_esom(inputs=True, outputs=True, solve_info=True, save_hourly=save_hourly)
    my_model.esom.ampl.close()

    i+=1

# Run with: & C:/Users/valen/anaconda3/envs/energyscope/python.exe scripts/run.py
# Use the "energyscope" conda env; AMPL must be installed in C:\Users\valen\AMPL