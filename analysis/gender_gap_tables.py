"""
Compute gender-gap *and* penetration tables
===========================================

Reads
------
• output.csv                          (TikTok queries, written by app.py)
• reference/pop_by_country_buckets.csv (2024 population counts you built)

New outputs
-----------
outputs/penetration_by_bucket.csv      one row per bucket (all countries)
outputs/penetration_by_country.csv     one row per country per bucket
   columns:  pop_male  pop_female  tiktok_male  tiktok_female
             pen_male  pen_female  gap_abs  gap_pct
(plus the existing overall_gap.csv and gap_by_country.csv)

Run from repo root:
    python analysis/gender_gap_tables.py
"""

from pathlib import Path
import pandas as pd

# ------------------------------------------------------------------
# 1 ── locate input & output paths
# ------------------------------------------------------------------
RAW_FILE   = Path("output.csv")
POP_FILE   = Path("reference/pop_by_country_buckets.csv")
OUT_DIR    = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

# TikTok buckets expected in RAW_FILE  →  column names in POP_FILE
BUCKET_MAP = {
    "1014": "1014",
    "1519": "1519",
    "2024": "2024",
    "2534": "2534",
    "3544": "3544",
    "4554": "4554",
    "55plus": "55plus",
}
# ------------------------------------------------------------------
# 2 ── TikTok audience: clean → long format
# ------------------------------------------------------------------
aud = pd.read_csv(RAW_FILE)

# single-point audience estimate
aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

# keep only explicit male / female rows
aud = aud[aud["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])]

# your TikTok code must include an age bucket column;
# rename it to "bucket" (values like '1014','1519', … '55plus')
aud = aud.rename(columns={"age_bucket": "bucket", "code": "country_code"})

aud["gender"] = aud["genders"].map(
    {"GENDER_MALE": "male", "GENDER_FEMALE": "female"}
)

aud_tidy = (
    aud.groupby(["country_code", "bucket", "gender"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_code", "bucket"],
               columns="gender", values="est_users")
        .fillna(0)
        .reset_index()
        .rename(columns={"male": "tiktok_male", "female": "tiktok_female"})
)

# ------------------------------------------------------------------
# 3 ── Population: wide → long → tidy
# ------------------------------------------------------------------
pop_wide = pd.read_csv(POP_FILE)

pop_long = (
    pop_wide
      .set_index(["country_code", "country_name"])
      .rename(columns=lambda c: c.replace("pop_", ""))   # drop 'pop_' prefix
      .stack()
      .reset_index()
      .rename(columns={"level_2": "tmp", 0: "pop"})
)

# split tmp into sex + bucket  (e.g. 'male_2534')
pop_long[["sex", "bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
pop_long = pop_long.drop(columns="tmp")

pop_tidy = (
    pop_long.pivot_table(index=["country_code", "bucket"],
                         columns="sex", values="pop")
            .reset_index()
            .rename(columns={"male": "pop_male", "female": "pop_female"})
)

# ------------------------------------------------------------------
# 4 ── Merge TikTok ↔ population
# ------------------------------------------------------------------
merged = (aud_tidy
          .merge(pop_tidy, on=["country_code", "bucket"], how="left")
          .dropna(subset=["pop_male", "pop_female"]))     # guards against ISO mismatches

# penetration rates
merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]

# gender gap (penetration diff & % diff)
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (merged["pen_male"] + merged["pen_female"])

# ------------------------------------------------------------------
# 5 ── Write penetration tables
# ------------------------------------------------------------------
# (a) overall by bucket (all countries combined)
overall_bucket = (
    merged.groupby("bucket")[["tiktok_male", "tiktok_female",
                              "pop_male", "pop_female"]]
          .sum()
          .assign(pen_male   = lambda d: d["tiktok_male"]   / d["pop_male"],
                  pen_female = lambda d: d["tiktok_female"] / d["pop_female"])
)
overall_bucket["gap_abs"] = overall_bucket["pen_male"] - overall_bucket["pen_female"]
overall_bucket["gap_pct"] = 100 * overall_bucket["gap_abs"] / (
    overall_bucket["pen_male"] + overall_bucket["pen_female"]
)

overall_bucket.to_csv(OUT_DIR / "penetration_by_bucket.csv")
print("✓ penetration_by_bucket.csv written")

# (b) by country & bucket
merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv written")

# ------------------------------------------------------------------
# 6 ── Retain original overall & by-country gender-gap tables
# ------------------------------------------------------------------
tot = (
    aud.groupby("gender")["est_users"].sum()
        .rename({"male": "total_male", "female": "total_female"})
        .to_frame().T
)
tot["gap_abs"] = tot["total_male"] - tot["total_female"]
tot["gap_pct"] = 100 * tot["gap_abs"] / (tot["total_male"] + tot["total_female"])
tot.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_country = (
    aud.groupby(["country_code", "gender"])["est_users"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"male": "total_male", "female": "total_female"})
        .reset_index()
)
by_country["gap_abs"] = by_country["total_male"] - by_country["total_female"]
by_country["gap_pct"] = 100 * by_country["gap_abs"] / (
    by_country["total_male"] + by_country["total_female"])
by_country.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv updated")

# ------------------------------------------------------------------
# 7 ── Quick sanity check
# ------------------------------------------------------------------
print("\nTop 5 buckets (all countries) by |gap_pct|:")
print(overall_bucket.reindex(overall_bucket["gap_pct"].abs()
                             .sort_values(ascending=False).index)
                    .head(5)[["gap_pct"]])
