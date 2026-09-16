"""Two-pass solve campaign over a group of scenarios.

    ####################################################################################
    #  DO NOT RUN on this repository as published. Every group except "sens" REWRITES  #
    #  share_dispersion in Data/<year>/<scenario>/C*/Misc.json, in place, and the      #
    #  values it writes are NOT the frozen ones that produced the published results:   #
    #  the frozen values came from a pass-1 solve that pass 2 has since overwritten.   #
    #  Measured drift: +0.1 % to +10.4 % (see scripts/calibrate_share_dispersion.py).  #
    #                                                                                  #
    #  This file is kept as the record of how the published results were sequenced.    #
    #  To re-solve a case without touching Data/, use:                                 #
    #      python scripts/run.py <case>                                                #
    ####################################################################################

    python scripts/solve.py <group> [--only all|pass1|pass2] [--skip-pass1 a,b] [--dry-run]

Groups:
    campaign   every scenario the A/B/C classification touches, in one sweep
    2035       no_transition / early_access / late_access at 2035
    2050       the same three at 2050. Must run after 2035: Data/2050 chains f_min[2050]
               from each scenario's own solved 2035 Assets.csv.
    brazil     early_access_brazil_2050 alone. Must run after 2050: its ELECTRICITY
               avail_exterior split between C3 and C5 is derived from no_transition_2050's
               own solved GENSET_DIESEL production.
    sens       the single-variable sensitivities, one pass and no calibration of their own:
               each inherits its parent scenario's catalogue and share_dispersion.

Two passes: share_dispersion is forced to 0 and every scenario solves once so its local
electricity supply can be measured (pass 1), each scenario's share_dispersion is recalibrated
from its own pass-1 solve (calibrate_share_dispersion.py), then every scenario solves again
(pass 2). The campaign group starts from a share_dispersion already written by the propagation
step, so it does not force the zeros itself.

reality and reality_phase2 are absent on purpose: with no grid extension nobody is reconnected,
so their observed 2025 home fleet does not depend on the classification. access_transition shares
Data/2025/reality_access with reality_access and cannot carry a share_dispersion of its own, so it
inherits that calibration and is solved in pass 2 only.

Runs are strictly sequential: init_ta(algo='kmedoid') rewrites the SHARED typical-day cache
case_studies/C1_C2_C3_C4_C5/00_td_dat/ on every run, so two concurrent runs would corrupt it.
solve_result_num is checked after every run, because the pipeline writes normal-looking output
files even on a rejected solve.
"""
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import CASE_STUDIES, ROOT, RUN_LOGS

import calibrate_share_dispersion

# (run.py case, case_study dir, Data year, Data scenario, owns its Misc.json)
CAMPAIGN = [
    ("reality_access",           "norte_amazonia_reality_access_2025",      "2025", "reality_access",      True),
    ("sufficiency",              "norte_amazonia_sufficiency_2025",         "2025", "sufficiency",         True),
    ("no_transition_2035",       "norte_amazonia_no_transition_2035",       "2035", "no_transition",       True),
    ("early_access_2035",        "norte_amazonia_early_access_2035",        "2035", "early_access",        True),
    ("late_access_2035",         "norte_amazonia_late_access_2035",         "2035", "late_access",         True),
    ("no_transition_2050",       "norte_amazonia_no_transition_2050",       "2050", "no_transition",       True),
    ("early_access_2050",        "norte_amazonia_early_access_2050",        "2050", "early_access",        True),
    ("late_access_2050",         "norte_amazonia_late_access_2050",         "2050", "late_access",         True),
    ("early_access_brazil_2050", "norte_amazonia_early_access_brazil_2050", "2050", "early_access_brazil", True),
    ("access_transition",        "norte_amazonia_access_transition_2025",   "2025", "reality_access",      False),
]

GROUPS = {
    "campaign": CAMPAIGN,
    "2035": [
        ("no_transition_2035", "norte_amazonia_no_transition_2035", "2035", "no_transition", True),
        ("early_access_2035",  "norte_amazonia_early_access_2035",  "2035", "early_access",  True),
        ("late_access_2035",   "norte_amazonia_late_access_2035",   "2035", "late_access",   True),
    ],
    "2050": [
        ("no_transition_2050", "norte_amazonia_no_transition_2050", "2050", "no_transition", True),
        ("early_access_2050",  "norte_amazonia_early_access_2050",  "2050", "early_access",  True),
        ("late_access_2050",   "norte_amazonia_late_access_2050",   "2050", "late_access",   True),
    ],
    "brazil": [
        ("early_access_brazil_2050", "norte_amazonia_early_access_brazil_2050",
         "2050", "early_access_brazil", True),
    ],
}

SENS = [
    ("early_access_2050_sens_nodecsolar",      "norte_amazonia_early_access_2050_sens_nodecsolar"),
    ("late_access_2050_sens_nodecsolar",       "norte_amazonia_late_access_2050_sens_nodecsolar"),
    ("late_access_2050_sens_battom",           "norte_amazonia_late_access_2050_sens_battom"),
    ("early_access_brazil_2050_sens_price003", "norte_amazonia_early_access_brazil_2050_sens_price003"),
    ("early_access_brazil_2050_sens_price009", "norte_amazonia_early_access_brazil_2050_sens_price009"),
    ("early_access_brazil_2050_sens_vol923",   "norte_amazonia_early_access_brazil_2050_sens_vol923"),
    ("early_access_brazil_2050_sens_vol1857",  "norte_amazonia_early_access_brazil_2050_sens_vol1857"),
    ("no_transition_2050_sens_diesel20",       "norte_amazonia_no_transition_2050_sens_diesel20"),
]

# groups that force share_dispersion to 0 before pass 1
ZERO_FIRST = {"2035", "2050", "brazil"}

