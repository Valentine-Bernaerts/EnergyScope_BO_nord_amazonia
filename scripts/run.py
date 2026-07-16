# Norte Amazónica 2025 — multi-cell run
# 5 clusters: C1 (Beni/Ixiamas), C2 (Bolpebra), C3 (Riberalta/Guayaramerín/Puerto),
#             C4 (Central Pando), C5 (Cobija)
# Scenario selected below (sufficiency / sufficiency_phase2 / reality).
# Data folder is chosen automatically from the scenario: Data/2025/<scenario>/

import numpy as np
from pathlib import Path

# additional line for VS studio
import sys

import pandas as pd

sys.path.insert(0, r'C:\Valen\Tfe\EnergyScope_BO_nord_amazonia')
from esmc import Esmc
from esmc.common import bo_country_code, CSV_SEPARATOR

# Choose which case to run. Available options:
#   'sufficiency'         -> norte_amazonia_sufficiency_2025               (data: Data/2025/sufficiency)
#   'sufficiency_phase2'  -> norte_amazonia_sufficiency_2025_phase2        (data: Data/2025/sufficiency)
#   'reality'             -> norte_amazonia_sufficiency_2025_reality       (data: Data/2025/reality)
#   'reality_phase2'      -> norte_amazonia_sufficiency_2025_reality_phase2 (data: Data/2025/reality)
selected_case = 'reality_phase2'

year = 2025

if selected_case == 'sufficiency':
    scenario = 'sufficiency'
    case_study = f'norte_amazonia_sufficiency_{year}'
elif selected_case == 'sufficiency_phase2':
    scenario = 'sufficiency'
    case_study = f'norte_amazonia_sufficiency_{year}_phase2'
elif selected_case == 'reality':
    scenario = 'reality'
    case_study = f'norte_amazonia_sufficiency_{year}_reality'
elif selected_case == 'reality_phase2':
    scenario = 'reality'
    case_study = f'norte_amazonia_sufficiency_{year}_reality_phase2'
else:
    raise ValueError(f"Unknown selected_case '{selected_case}': "
                     "use 'sufficiency', 'sufficiency_phase2', 'reality' or 'reality_phase2'")

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

# Set i = 0 to (re)generate the TD clustering for the current scenario (kmedoid).
# The clustering cache in 00_td_dat/ is shared across scenarios, so reusing it
# (i = 1) after switching scenario can make the model infeasible. Regenerate once
# per scenario, then you may switch back to i = 1 to reuse it within that scenario.
i = 0

