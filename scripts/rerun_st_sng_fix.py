# Re-run Phase 1 and Phase 2 after ST_SNG ghost fix.
# ST_SNG f_min/f_max set to 0 in all cluster CSVs and both reg_technologies.dat files.
# Uses algo='read' (existing 16-TD clustering) and skips print_data so that
# phase-specific dat differences (Phase 1 old TECH_HS costs / Phase 2 share_dispersion
# f_min values) are preserved exactly as they were before the fix.

import sys
import logging
from pathlib import Path

sys.path.insert(0, r'C:\Valen\Tfe\EnergyScope_BO_nord_amazonia')
from esmc import Esmc

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

cases = [
    'norte_amazonia_sufficiency_2025',          # Phase 1: share_dispersion=0
    'norte_amazonia_sufficiency_2025_phase2',   # Phase 2 BC: share_dispersion=BC, TECH_HS costs 2730/594/1302
]

tds = 16
ampl_path = r'C:\Users\valen\AMPL'
save_hourly = ['Resources', 'Exchanges', 'Assets', 'Storage', 'Curt']

ft_to_drop = [
    'BIOMASS_TO_GASOLINE', 'BIOMASS_TO_DIESEL',
    'BIOWASTE_TO_GASOLINE', 'BIOWASTE_TO_DIESEL',
    'POWER_TO_GASOLINE', 'POWER_TO_DIESEL',
    'H2_TO_GASOLINE', 'H2_TO_DIESEL',
]

config_base = {
    'comment': 'ST_SNG fix rerun',
    'regions_names': ['C1', 'C2', 'C3', 'C4', 'C5'],
    'gwp_limit_overall': None,
    're_share_primary': None,
    'f_perc': True,
    'year': 2025,
}

results_summary = {}

for c in cases:
    print(f'\n{"="*60}')
    print(f'Case: {c}')
    print('='*60)

    config = {**config_base, 'case_study': c}

    my_model = Esmc(config, nbr_td=tds)

    current_project = Path(__file__).parents[1]
    my_model.project_dir = current_project
    my_model.dat_dir = current_project / 'case_studies' / my_model.space_id / '00_td_dat'
    my_model.cs_dir = current_project / 'case_studies' / my_model.space_id / my_model.case_study
    my_model.dat_dir.mkdir(parents=True, exist_ok=True)
    my_model.cs_dir.mkdir(parents=True, exist_ok=True)

    # Read data — needed so self.regions exists for cost-breakdown post-processing.
    # We do NOT call print_data, so the existing (now fixed) dat files are used.
    my_model.read_data_indep()
    my_model.init_regions()

    # Drop FT-to-liquid technologies (consistent with original runs).
    my_model.ref_region.data['Technologies'] = (
        my_model.ref_region.data['Technologies'].drop(index=ft_to_drop)
    )
    my_model.data_indep['Layers_in_out'] = (
        my_model.data_indep['Layers_in_out'].drop(index=ft_to_drop)
    )
    for r_code, region in my_model.regions.items():
        region.data['Technologies'] = region.data['Technologies'].drop(index=ft_to_drop)

    # Use existing 16-TD clustering — no re-clustering.
    my_model.init_ta(algo='read', ampl_path=ampl_path)

    # Skip print_td_data() and print_data() — dat files already fixed in-place.

    # Load model + fixed dat files into AMPL, solve, extract results.
    my_model.set_esom(ampl_path=ampl_path)
    my_model.solve_esom()
    my_model.get_year_results(save_hourly=save_hourly)
    my_model.prints_esom(inputs=True, outputs=True, solve_info=True, save_hourly=save_hourly)

    total_cost = float(my_model.results_all['TotalCost'].iloc[0])
    results_summary[c] = total_cost
    print(f'\nTotalCost [{c}] = {total_cost:.6f} M€/yr')

    my_model.esom.ampl.close()

print('\n\n=== SUMMARY ===')
for c, tc in results_summary.items():
    label = 'Phase 1' if '2025_p' not in c else 'Phase 2 BC'
    # recheck label
    if 'phase2' in c:
        label = 'Phase 2 BC'
    else:
        label = 'Phase 1'
    print(f'{label:12s}  TotalCost = {tc:.6f} M€/yr')
