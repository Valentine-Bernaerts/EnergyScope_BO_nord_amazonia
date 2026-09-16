"""What each scenario changes, relative to the catalogue read from Data/<year>/<scenario>/.

One entry per case name accepted by run.py. A field left at its default means "unchanged", so
a case reads as the short list of what it actually does. Two scenarios that differ only by their
input folder (late_access vs early_access at the same horizon) therefore differ by one line here.

Fields
    year, data, study   read Data/<year>/<data>/, write case_studies/C1_C2_C3_C4_C5/<study>/
    solver              CPLEX option set (see CPLEX below)
    reuse_td            reuse the typical days cached in 00_td_dat instead of re-clustering
    uncap_diesel        DIESEL avail_exterior -> 1e6 in every cluster
    uncap_sin_c1        C1 ELECTRICITY avail_exterior -> 1e6
    unlock_supply       PV_UTILITY and BATT_LI f_max -> 1e15
    no_home_battery     BATT_HS forced to 0, pv/battery ratio check switched off
    home_fleet_floor    PV_HS / HS_DIESEL / BATT_HS f_min from share_dispersion_final_BC.csv
    block_dec_solar     DEC_SOLAR f_min = f_max = 0
    zero_f_min_prod     {technology: [clusters]} whose f_min_prod floor is released
    tech_params         ((technology, column, value), ...) applied in every cluster
    indep_params        ((table, row, column, value), ...) applied to the shared catalogue
    brazil_import       total ELECTRICITY avail_exterior over C3 + C5 [GWh/y], split preserved
"""
from dataclasses import dataclass, field, replace

import pandas as pd

# off-grid home systems; share_dispersion_final_BC.csv stores f_min already in GW/GWh
HOME_TECHS = {'PV_HS': 'f_min_PV_HS_GW',
              'HS_DIESEL': 'f_min_HS_DIESEL_GW',
              'BATT_HS': 'f_min_BATT_HS_GWh'}

# Source A's 2025 diesel/gas fleet, locked in by the frozen counterfactual
FROZEN_FLEET = {'GENSET_DIESEL': ['C3', 'C4', 'C5'],
                'DEC_BOILER_GAS': ['C2', 'C3', 'C4', 'C5'],
                'DEC_DIRECT_ELEC': ['C1', 'C3', 'C5']}

CPLEX = {
    'sufficiency': ['baropt', 'predual=-1', 'barstart=4', 'comptol=1e-4', 'crossover=0',
                    'timelimit 172800', 'bardisplay=1', 'display=2'],
    # brownfield lock-down shrinks the LP to ~400K vars after presolve; dual simplex (no baropt)
    # avoids barrier degeneracy on the tightly-fixed constraints
    'reality': ['timelimit 172800', 'display=2'],
    # projections carry absolute f_max_prod on PV_HS/HS_DIESEL, same as the 2025 reality family:
    # dual simplex avoids the barrier-without-crossover interior point that never gets cleaned up
    # against ~2 GWh absolute caps in a model running at ~4375 GWh scale (GRID F_year)
    'projection': ['timelimit 172800', 'display=2'],
}


@dataclass(frozen=True)
class Case:
    year: int
    data: str
    study: str
    solver: str = 'default'
    reuse_td: bool = False
    uncap_diesel: bool = False
    uncap_sin_c1: bool = False
    unlock_supply: bool = False
    no_home_battery: bool = False
    home_fleet_floor: bool = False
    block_dec_solar: bool = False
    zero_f_min_prod: dict = field(default_factory=dict)
    tech_params: tuple = ()
    indep_params: tuple = ()
    brazil_import: float = None


