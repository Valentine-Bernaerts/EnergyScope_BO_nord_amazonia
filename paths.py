"""Filesystem layout of this repository and of the data it depends on.

Solving the model requires AMPL with the CPLEX solver; both need a licence
(free academic licences exist for each). The analysis notebooks read solved
outputs only and need neither.

Two environment variables override the defaults:
    ENERGYSCOPE_AMPL_PATH   AMPL installation directory
    ENERGYSCOPE_BED_PATH    bolivia-energy-data repository
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'Data'
CASE_STUDIES = ROOT / 'case_studies' / 'C1_C2_C3_C4_C5'
RUN_LOGS = ROOT / 'run_logs'


def _ampl_path():
    env = os.environ.get('ENERGYSCOPE_AMPL_PATH')
    if env:
        return env
    home = Path.home() / 'AMPL'
    # None means "ampl is on PATH", which is what amplpy expects
    return str(home) if home.is_dir() else None


AMPL_PATH = _ampl_path()

# Census, GIS and projection data used to build Data/ and to reconstruct costs.
# Published as a separate repository, expected next to this one.
BOLIVIA_DATA = Path(os.environ.get('ENERGYSCOPE_BED_PATH', ROOT.parent / 'bolivia-energy-data'))


def bolivia_file(*parts):
    """Path to a file of bolivia-energy-data, named explicitly if it is missing."""
    p = BOLIVIA_DATA.joinpath(*parts)
    if not p.exists():
        raise FileNotFoundError(
            f'{p}\n'
            f'This file belongs to the bolivia-energy-data repository, expected at '
            f'{BOLIVIA_DATA}. Clone it next to this repository, or point '
            f'ENERGYSCOPE_BED_PATH at it.')
    return p