DRY_RUN = False
LOG_FILE = None


def log(msg):
    if DRY_RUN:
        return
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    if LOG_FILE is not None:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def solve_result_num(case_study):
    p = CASE_STUDIES / case_study / "outputs" / "Solve_info.csv"
    if not p.exists():
        return None
    si = pd.read_csv(p, sep=r"\t;\t", header=None, index_col=0, engine="python")
    return int(float(si.loc["solve_result_num", 1]))


def run_case(selected_case, case_study, label):
    if DRY_RUN:
        print("RUN    %-6s %-42s %s" % (label, selected_case, case_study))
        return True
    t0 = time.time()
    log("%s  %s  START" % (label, selected_case))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "run.py"), selected_case],
                       cwd=str(ROOT), capture_output=True, text=True, errors="replace")
    dt = time.time() - t0
    if r.returncode != 0:
        log("%s  %s  RUN FAILED rc=%d (%.0fs)\n%s"
            % (label, selected_case, r.returncode, dt, r.stderr[-3000:]))
        return False
    n = solve_result_num(case_study)
    if n != 0:
        log("%s  %s  SOLVE REJECTED solve_result_num=%s (%.0fs)" % (label, selected_case, n, dt))
        return False
    log("%s  %s  OK solve_result_num=0 (%.0fs)" % (label, selected_case, dt))
    return True


def zero_share_dispersion(cases):
    done = set()
    for _, _, year, scen, _ in cases:
        if (year, scen) in done:
            continue
        done.add((year, scen))
        if DRY_RUN:
            print("ZERO   %s/%s" % (year, scen))
            continue
        calibrate_share_dispersion.write_misc(
            year, scen, {c: 0.0 for c in calibrate_share_dispersion.CLUSTERS})
        log("share_dispersion forced to 0 in Data/%s/%s/C1-C5/Misc.json" % (year, scen))


def calibrate(case_study, year, scen):
    if DRY_RUN:
        print("CALIB  %-42s %s/%s" % (case_study, year, scen))
        return
    vals = calibrate_share_dispersion.main(case_study, year, scen)
    log("calibrated %-30s %s" % (scen + "/" + year, {c: round(v, 8) for c, v in vals.items()}))


def run_sens():
    failed = {}
    for sel, cs_dir in SENS:
        if not run_case(sel, cs_dir, "sens"):
            failed[sel] = "sens"
    log("--- SUMMARY (sens)")
    for sel, where in failed.items():
        log("DID NOT SOLVE: %-42s (%s)" % (sel, where))
    if not failed:
        log("every sensitivity solved")
    return 0


def main(argv):
    global DRY_RUN, LOG_FILE

    if not argv or argv[0] not in GROUPS and argv[0] != "sens":
        raise SystemExit("usage: python scripts/solve.py <group> [--only all|pass1|pass2] "
                         "[--skip-pass1 a,b] [--dry-run]\ngroups: %s"
                         % ", ".join(list(GROUPS) + ["sens"]))

    group = argv[0]
    DRY_RUN = "--dry-run" in argv
    only = argv[argv.index("--only") + 1] if "--only" in argv else "all"
    # Resume support: a case listed after --skip-pass1 already has a valid pass-1 solve on disk
    # (share_dispersion = 0, solve_result_num = 0) and is not re-solved. Re-verified below rather
    # than trusted.
    skip_pass1 = argv[argv.index("--skip-pass1") + 1].split(",") if "--skip-pass1" in argv else []

    LOG_FILE = RUN_LOGS / ("solve_%s.log" % group)
    log("=" * 70)
    log("campaign start -- group %s%s"
        % (group, ("  (pass 1 skipped for: %s)" % ",".join(skip_pass1)) if skip_pass1 else ""))

    if group == "sens":
        return run_sens()

    cases = GROUPS[group]
    failed = {}

    if group in ZERO_FIRST:
        zero_share_dispersion(cases)

    # A scenario that does not solve is a RESULT, not a reason to stop the campaign: the frozen
    # counterfactual can genuinely have no feasible electricity balance once its home-system cap is
    # set correctly. Failures are recorded, the scenario is dropped from calibration and from
    # pass 2, and every other scenario runs to completion.
    if only in ("all", "pass1"):
        log("--- PASS 1: share_dispersion = 0, measuring local supply")
        for sel, cs_dir, _, _, owns in cases:
            if not owns:
                continue
            if sel in skip_pass1:
                n = solve_result_num(cs_dir)
                assert n == 0, ("%s: --skip-pass1 given but solve_result_num=%s -- refusing to "
                                "calibrate from a solve that is not on disk and optimal" % (sel, n))
                log("pass1  %s  SKIPPED, existing solve reused (solve_result_num=0)" % sel)
                continue
            if not run_case(sel, cs_dir, "pass1"):
                failed[sel] = "pass1"
                log("RECORDED as a finding, campaign continues: %s did not solve" % sel)

        log("--- CALIBRATION")
        for sel, cs_dir, year, scen, owns in cases:
            if not owns or sel in failed:
                continue
            calibrate(cs_dir, year, scen)

    if only in ("all", "pass2"):
        log("--- PASS 2: calibrated share_dispersion, final solves")
        for sel, cs_dir, _, _, _ in cases:
            if sel in failed:
                log("pass2  %s  SKIPPED (no pass-1 solve, so no calibration)" % sel)
                continue
            if not run_case(sel, cs_dir, "pass2"):
                failed[sel] = failed.get(sel, "pass2")

    log("--- SUMMARY (group %s)" % group)
    if failed:
        for sel, where in failed.items():
            log("DID NOT SOLVE: %-30s (%s)" % (sel, where))
    else:
        log("every scenario of group %s solved" % group)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
