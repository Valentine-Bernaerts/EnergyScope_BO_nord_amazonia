#!/usr/bin/env python3
"""convert_decimal.py
====================

Converteix un fitxer CSV separat per punt i coma (;) amb decimals en coma (",")
a un altre CSV amb els mateixos camps però amb decimals en punt (".").

Com usar‑lo
-----------
1. **Edita** les variables `CSV_INPUT` i `CSV_OUTPUT` aquí sota amb els noms (o
   rutes) del fitxer d’entrada i de sortida que vulguis.
2. Executa simplement:

       python convert_decimal.py

El fitxer de sortida mantindrà el separador de camps `;` però amb els decimals
en format anglosaxó (`.`).
"""

from __future__ import annotations

import os
import sys
import pandas as pd

# ────────────────────── CONFIGURA AQUI ────────────────────── #
CSV_INPUT = "Time_series.csv"      # ← Nom del CSV original (amb , com a decimal)
CSV_OUTPUT = "Time_series.csv"      # ← Nom del CSV convertit (amb . com a decimal)
# ──────────────────────────────────────────────────────────── #


def main() -> None:
    if not os.path.isfile(CSV_INPUT):
        print(f"❌ No s'ha trobat el fitxer d'entrada: {CSV_INPUT}")
        sys.exit(1)

    # Llegeix el CSV: separador ; i decimals ,
    df = pd.read_csv(CSV_INPUT, sep=";", decimal=",")

    # Escriu el CSV amb separador ; (pandas escriu els decimals amb . per defecte)
    df.to_csv(CSV_OUTPUT, sep=";", index=False)
    print(f"✅ Fitxer convertit desat a '{CSV_OUTPUT}'.")


if __name__ == "__main__":
    main()