CASES = {
    # --- 2025 -------------------------------------------------------------------------------
    # The real 2025 home fleet is a floor, f_max stays open. This overrides the static f_min of
    # Technologies.csv, which is not regenerated when the CSV changes. share_dispersion is
    # deliberately NOT taken from that CSV: its column is a ratio of HOUSEHOLDS, while the
    # constraint it fed (share_tech_hs, ESMC_model_AMPL.mod) is a ratio of ENERGY, and a
    # dispersed household consumes far less than a grid-connected one. It is calibrated on this
    # scenario's own pass-1 solve instead (scripts/calibrate_share_dispersion.py).
    'sufficiency': Case(2025, 'sufficiency', 'norte_amazonia_sufficiency_2025',
                        solver='sufficiency', home_fleet_floor=True),

    # Dispatch of the real 2025 system. Diesel is a purchased fuel and C1's SIN import cap is
    # historical rather than physical, so both are uncapped. BATT_HS is negligible in reality.
    'reality': Case(2025, 'reality', 'norte_amazonia_reality_2025',
                    solver='reality', uncap_diesel=True, uncap_sin_c1=True, no_home_battery=True),

    # Same dispatch, but utility PV and grid batteries may be built. f_min stays brownfield;
    # wind and hydro stay off, to match sufficiency.
    'reality_phase2': Case(2025, 'reality', 'norte_amazonia_reality_2025_phase2',
                           solver='reality', uncap_diesel=True, uncap_sin_c1=True,
                           no_home_battery=True, unlock_supply=True),

    # Real 2025 system + universal-access demand. The home-system floors are baked into
    # Data/2025/reality_access/*/Technologies.csv, so the pv/battery ratio check stays on.
    'reality_access': Case(2025, 'reality_access', 'norte_amazonia_reality_access_2025',
                           solver='reality', uncap_diesel=True, uncap_sin_c1=True),

    # reality_access + supply-side unlock, and the frozen 2025 fleet is released.
    'access_transition': Case(2025, 'reality_access', 'norte_amazonia_access_transition_2025',
                              solver='reality', uncap_diesel=True, uncap_sin_c1=True,
                              unlock_supply=True, zero_f_min_prod=FROZEN_FLEET),

    # --- projections ------------------------------------------------------------------------
    # Technologies.csv locks PV_UTILITY/BATT_LI to f_max = f_min (existing fleet only) for every
    # projection scenario: that default *is* no_transition. early_access and late_access are the
    # same supply-side transition on an earlier or later calendar, which is carried by their own
    # Demands.csv, so they differ from no_transition only by unlock_supply.
    'no_transition_2035': Case(2035, 'no_transition', 'norte_amazonia_no_transition_2035',
                               solver='projection'),
    'late_access_2035': Case(2035, 'late_access', 'norte_amazonia_late_access_2035',
                             solver='projection', unlock_supply=True),
    'early_access_2035': Case(2035, 'early_access', 'norte_amazonia_early_access_2035',
                              solver='projection', unlock_supply=True),

    'no_transition_2050': Case(2050, 'no_transition', 'norte_amazonia_no_transition_2050',
                               solver='projection'),
    'late_access_2050': Case(2050, 'late_access', 'norte_amazonia_late_access_2050',
                             solver='projection', unlock_supply=True),
    'early_access_2050': Case(2050, 'early_access', 'norte_amazonia_early_access_2050',
                              solver='projection', unlock_supply=True),

    # early_access 2050 with the Brazilian interconnection open to C3 and C5.
    'early_access_brazil_2050': Case(2050, 'early_access_brazil',
                                     'norte_amazonia_early_access_brazil_2050',
                                     solver='projection', unlock_supply=True),
}


def sens(parent, suffix, **changes):
    """A sensitivity: its parent case with one parameter changed, in its own case study."""
    base = CASES[parent]
    return replace(base, study=base.study + suffix, **changes)


CASES.update({
    # Diesel lifetime 20 y instead of 30 y, in the scenario where diesel carries the whole
    # system. Source: Plan Electrico Referencial 2035.
    'no_transition_2050_sens_diesel20': sens(
        'no_transition_2050', '_sens_diesel20',
        tech_params=(('GENSET_DIESEL', 'lifetime', 20.0),)),

    # DEC_SOLAR blocked. Checks whether the NREL ATB cost ratio, applied to PV and batteries but
    # not to the solar collector (frozen at its 2025 price), mechanically favours the electric
    # resistance by 2050. DEC_SOLAR's 2050 f_min is a small floor chained from the scenario's own
    # 2035 solve, not a pre-existing fleet, so zeroing it is part of the counterfactual: a system
    # where the collector was never built. TS_DEC, the tank, is deliberately left untouched.
    'early_access_2050_sens_nodecsolar': sens(
        'early_access_2050', '_sens_nodecsolar', block_dec_solar=True),
    'late_access_2050_sens_nodecsolar': sens(
        'late_access_2050', '_sens_nodecsolar', block_dec_solar=True),

    # BATT_LI fixed O&M at the NREL ATB 2024 rule, 2.5 % of capital cost per year applied to the
    # 2025 catalogue c_inv (0.025 * 425.88 = 10.647 M EUR/GWh/y), so the value is horizon-flat,
    # against the catalogue's own 0.658412583 (= 0.155 %/y). Only c_maint differs from the central
    # run, so the typical days are reused: the clustering input is identical and reusing the exact
    # days keeps the comparison strictly single-variable.
    'late_access_2050_sens_battom': sens(
        'late_access_2050', '_sens_battom',
        tech_params=(('BATT_LI', 'c_maint', 10.647),), reuse_td=True),

    # Brazilian import price. The central 0.0593 M EUR/GWh lives in the shared
    # Data/2050/*/00_INDEP/Resources_indep.csv, identical across all four 2050 scenarios; that
    # file is never touched on disk, the override is applied in memory to this run only.
    'early_access_brazil_2050_sens_price003': sens(
        'early_access_brazil_2050', '_sens_price003',
        indep_params=(('Resources_indep', 'ELECTRICITY', 'c_op_exterior', 0.03),)),
    'early_access_brazil_2050_sens_price009': sens(
        'early_access_brazil_2050', '_sens_price009',
        indep_params=(('Resources_indep', 'ELECTRICITY', 'c_op_exterior', 0.09),)),

    # Brazilian import volume, against the central 113.8 GWh/y. The C3/C5 split is read back from
    # what is actually deployed and preserved exactly; only the total is rescaled.
    'early_access_brazil_2050_sens_vol923': sens(
        'early_access_brazil_2050', '_sens_vol923', brazil_import=92.3),
    'early_access_brazil_2050_sens_vol1857': sens(
        'early_access_brazil_2050', '_sens_vol1857', brazil_import=185.7),

    # Solar water heater blocked at 2025, on the two universal-coverage scenarios (thesis
    # figure 21). These two keep their own folder layout, which analyse_resultats.ipynb reads.
    'reality_access_sens_nodecsolar': replace(
        CASES['reality_access'], study='_sensitivity_DEC_SOLAR_fmax0/reality_access',
        block_dec_solar=True),
    'sufficiency_sens_nodecsolar': replace(
        CASES['sufficiency'], study='_sensitivity_DEC_SOLAR_fmax0/sufficiency',
        block_dec_solar=True),
})


