"""
gender_gap_tables.py – compute TikTok penetration & gender-gap
from the *slim* file produced by analysis/edit_output_tt.py
----------------------------------------------------------------
Reads
  • outputs/tt_clean.csv                     (slim TikTok export)
  • reference/pop_by_country_buckets.csv     (population buckets)

Writes to outputs/
  • penetration_by_country.csv   (country × age bucket)
  • penetration_by_bucket.csv    (world totals per bucket)
  • overall_gap.csv, gap_by_country.csv      (legacy totals)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import re

# ------------------------------------------------------------------
RAW_FILE = Path("outputs/tt_clean.csv")           # <─ new slim file
POP_FILE = Path("reference/pop_by_country_buckets.csv")
OUT_DIR  = Path("outputs"); OUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# helper maps & utilities
RANGE_MAP = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}
def bucket_from_age_label(s: pd.Series) -> pd.Series:
    mapped = s.map(RANGE_MAP)
    if mapped.isna().any():
        raise ValueError("Unmapped age_bucket values:", mapped.unique())
    return mapped

normal = lambda x: re.sub(r"[^a-z0-9]", "", str(x).lower())

# ------------------------------------------------------------------
# 1 · population buckets  (gives ISO-3 codes + totals)
pop = pd.read_csv(POP_FILE)

name2iso = {normal(n): c for n, c in zip(pop["country_name"],
                                         pop["country_code"])}

pop_long = (
    pop.set_index(["country_code", "country_name"])
       .rename(columns=lambda c: c.replace("pop_", ""))
       .stack()
       .reset_index()
       .rename(columns={"level_2": "tmp", 0: "pop"})
)
pop_long[["sex", "bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
pop_tidy = (
    pop_long.pivot_table(index=["country_code", "bucket"],
                         columns="sex", values="pop")
            .reset_index()
            .rename(columns={"male": "pop_male", "female": "pop_female"})
)

# ------------------------------------------------------------------
# 2 · TikTok slim file → tidy                                              
aud = pd.read_csv(RAW_FILE)

# ensure ISO-3 code column present
if "country_code" not in aud.columns or aud["country_code"].isna().all():
    aud["country_code"] = aud["country_name"].map(lambda x: name2iso.get(normal(x)))

aud = aud.dropna(subset=["country_code", "sex", "age_bucket"])

# make sure est_users exists
if "est_users" not in aud.columns:
    aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

aud["bucket"] = bucket_from_age_label(aud["age_bucket"])

aud_tidy = (
    aud.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_code", "bucket"],
               columns="sex", values="est_users")
        .fillna(0)
        .reset_index()
        .rename(columns={"male": "tiktok_male",
                         "female": "tiktok_female"})
)

# ------------------------------------------------------------------
# 3 · merge with population & compute metrics
merged = aud_tidy.merge(pop_tidy, on=["country_code", "bucket"], how="inner")

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (
    merged["pen_male"] + merged["pen_female"])

merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv  →", len(merged), "rows")

# ------------------------------------------------------------------
# 4 · world totals by bucket
world = (
    merged.groupby("bucket")[["tiktok_male", "tiktok_female",
                              "pop_male", "pop_female"]]
          .sum()
          .assign(pen_male   = lambda d: d["tiktok_male"] / d["pop_male"],
                  pen_female = lambda d: d["tiktok_female"] / d["pop_female"])
)
world["gap_abs"] = world["pen_male"] - world["pen_female"]
world["gap_pct"] = 100 * world["gap_abs"] / (world["pen_male"] + world["pen_female"])
world.to_csv(OUT_DIR / "penetration_by_bucket.csv")
print("✓ penetration_by_bucket.csv   →", len(world), "buckets")

# ------------------------------------------------------------------
# 5 · legacy totals (unchanged logic)
tot = (aud.groupby("sex")["est_users"].sum()
          .rename({"male": "total_male", "female": "total_female"})
          .to_frame().T)
tot["gap_abs"] = tot["total_male"] - tot["total_female"]
tot["gap_pct"] = 100 * tot["gap_abs"] / (tot["total_male"] + tot["total_female"])
tot.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_cty = (aud.groupby(["country_code", "sex"])["est_users"].sum()
            .unstack(fill_value=0)
            .rename(columns={"male": "total_male", "female": "total_female"})
            .reset_index())
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
by_cty["gap_pct"] = 100 * by_cty["gap_abs"] / (
    by_cty["total_male"] + by_cty["total_female"])
by_cty.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")

print("\nWorld buckets by |gap_pct| (top-5):")
print(world.reindex(world["gap_pct"].abs().sort_values(ascending=False).index)
           [["gap_pct"]].head())
