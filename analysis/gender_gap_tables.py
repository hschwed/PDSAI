"""
gender_gap_tables.py  –  TikTok penetration & gender-gap by age bucket
----------------------------------------------------------------------
Reads
  • output.csv                              (TikTok audience export)
  • reference/pop_by_country_buckets.csv    (population buckets 2024)

Writes to outputs/
  • penetration_by_country.csv   (country × bucket detail)
  • penetration_by_bucket.csv    (world totals per bucket)
  • overall_gap.csv, gap_by_country.csv    (legacy totals)

Run from repo root:
    python analysis/gender_gap_tables.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
import re

RAW_FILE = Path("output.csv")
POP_FILE = Path("reference/pop_by_country_buckets.csv")
OUT_DIR  = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)

# ── helpers ─────────────────────────────────────────────────────────
RANGE_MAP = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}
def derive_bucket(df: pd.DataFrame) -> pd.Series:
    """Return a Series of bucket labels matching the population file."""
    if "bucket" in df.columns:
        return df["bucket"].astype(str)
    if "age_bucket" in df.columns:
        return df["age_bucket"].astype(str)
    if "ages_ranges" in df.columns:
        mapped = df["ages_ranges"].map(RANGE_MAP)
        if mapped.isna().any():
            raise ValueError("Unmapped ages_ranges values:", mapped.unique())
        return mapped
    if {"age_min", "age_max"} <= set(df.columns):
        a, b = df["age_min"].astype(int), df["age_max"].astype(int)
        return np.where(b >= 55, "55plus",
               np.where((a==25)&(b==34), "2534",
               np.where((a==35)&(b==44), "3544",
               np.where((a==45)&(b==54), "4554",
                        [f"{x:02d}{y:02d}" for x,y in zip(a,b)]))))
    raise ValueError("No age bucket info in TikTok file")

def normal(s:str)->str:
    """Lowercase + remove non-alnum (for fuzzy name matching)."""
    return re.sub(r"[^a-z0-9]", "", s.lower())

# ── 1 · population (gives ISO codes + long form) ────────────────────
pop = pd.read_csv(POP_FILE)

# map "cleaned" country name → ISO-3
name2iso = {normal(n): c for n, c in zip(pop["country_name"], pop["country_code"])}

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

# ── 2 · TikTok audience → tidy with ISO code ────────────────────────
aud = pd.read_csv(RAW_FILE)
aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2
aud = aud[aud["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])]

aud["bucket"] = derive_bucket(aud)

# ISO code column if present, else map from country name
aud["country_code"] = aud["code"] if "code" in aud.columns else \
                      aud["name"].map(lambda x: name2iso.get(normal(x)))
aud = aud.dropna(subset=["country_code"])        # drop rows we can’t map

aud["gender"] = aud["genders"].map({"GENDER_MALE": "male",
                                    "GENDER_FEMALE": "female"})

aud_tidy = (
    aud.groupby(["country_code", "bucket", "gender"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_code", "bucket"],
               columns="gender", values="est_users")
        .fillna(0)
        .reset_index()
        .rename_axis(None, axis=1)              # flatten MultiIndex header
        .rename(columns={"male": "tiktok_male",
                         "female": "tiktok_female"})
)

# ── 3 · merge + metrics ─────────────────────────────────────────────
merged = (aud_tidy
          .merge(pop_tidy, on=["country_code", "bucket"], how="inner"))

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (
    merged["pen_male"] + merged["pen_female"])

merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv  →", len(merged), "rows")

# ── 4 · world totals per bucket ─────────────────────────────────────
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

# ── 5 · legacy totals (unchanged) ───────────────────────────────────
tot = (aud.groupby("gender")["est_users"].sum()
          .rename({"male": "total_male", "female": "total_female"})
          .to_frame().T)
tot["gap_abs"] = tot["total_male"] - tot["total_female"]
tot["gap_pct"] = 100 * tot["gap_abs"] / (tot["total_male"] + tot["total_female"])
tot.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_cty = (aud.groupby(["country_code", "gender"])["est_users"].sum()
            .unstack(fill_value=0)
            .rename(columns={"male": "total_male", "female": "total_female"})
            .reset_index())
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
by_cty["gap_pct"] = 100 * by_cty["gap_abs"] / (
    by_cty["total_male"] + by_cty["total_female"])
by_cty.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")

print("\nWorld buckets by |gap_pct|:")
print(world.reindex(world["gap_pct"].abs().sort_values(ascending=False).index)
           [["gap_pct"]].head())