def apply_case(case, model, project_dir):
    """Apply to the model in memory what this case changes. No file on disk is written."""
    if case.home_fleet_floor:
        bc = pd.read_csv(project_dir / 'Data' / str(case.year) / case.data
                         / 'share_dispersion_final_BC.csv', index_col='Cluster')
        for r_code, region in model.regions.items():
            for tech, col in HOME_TECHS.items():
                if tech in region.data['Technologies'].index:
                    region.data['Technologies'].loc[tech, 'f_min'] = float(bc.loc[r_code, col])
                    region.data['Technologies'].loc[tech, 'f_max'] = 1e15

    if case.uncap_diesel:
        for r_code, region in model.regions.items():
            if 'DIESEL' in region.data['Resources'].index:
                region.data['Resources'].loc['DIESEL', 'avail_exterior'] = 1e6

    if case.uncap_sin_c1 and 'C1' in model.regions:
        resources = model.regions['C1'].data['Resources']
        if 'ELECTRICITY' in resources.index:
            resources.loc['ELECTRICITY', 'avail_exterior'] = 1e6

    if case.no_home_battery:
        for r_code, region in model.regions.items():
            region.data['Misc']['pv_battery_ratio_enforced'] = 0
            if 'BATT_HS' in region.data['Technologies'].index:
                region.data['Technologies'].loc['BATT_HS', 'f_min'] = 0.0
                region.data['Technologies'].loc['BATT_HS', 'f_max'] = 0.0

    if case.unlock_supply:
        for r_code, region in model.regions.items():
            region.data['Technologies'].loc['PV_UTILITY', 'f_max'] = 1e15
            region.data['Technologies'].loc['BATT_LI', 'f_max'] = 1e15

    for tech, r_codes in case.zero_f_min_prod.items():
        for r_code in r_codes:
            model.regions[r_code].data['Technologies'].loc[tech, 'f_min_prod'] = 0.0

    if case.block_dec_solar:
        for r_code, region in model.regions.items():
            if 'DEC_SOLAR' in region.data['Technologies'].index:
                region.data['Technologies'].loc['DEC_SOLAR', 'f_min'] = 0.0
                region.data['Technologies'].loc['DEC_SOLAR', 'f_max'] = 0.0

    for tech, col, value in case.tech_params:
        for r_code, region in model.regions.items():
            if tech in region.data['Technologies'].index:
                region.data['Technologies'].loc[tech, col] = value

    for table, row, col, value in case.indep_params:
        model.data_indep[table].loc[row, col] = value

    if case.brazil_import is not None:
        c3 = model.regions['C3'].data['Resources'].loc['ELECTRICITY', 'avail_exterior']
        c5 = model.regions['C5'].data['Resources'].loc['ELECTRICITY', 'avail_exterior']
        scale = case.brazil_import / (c3 + c5)
        model.regions['C3'].data['Resources'].loc['ELECTRICITY', 'avail_exterior'] = c3 * scale
        model.regions['C5'].data['Resources'].loc['ELECTRICITY', 'avail_exterior'] = c5 * scale


def ampl_options(case, model, run_logs):
    """AMPL/CPLEX options for this case, or None to keep set_esom's own defaults."""
    if case.solver == 'default':
        return None
    if case.solver == 'reality':
        log_file = model.cs_dir / 'log.txt'
    else:
        run_logs.mkdir(parents=True, exist_ok=True)
        log_file = run_logs / ('%s_log.txt' % case.study.replace('/', '_'))
    return {'show_stats': 3,
            'log_file': str(log_file),
            'presolve': 200,
            'times': 1,
            'gentimes': 1,
            'cplex_options': ' '.join(CPLEX[case.solver])}