for c in cases:

    print(c)

    # define configuration
    config = {'case_study': c,
              'comment': 'none',
              # Ligne originale (ligne 45 du script original) :
              # 'regions_names': bo_country_code,
              # Remplacée par 5 régions car 8 régions (~16 GB RAM) dépasse la mémoire disponible.
              # Pour revenir à 8 régions : décommenter la ligne ci-dessus et commenter la ligne ci-dessous.
              'regions_names': ['C1', 'C2', 'C3', 'C4', 'C5'],
              'gwp_limit_overall': gwp_limit_overall,
              're_share_primary': re_share_primary,
              'f_perc': f_perc,
              'year': year,
              'scenario': scenario}

    # initialize EnergyScope Multi-cells framework
    my_model = Esmc(config, nbr_td=tds)

    # redirect data/output paths to this repo instead of EnergyScope_multicell_BO_Roger_Thesis
    current_project = Path(__file__).parents[1]
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


    if c == 'norte_amazonia_sufficiency_2025':
        print('\n--- Phase 1 (greenfield) overrides ---')
        # Phase 1 = greenfield: no existing BC installations and no demand dispersion.
        # The base sufficiency data ships with phase 2 brownfield values, so we reset them here.
        for r_code, region in my_model.regions.items():
            region.data['Misc']['share_dispersion'] = 0.0
            for tech in ['PV_HS', 'HS_DIESEL']:
                if tech in region.data['Technologies'].index:
                    region.data['Technologies'].loc[tech, 'f_min'] = 0.0
            print(f'  {r_code}: share_dispersion=0, PV_HS f_min=0, HS_DIESEL f_min=0')
        print('--- end Phase 1 overrides ---\n')

    # Phase 2 = brownfield: the base sufficiency data already ships with the BC
    # share_dispersion and PV_HS/HS_DIESEL f_min values baked in, so no override
    # is needed here (Phase 1 above is the one that resets them to greenfield).

    if c in ('norte_amazonia_sufficiency_2025_reality', 'norte_amazonia_sufficiency_2025_reality_phase2'):
        # In pure dispatch, diesel is a purchased fuel (not infrastructure-capped).
        # The CSV avail_exterior values reflect historical consumption in a greenfield run
        # (where PV+storage reduced diesel use). With gensets as sole electricity source,
        # the historical cap is too tight → infeasible. Set to unlimited so cost drives dispatch.
        for r_code, region in my_model.regions.items():
            if 'DIESEL' in region.data['Resources'].index:
                region.data['Resources'].loc['DIESEL', 'avail_exterior'] = 1e6
        # C1 is SIN-connected: avail_exterior[ELECTRICITY]=11.59 GWh was the historical
        # baseline SIN delivery, not a physical grid capacity limit. Without local GENSET,
        # C1 must draw its full demand (~12-14 GWh) from SIN → cap is too tight.
        if 'C1' in my_model.regions:
            if 'ELECTRICITY' in my_model.regions['C1'].data['Resources'].index:
                my_model.regions['C1'].data['Resources'].loc['ELECTRICITY', 'avail_exterior'] = 1e6

        # Source B home systems (PV_HS, HS_DIESEL, share_dispersion) are already
        # brownfield-locked (f_min=f_max) in the reality CSV data, no override needed.
        # BATT_HS is forced to 0 here: the CSV's existing home battery bank (~123 Wh/hh,
        # negligible at cluster scale) would otherwise trip the model's
        # pv_battery_ratio_hs_min/max constraint (0.5-2.0 kWp/kWh, sized for coherent
        # greenfield PV+battery kits) and force PV_HS to 0 too, so that constraint is
        # disabled for reality via pv_battery_ratio_enforced (default 1 elsewhere).
        for r_code, region in my_model.regions.items():
            region.data['Misc']['pv_battery_ratio_enforced'] = 0
            if 'BATT_HS' in region.data['Technologies'].index:
                region.data['Technologies'].loc['BATT_HS', 'f_min'] = 0.0
                region.data['Technologies'].loc['BATT_HS', 'f_max'] = 0.0

    if c == 'norte_amazonia_sufficiency_2025_reality_phase2':
        # Same real 2025 demand and dispatch as reality, but let the model build new
        # utility-scale PV and grid batteries to see how much cost drops when supply
        # is optimized. f_min stays at the existing brownfield value (0 everywhere,
        # 0.0051 GW in C5), only f_max is unlocked.
        # WIND_ONSHORE and HYDRO_DAM/HYDRO_RIVER are not unlocked: their f_max is 0
        # in the base data and sufficiency_phase2 never raises it either, so leaving
        # them at 0 keeps this comparable to sufficiency_phase2.
        for r_code, region in my_model.regions.items():
            region.data['Technologies'].loc['PV_UTILITY', 'f_max'] = 1e15
            region.data['Technologies'].loc['BATT_LI', 'f_max'] = 1e15

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
    if c in ('norte_amazonia_sufficiency_2025_reality', 'norte_amazonia_sufficiency_2025_reality_phase2'):
        # Brownfield lock-down reduces the LP to ~400K vars after presolve.
        # crossover=1 is feasible at this size; avoids barrier degeneracy from tightly-fixed constraints.
        # No baropt: let CPLEX use dual simplex (barrier degenerates on tight brownfield LP)
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

    # Solving the ESOM
    my_model.solve_esom()

    # Getting and printing year results
    my_model.get_year_results(save_hourly=save_hourly)
    my_model.prints_esom(inputs=True, outputs=True, solve_info=True, save_hourly=save_hourly)

    # delete ampl object to free resources
    my_model.esom.ampl.close()

    i+=1

# =============================================================================
# HOW TO RUN THIS SCRIPT
# -----------------------------------------------------------------------------
# Terminal: PowerShell
#
# Command to copy and paste:
#   & C:/Users/valen/anaconda3/envs/energyscope/python.exe c:/Valen/Tfe/EnergyScope_BO_nord_amazonia/scripts/run.py
#
# Notes:
# - Use the conda "energyscope" environment (not "ramp", not "base")
# - AMPL must be installed in C:\Users\valen\AMPL
# =============================================================================