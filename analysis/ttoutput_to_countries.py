# Uses [BR_male_female_output.csv] and [countries.csv]



# Keeps only rows whose geo_location matches one of the 57 COUNTRY-level region_ids
# Writes the reduced CSV to outputs/country_output.csv


from pathlib import Path
import pandas as pd
import sys

# ───────────────────────── file paths ───────────────────────────
INPUT       = Path("reference/BR_male_female_output.csv")
COUNTRIES   = Path("countries.csv")
OUT         = Path("outputs/country_output.csv")
OUT.parent.mkdir(exist_ok=True)

# ───────────── 1. Load list of valid region IDs ────────────────
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

# ───────────── 2. Load the filtered TikTok file ────────────────
try:
    df = pd.read_csv(INPUT)
except FileNotFoundError:
    sys.exit(f"❌ {INPUT} not found")

# ────────── 3. Ensure geo_location exists & is numeric ──────────
if "geo_location" not in df.columns:
    sys.exit(
        "❌ No 'geo_location' column found in "
        f"{INPUT}. Available columns: {list(df.columns)}"
    )
df["geo_location"] = pd.to_numeric(df["geo_location"], errors="coerce").astype("Int64")

# ───────────── 4. Filter to the 57 countries ────────────────
before = len(df)
df = df[df["geo_location"].isin(valid_ids)].copy()
after = len(df)

# ──────────── 5. Save the filtered output ────────────────
df.to_csv(OUT, index=False)
print(
    f"✓ {OUT} written "
    f"(kept {after:,} of {before:,} rows; "
    f"{len(valid_ids)} valid COUNTRY geo_locations)"
)
