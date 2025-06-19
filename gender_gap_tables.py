# work with output.csv
"""
Create gender-gap tables from TikTok audience estimates
------------------------------------------------------

How to run (from the repo root):

    python analysis/gender_gap_tables.py

Outputs
-------
1. outputs/overall_gap.csv
   • one row summing all countries, male vs female

2. outputs/gap_by_country.csv
   • one row per country with the same gap metrics

Both CSVs contain:
    total_male, total_female, gap_abs, gap_pct
"""

from pathlib import Path
import pandas as pd

# ------------------------------------------------------------------
# 1 ── Locate input & make sure output folders exist
# ------------------------------------------------------------------
RAW_FILE = Path("output.csv")       # written by app.py
OUT_DIR  = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# 2 ── Load data & basic cleaning
# ------------------------------------------------------------------
df = pd.read_csv(RAW_FILE)

# single-point audience estimate for every row
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2

# keep only explicit male / female rows
df = df[df["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])]

# ------------------------------------------------------------------
# 3 ── Overall table (all countries combined)
# ------------------------------------------------------------------
overall = (
    df.groupby("genders")["est_users"].sum()
      .rename({"GENDER_MALE": "total_male", "GENDER_FEMALE": "total_female"})
      .to_frame().T                               # turn the Series into a 1-row DataFrame
)
overall["gap_abs"] = overall["total_male"] - overall["total_female"]
overall["gap_pct"] = 100 * overall["gap_abs"] / (
    overall["total_male"] + overall["total_female"]
)

overall.to_csv(OUT_DIR / "overall_gap.csv", index=False)
print("✓ overall_gap.csv written")

# ------------------------------------------------------------------
# 4 ── Country-level table
# ------------------------------------------------------------------
by_country = (
    df.groupby(["name", "genders"])["est_users"]
      .sum()
      .unstack(fill_value=0)
      .rename(columns={"GENDER_MALE": "total_male",
                       "GENDER_FEMALE": "total_female"})
      .reset_index()
)

by_country["gap_abs"] = by_country["total_male"] - by_country["total_female"]
by_country["gap_pct"] = 100 * by_country["gap_abs"] / (
    by_country["total_male"] + by_country["total_female"]
)

by_country.to_csv(OUT_DIR / "gap_by_country.csv", index=False)
print("✓ gap_by_country.csv written")

# ------------------------------------------------------------------
# 5 ── Quick sanity check in terminal
# ------------------------------------------------------------------
print("\nTop 5 countries by |gap_pct|:")
print(by_country.reindex(by_country["gap_pct"].abs().sort_values(ascending=False).index)
                     .head(5)
                     [["name", "gap_pct"]])
