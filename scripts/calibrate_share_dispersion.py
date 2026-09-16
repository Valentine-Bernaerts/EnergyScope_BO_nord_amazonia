"""Recalibrate share_dispersion from a pass-1 solve, and write it to Misc.json.

    ####################################################################################
    #  DO NOT RUN. This script produced the share_dispersion values now frozen in      #
    #  Data/**/Misc.json, once, and must not be run again.                             #
    #                                                                                  #
    #  It is kept because it is the only record of how those values were derived:      #
    #  no notebook writes share_dispersion, and it cannot be recovered from the CSVs.  #
    #  It is documentation of a completed step, not a step of the pipeline.            #
    #                                                                                  #
    #  Why re-running it does not reproduce Data/: the calibration reads the solve of  #
    #  the case study it is given. The frozen values were computed from a PASS-1 solve #
    #  (share_dispersion forced to 0); pass 2 then overwrote that solve in the same     #
    #  output directory. Calibrating again from what is on disk therefore measures a   #
    #  different local electricity supply and lands somewhere else. Measured drift     #
    #  against the frozen values: +0.1 % to +10.4 %, worst case                        #
    #  early_access_brazil_2050 / C4 (frozen 0.00175800 -> recomputed 0.00194101).     #
    #                                                                                  #
    #  The same applies to scripts/solve.py, which calls write_misc() below: its       #
    #  two-pass groups rewrite Data/**/Misc.json in place.                             #
    ####################################################################################

Method, unchanged from the one already used for 2035/2050
("bolivia-energy-data/analyse data ramp/2050/share_dispersion.ipynb"):

    share_dispersion[c] = target[c] / (target[c] + offre_locale_hors_TECH_HS[c])

target[c]                  = demande_dispersee_GWh of that horizon's cluster_summary.csv
offre_locale_hors_TECH_HS  = every technology feeding the ELECTRICITY layer in that scenario's own
                             pass-1 solve (Year_balance.csv, excluding the ELECTRICITY balance row
                             itself and PV_HS / HS_DIESEL / BATT_HS), plus R_year_local and
                             R_year_exterior for ELECTRICITY read from that region's Resources.csv.
                             R_year_import / R_year_export are excluded on purpose: they are
                             inter-cluster exchange, not local supply, and Year_balance nets them
                             into one aggregate flow, so Resources.csv is read directly instead.

C2 and C5 are forced to 0 after the formula: C2 imports nearly all its electricity from C5, so the
denominator is too close to zero for the ratio to bite (its live mechanism is the f_max_prod cap
alone), and C5's target is 0 so the formula already gives 0.

share_dispersion is an ENERGY ratio, never the household ratio published in
share_dispersion_final_BC.csv: a dispersed household consumes far less than a grid-connected one,
so substituting one for the other overstates the floor (run.py, sufficiency block).

Usage:  python scripts/calibrate_share_dispersion.py <case_study> <year> <data_scenario>
"""
import io
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import ROOT, bolivia_file

ROOT = str(ROOT)
CLUSTERS = ["C1", "C2", "C3", "C4", "C5"]
EXCLUDE = {"ELECTRICITY", "PV_HS", "HS_DIESEL", "BATT_HS"}
FORCED_ZERO = ("C2", "C5")
CLASSIF_YEAR = {"2025": "2024", "2035": "2035", "2050": "2050"}


def check_solved(case_study):
    """Always verify the source actually solved: the pipeline writes normal-looking files even
    on a rejected solve."""
    p = os.path.join(ROOT, "case_studies", "C1_C2_C3_C4_C5", case_study, "outputs",
                     "Solve_info.csv")
    si = pd.read_csv(p, sep=r"\t;\t", header=None, index_col=0, engine="python")
    n = int(float(si.loc["solve_result_num", 1]))
    assert n == 0, ("%s: solve_result_num=%d != 0 -- refusing to calibrate share_dispersion "
                    "from a non-optimal pass-1 solve" % (case_study, n))
    return n


def offre_locale(case_study):
    """{cluster: local electricity supply excluding TECH_HS, GWh/y} from the pass-1 solve."""
    d = os.path.join(ROOT, "case_studies", "C1_C2_C3_C4_C5", case_study, "outputs",
                     "regional_results")
    yb = pd.read_csv(os.path.join(d, "Year_balance.csv"), sep=";")
    yb["ELECTRICITY"] = pd.to_numeric(yb["ELECTRICITY"], errors="coerce")
    tech = yb[~yb["Elements"].isin(EXCLUDE)]
    tech = tech[tech["ELECTRICITY"] > 1e-9]
    tech_sum = tech.groupby("Regions")["ELECTRICITY"].sum()

    res = pd.read_csv(os.path.join(d, "Resources.csv"), sep=";")
    elec = res[res["Resources"] == "ELECTRICITY"].set_index("Regions")
    loc = pd.to_numeric(elec["R_year_local"], errors="coerce").fillna(0.0)
    ext = pd.to_numeric(elec["R_year_exterior"], errors="coerce").fillna(0.0)
    return {c: float(tech_sum.get(c, 0.0)) + float(loc.get(c, 0.0)) + float(ext.get(c, 0.0))
            for c in CLUSTERS}


def write_misc(year, scenario, values):
    """Set share_dispersion in Data/<year>/<scenario>/C*/Misc.json, keeping each file's layout."""
    for c in CLUSTERS:
        p = os.path.join(ROOT, "Data", year, scenario, c, "Misc.json")
        with io.open(p, encoding="utf-8", newline="") as f:
            lines = f.read().splitlines(keepends=True)
        hits = [n for n, l in enumerate(lines) if '"share_dispersion"' in l]
        assert len(hits) == 1, "%s: %d share_dispersion lines" % (p, len(hits))
        n = hits[0]
        body = lines[n].rstrip("\r\n")
        eol = lines[n][len(body):]
        head, _, tail = body.partition(":")
        comma = "," if tail.rstrip().endswith(",") else ""
        lines[n] = "%s: %s%s%s" % (head, repr(float(values[c])), comma, eol)
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)
        back = json.load(io.open(p, encoding="utf-8-sig"))
        assert abs(float(back["share_dispersion"]) - values[c]) < 1e-12, p


def main(case_study, year, scenario):
    check_solved(case_study)
    cs = pd.read_csv(bolivia_file("analyse_GIS_projections", "output",
                                  CLASSIF_YEAR[year], "cluster_summary.csv")).set_index("Cluster")
    target = {c: float(cs.loc[c, "demande_dispersee_GWh"]) for c in CLUSTERS}
    offre = offre_locale(case_study)

    raw, deployed = {}, {}
    for c in CLUSTERS:
        denom = target[c] + offre[c]
        raw[c] = (target[c] / denom) if denom > 0 else 0.0
        deployed[c] = 0.0 if c in FORCED_ZERO else raw[c]

    write_misc(year, scenario, deployed)
    print("%-42s target/offre_locale -> share_dispersion (C2,C5 forced to 0)" % case_study)
    for c in CLUSTERS:
        flag = "  <- forced 0" if c in FORCED_ZERO else ""
        print("   %s  target=%8.4f  offre=%10.4f  raw=%.8f  deployed=%.8f%s"
              % (c, target[c], offre[c], raw[c], deployed[c], flag))
    return deployed


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
