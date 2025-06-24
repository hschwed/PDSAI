# uses [reference/countries.csv] & [outputs/country_output.csv]
# computes penetration rates & gender gaps for the filtered set

# Inputs:
#   outputs/country_output.csv
#   reference/countries.csv
#   reference/pop_by_country_buckets_stripped.csv
# Outputs:
#   outputs/penetration_by_country.csv
#   outputs/penetration_by_bucket.csv
#   outputs/overall_gap.csv
#   outputs/gap_by_country.csv



from pathlib import Path
import pandas as pd
import numpy as np
import sys


# ───────────────────────── file paths ───────────────────────────
TT_FILE   = Path("outputs/country_output.csv")
POP_FILE  = Path("reference/pop_by_country_buckets_stripped.csv")
REF_FILE  = Path("countries.csv")
OUT_DIR   = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────── age-bucket map ─────────────────────
# TikTok → World Bank buckets
AGE2BKT = {
    # TikTok age-range  →  World-Bank bucket
    "AGE_13_17":  "1519",   # align 13-17 with WB 15-19
    "AGE_18_24":  "2024",   # 18-24 → 20-24
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus"  # keep WB’s 55+
}

# ─────────────────── 1. Load population buckets ─────────────────
pop = pd.read_csv(POP_FILE)

pop_long = (
    pop.set_index(["country_code", "country_name"])
       .stack()
       .reset_index()
       .rename(columns={"level_2": "tmp", 0: "pop"})
)
pop_long[["sex", "bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
pop_tidy = (
    pop_long.pivot_table(
        index=["country_code", "bucket"],
        columns="sex",
        values="pop",
        aggfunc="first"
    )
    .reset_index()
    .rename(columns={"male": "pop_male", "female": "pop_female"})
)

# ─────────────────── 2. Load countries reference ────────────────
ref = pd.read_csv(REF_FILE)
iso_map = (
    ref.loc[ref["region_level"].str.upper() == "COUNTRY", ["region_id", "country_code"]]
       .astype({"region_id": int})
)

# ─────────────────── 3. Load TikTok export ──────────────────────
aud = pd.read_csv(TT_FILE)

# build est_users & sex if missing
if "est_users" not in aud.columns:
    aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

if "sex" not in aud.columns and "genders" in aud.columns:
    aud["sex"] = aud["genders"].map({
        "GENDER_MALE": "male",
        "GENDER_FEMALE": "female"
    })

# map geo_location (region_id) → ISO-3 country_code
if "country_code" not in aud.columns:
    if "geo_location" not in aud.columns:
        sys.exit("❌ country_output.csv lacks both country_code and geo_location")
    aud = aud.merge(
        iso_map,
        left_on="geo_location",
        right_on="region_id",
        how="inner"
    )
    aud.drop(columns=["region_id"], inplace=True)

# sanity-check required columns
required = ["country_code", "ages_ranges", "sex", "est_users"]
missing  = [c for c in required if c not in aud.columns]
if missing:
    sys.exit(f"❌ Missing columns in {TT_FILE}: {missing}")

# map TikTok age labels → WB bucket codes
aud["bucket"] = aud["ages_ranges"].map(AGE2BKT)
bad = aud.loc[aud["bucket"].isna(), "ages_ranges"].unique()
if len(bad):
    sys.exit(f"❌ Unknown age ranges in TikTok file: {bad}")

# ─────────────────── 4. Aggregate TikTok audience ───────────────
aud_tidy = (
    aud.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"]
       .sum()
       .pivot(index=["country_code", "bucket"], columns="sex", values="est_users")
       .fillna(0)
       .reset_index()
       .rename(columns={"male": "tiktok_male", "female": "tiktok_female"})
)

# ─────────────────── 5. Merge & compute metrics ─────────────────
merged = aud_tidy.merge(pop_tidy, on=["country_code", "bucket"], how="inner")
if merged.empty:
    sys.exit("❌ Merge produced zero rows – check country codes & bucket labels")

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"]    = merged["pen_male"] - merged["pen_female"]
den = merged["pen_male"] + merged["pen_female"]
merged["gap_pct"]    = np.where(den > 0, 100 * merged["gap_abs"] / den, 0)

for col in ["pen_male", "pen_female", "gap_abs", "gap_pct"]:
    merged[col] = merged[col].round(4)

merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print(f"✓ penetration_by_country.csv → {len(merged):,} rows")

# ─────────────────── 6. World totals by bucket ──────────────────
world = (
    merged.groupby("bucket")[["tiktok_male", "tiktok_female", "pop_male", "pop_female"]]
          .sum()
          .assign(
              pen_male   = lambda d: d["tiktok_male"]   / d["pop_male"],
              pen_female = lambda d: d["tiktok_female"] / d["pop_female"]
          )
)
world["gap_abs"] = world["pen_male"] - world["pen_female"]
den_w = world["pen_male"] + world["pen_female"]
world["gap_pct"] = np.where(den_w > 0, 100 * world["gap_abs"] / den_w, 0)
world[["pen_male", "pen_female", "gap_abs", "gap_pct"]] = world[["pen_male", "pen_female", "gap_abs", "gap_pct"]].round(4)
world.to_csv(OUT_DIR / "penetration_by_bucket.csv", index=False)
print(f"✓ penetration_by_bucket.csv → {len(world):,} buckets")

# ─────────────────── 7. Legacy totals ───────────────────────────
overall = (
    merged[["tiktok_male", "tiktok_female"]]
      .sum()
      .rename({"tiktok_male": "total_male", "tiktok_female": "total_female"})
      .to_frame().T
)
overall["gap_abs"] = overall["total_male"] - overall["total_female"]
den_o = overall["total_male"] + overall["total_female"]
overall["gap_pct"] = np.where(den_o > 0, 100 * overall["gap_abs"] / den_o, 0)
overall[["gap_abs", "gap_pct"]] = overall[["gap_abs", "gap_pct"]].round(4)
overall.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_cty = (
    merged.groupby("country_code")[["tiktok_male", "tiktok_female"]]
          .sum()
          .reset_index()
          .rename(columns={"tiktok_male": "total_male", "tiktok_female": "total_female"})
)
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
den_c = by_cty["total_male"] + by_cty["total_female"]
by_cty["gap_pct"] = np.where(den_c > 0, 100 * by_cty["gap_abs"] / den_c, 0)
by_cty[["gap_abs", "gap_pct"]] = by_cty[["gap_abs", "gap_pct"]].round(4)
by_cty.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")
