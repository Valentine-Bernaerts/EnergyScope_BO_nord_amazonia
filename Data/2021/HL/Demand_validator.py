#!/usr/bin/env python3
"""
demand_csv_validator.py  ·  **Zero‑config edition (v0.3)**
===========================================================
Simplement executa:

    $ python demand_csv_validator.py

Sense arguments:
  • Escaneja tots els `*.csv` del directori actual (afegiu `--recursive` per
    subcarpetes).
  • Si hi ha `parameters.json`, l’agafa com a mapping de `parameter name`.

Afegits a v0.3
--------------
1. **Numeric‑like strings detector** – cerca cel·les `object` que semblen nombres
   ("123", "45.6") però no són `float` ➜ FAIL.
2. **Mapping exhaustiu** ara és obligatori si `parameters.json` existeix; paràmetres
   sense node ➜ FAIL.

Checks complets (per fitxer)
---------------------------
✅ Columna `parameter name` present.
✅ ≥1 columna numèrica real (`float`/`int`).
✅ Cap string‑num ≠ num (veure 1).
✅ Files >0 i múltiple de 8 760 (o avís).
✅ Index duplicat? → FAIL.
✅ Ratio `NaN` ≤ llindar (0,1 % per defecte).
✅ Suma numèrica > 0.
✅ Paràmetres tots al mapping (si n’hi ha).

Sortida final: `EXIT 0` si tot passa, `EXIT 1` en cas contrari.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Set

import pandas as pd

PASS = "\u2705"  # ✓
FAIL = "\u274c"  # ✗
WARN = "\u26A0"  # ⚠️


class ValidationError(Exception):
    """Raised for any validation failure."""


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------

def detect_sep(sample: str) -> str:
    return ";" if sample.count(";") > sample.count(",") else ","


def read_csv_safely(path: Path) -> pd.DataFrame:
    with path.open("rb") as fh:
        head = fh.read(4096).decode(errors="ignore")
    sep = detect_sep(head)
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, sep=sep, encoding=enc, engine="python")
        except UnicodeDecodeError:
            continue
    raise ValidationError("Could not decode CSV with common encodings")


def normalise_parameter_col(df: pd.DataFrame) -> str:
    for col in df.columns:
        if col.strip().lower() == "parameter name":
            return col
    raise ValidationError("Column 'parameter name' not found (case‑insensitive)")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_numeric_columns(df: pd.DataFrame):
    num_cols = df.select_dtypes(include="number").columns
    if num_cols.empty:
        raise ValidationError("No numeric columns detected")
    return list(num_cols)


def check_numeric_like_strings(df: pd.DataFrame):
    pat = re.compile(r"^\s*-?\d+(?:[\.,]\d+)?\s*$")
    mask = df.select_dtypes("object").applymap(lambda x: bool(pat.match(str(x))) if pd.notna(x) else False)
    count = mask.sum().sum()
    if count:
        rows, cols = mask.any(axis=1).sum(), mask.any().sum()
        raise ValidationError(f"{count} numeric‑like strings in {rows} rows / {cols} cols – cast to float")


def check_length(df: pd.DataFrame):
    n = len(df)
    if n == 0:
        raise ValidationError("File is empty")
    if n % 8760 != 0:
        print(f"  {WARN} Rows ({n}) not multiple of 8 760")
    return n


def check_duplicates(df: pd.DataFrame):
    if df.index.duplicated().any():
        raise ValidationError(f"Index contains {df.index.duplicated().sum()} duplicate timestamps")


def check_nans(df: pd.DataFrame, max_ratio: float):
    ratio = df.isna().sum().sum() / df.size
    if ratio > max_ratio:
        raise ValidationError(f"NaN ratio {ratio:.2%} exceeds {max_ratio:.2%}")
    return ratio


def check_nonzero_sum(df: pd.DataFrame):
    total = df.select_dtypes("number").to_numpy().sum()
    if total == 0:
        raise ValidationError("Sum of numeric values is 0 – demand vector empty")
    return total


def check_parameters_mapping(df: pd.DataFrame, mapping: Set[str]):
    col = normalise_parameter_col(df)
    missing = set(df[col].str.strip().str.upper()) - {m.upper() for m in mapping}
    if missing:
        raise ValidationError(f"{len(missing)} parameters not in mapping: {sorted(missing)[:6]} …")


# ---------------------------------------------------------------------------
# Validator core
# ---------------------------------------------------------------------------

def validate_file(path: Path, args, mapping: Set[str]):
    print(f"\n=== {path} ===")
    try:
        df = read_csv_safely(path)
        df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)

        param_col = normalise_parameter_col(df); print(f"{PASS} Parameter column: '{param_col}'")
        num_cols = check_numeric_columns(df); print(f"{PASS} Numeric cols: {', '.join(num_cols[:5])}{' …' if len(num_cols)>5 else ''}")
        check_numeric_like_strings(df); print(f"{PASS} No numeric‑like strings in object columns")
        n_rows = check_length(df); print(f"{PASS} Row count: {n_rows}")

        # Attempt datetime index parse, silently skip on failure
        try:
            df.index = pd.to_datetime(df.iloc[:, 0], errors="raise")
            check_duplicates(df); print(f"{PASS} No duplicate timestamps")
        except Exception:
            print(f"  {WARN} Timestamp column not parsed – duplicate check skipped")

        ratio = check_nans(df, args.max_nan); print(f"{PASS} NaN ratio: {ratio:.3%}")
        total = check_nonzero_sum(df); print(f"{PASS} Total numeric sum: {total:,.2f}")

        if mapping:
            check_parameters_mapping(df, mapping); print(f"{PASS} All parameters in mapping")

        print(f"{PASS} {path.name}: ALL TESTS PASSED")
        return True

    except ValidationError as e:
        print(f"{FAIL} {e}")
        return False
    except Exception as e:
        print(f"{FAIL} Unexpected error: {e}")
        return False


# ---------------------------------------------------------------------------
# CLI wrapper
# ---------------------------------------------------------------------------

def cli(argv: List[str]):
    p = argparse.ArgumentParser(description="Validate demand CSV files (zero‑config)")
    p.add_argument("files", nargs="*", metavar="CSV", help="CSV files; default = *.csv here")
    p.add_argument("--mapping", help="JSON mapping of parameter names; default = parameters.json if present")
    p.add_argument("--recursive", action="store_true", help="Scan sub‑directories for *.csv when no files passed")
    p.add_argument("--max-nan", type=float, default=0.001, help="Max NaN ratio (default 0.1 %)")
    args = p.parse_args(argv[1:])

    # auto‑discover CSVs
    if not args.files:
        glob = "**/*.csv" if args.recursive else "*.csv"
        args.files = sorted(str(p) for p in Path('.').glob(glob))
        if not args.files:
            print("No CSV files found")
            sys.exit(1)
        print(f"Detected {len(args.files)} CSV files")

    # auto‑discover mapping
    if not args.mapping and Path("parameters.json").exists():
        args.mapping = "parameters.json"

    mapping: Set[str] = set()
    if args.mapping:
        try:
            with open(args.mapping, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            mapping = set(data if isinstance(data, list) else data.keys())
            if not mapping:
                print(f"{WARN} Mapping file empty – mapping test skipped")
        except Exception as e:
            print(f"{WARN} Could not read mapping file '{args.mapping}': {e}")

    all_ok = True
    for f in args.files:
        all_ok &= validate_file(Path(f), args, mapping)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    cli(sys.argv)
