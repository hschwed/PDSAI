# Uses [output.csv] and [countries.csv]
# Filters the TikTok export to only the 57 COUNTRY-level region_ids,
# and writes the reduced file to outputs/country_output.csv

from pathlib import Path
import pandas as pd

# ───────────────────────── file paths ───────────────────────────
RAW           = Path("output.csv")
COUNTRIES_CSV = Path("countries.csv")
OUT           = Path("outputs/country_output.csv")
OUT.parent.mkdir(exist_ok=True)

# ──────────────────── load reference list ────────────────────────
countries = pd.read_csv(COUNTRIES_CSV)
# select only rows at the COUNTRY level
valid_ids = countries.loc[
    countries["region_level"] == "COUNTRY",
    "region_id"
].astype(int).tolist()

# ───────────────────── load & filter data ───────────────────────
df = pd.read_csv(RAW)

# if region_id is not integer, cast it
df["region_id"] = df["region_id"].astype(int)

# keep only the 57 countries
df = df[df["region_id"].isin(valid_ids)].copy()

# ─────────────────────── save filtered output ───────────────────
df.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df):,} rows (filtered to {len(valid_ids)} countries)")
