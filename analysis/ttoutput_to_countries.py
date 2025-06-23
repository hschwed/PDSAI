# Uses [output.csv] and [countries.csv]
# Filters output.csv to the 57 COUNTRY-level region_ids in countries.csv
# and writes the reduced CSV to outputs/country_output.csv

from pathlib import Path
import pandas as pd
import sys

RAW          = Path("output.csv")
COUNTRIES    = Path("countries.csv")
OUT          = Path("outputs/country_output.csv")
OUT.parent.mkdir(exist_ok=True)

# ─────────────────── 1. Load list of valid region IDs ──────────────────
try:
    ref = pd.read_csv(COUNTRIES)
except FileNotFoundError:
    sys.exit(f"❌ {COUNTRIES} not found")

valid_ids = (
    ref.loc[ref["region_level"].str.upper() == "COUNTRY", "region_id"]
       .astype(int)
       .tolist()
)
if not valid_ids:
    sys.exit("❌ No COUNTRY-level rows found in countries.csv")

# ─────────────────── 2. Load TikTok export ─────────────────────────────
try:
    df = pd.read_csv(RAW)
except FileNotFoundError:
    sys.exit(f"❌ {RAW} not found")

# ─────────────────── 3. Locate region column ──────────────────────────
candidates = [c for c in df.columns]
preferred  = ["region_id", "regionId", "region", "region_code"]

region_col = next((c for c in preferred if c in candidates), None)
if region_col is None:
    sys.exit(
        "❌ No region-ID column found in output.csv.\n"
        f"   Available columns: {list(df.columns)}\n"
        "   Expected one of:  region_id, regionId, region, region_code"
    )

# Ensure integer type
df[region_col] = pd.to_numeric(df[region_col], errors="coerce").astype("Int64")

# ─────────────────── 4. Filter to the 57 countries ────────────────────
before = len(df)
df = df[df[region_col].isin(valid_ids)].copy()
after = len(df)

# ─────────────────── 5. Save result ───────────────────────────────────
df.to_csv(OUT, index=False)
print(
    f"✓ {OUT} written "
    f"(kept {after:,} of {before:,} rows; "
    f"{len(valid_ids)} valid COUNTRY region_ids)"
)
