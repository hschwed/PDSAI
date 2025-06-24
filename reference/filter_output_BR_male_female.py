# Reads output.csv, keeps only GENDER_MALE/GENDER_FEMALE rows
# and only those where name == "BR", then writes to reference/

from pathlib import Path
import pandas as pd

# ───────────────────────── file paths ───────────────────────────
RAW = Path("output.csv")
OUT = Path("reference/BR_male_female_output.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

# ──────────────────── load & filter data ────────────────────────
df = pd.read_csv(RAW)

# keep only male/female
df = df[df["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])]

# keep only rows where name == "BR"
df = df[df["name"] == "BR"]

# ─────────────────────── save result ────────────────────────────
df.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df):,} rows")
