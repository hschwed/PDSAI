# uses [reference/countries.csv] & [outputs/country_output.csv]
# computes penetration rates & gender gaps for the filtered set
# Outputs: [penetration_by_country.csv]
#          [penetration_by_bucket.csv]
#          [overall_gap.csv]
#          [gap_by_country.csv]



from pathlib import Path
import pandas as pd
import numpy as np
import re, unicodedata
import sys


# ───────────────────────── file paths ───────────────────────────
TT_FILE       = Path("outputs/country_output.csv")
POP_FILE      = Path("reference/pop_by_country_buckets_stripped.csv")
COUNTRIES_CSV = Path("countries.csv")
OUT_DIR       = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────── age-bucket map ─────────────────────────
RANGE_MAP = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}

# ────────────────────── helper functions ────────────────────────────
def _normal(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())

# -------------------------------------------------------------------
# STEP A · read population file (no extra scaling)
# -------------------------------------------------------------------
pop = pd.read_csv(POP_FILE)
pop_long = (
    pop.set_index(["country_code","country_name"])
       .stack()
       .reset_index()
       .rename(columns={"level_2":"tmp",0:"pop"})
)
pop_long[["sex","bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
pop_tidy = (
    pop_long.pivot_table(
        index=["country_code","bucket"],
        columns="sex", values="pop", aggfunc="first"
    )
    .reset_index()
    .rename(columns={"male":"pop_male","female":"pop_female"})
)

# -------------------------------------------------------------------
# STEP B · read filtered TikTok export
# -------------------------------------------------------------------
try:
    aud = pd.read_csv(TT_FILE)
except FileNotFoundError:
    sys.exit(f"❌ {TT_FILE} not found")

# STEP B1: detect & normalize region_id column
region_cols = ["region_id","regionId","region","region_code","geo_location"]
for col in region_cols:
    if col in aud.columns:
        aud["region_id"] = pd.to_numeric(aud[col], errors="coerce").astype("Int64")
        break
else:
    sys.exit(
        "❌ No region-ID column found in country_output.csv\n"
        f"   Available: {list(aud.columns)}"
    )

# -------------------------------------------------------------------
# STEP C · map region_id to ISO-3 via countries.csv
# -------------------------------------------------------------------
try:
    ref = pd.read_csv(COUNTRIES_CSV)
except FileNotFoundError:
    sys.exit(f"❌ {COUNTRIES_CSV} not found")

mapping = (
    ref.loc[ref["region_level"].str.upper()=="COUNTRY", ["region_id","country_code"]]
       .dropna()
       .astype({"region_id":int})
)
aud = aud.merge(mapping, on="region_id", how="left")
aud = aud.dropna(subset=["country_code"])
aud["country_code"] = aud["country_code"].astype(str)

# -------------------------------------------------------------------
# STEP D · map age buckets & prepare for aggregation
# -------------------------------------------------------------------
aud["bucket"] = aud["ages_ranges"].map(RANGE_MAP)
if aud["bucket"].isna().any():
    unknown = aud.loc[aud["bucket"].isna(), "ages_ranges"].unique()
    raise ValueError(f"Unknown age_bucket labels: {unknown}")

# ensure est_users exists
if "est_users" not in aud.columns:
    aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

# -------------------------------------------------------------------
# STEP E · aggregate TikTok by country_code, bucket, sex
# -------------------------------------------------------------------
aud_tidy = (
    aud.groupby(["country_code","bucket","sex"], as_index=False)["est_users"]
       .sum()
       .pivot(index=["country_code","bucket"], columns="sex", values="est_users")
       .fillna(0)
       .reset_index()
       .rename(columns={"male":"tiktok_male","female":"tiktok_female"})
)

# -------------------------------------------------------------------
# STEP F · merge with population + compute metrics
# -------------------------------------------------------------------
merged = aud_tidy.merge(pop_tidy, on=["country_code","bucket"], how="inner")
if merged.empty:
    raise RuntimeError("Empty merge – check country codes & buckets")

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"]    = merged["pen_male"] - merged["pen_female"]
den = merged["pen_male"] + merged["pen_female"]
merged["gap_pct"]    = np.where(den>0, 100*merged["gap_abs"]/den, 0)

# round final metrics
for col in ["pen_male","pen_female","gap_abs","gap_pct"]:
    merged[col] = merged[col].round(4)

# output country-level
merged.to_csv(OUT_DIR/"penetration_by_country.csv", index=False)
print(f"✓ penetration_by_country.csv -> {len(merged):,} rows")

# -------------------------------------------------------------------
# STEP G · world totals by bucket
# -------------------------------------------------------------------
world = (
    merged.groupby("bucket")[["tiktok_male","tiktok_female","pop_male","pop_female"]]
          .sum()
          .assign(
             pen_male   = lambda d: d.tiktok_male  / d.pop_male,
             pen_female = lambda d: d.tiktok_female/ d.pop_female
          )
)
world["gap_abs"] = world.pen_male - world.pen_female
den_w = world.pen_male + world.pen_female
world["gap_pct"] = np.where(den_w>0, 100*world.gap_abs/den_w, 0)
for col in ["pen_male","pen_female","gap_abs","gap_pct"]:
    world[col] = world[col].round(4)

world.to_csv(OUT_DIR/"penetration_by_bucket.csv", index=False)
print(f"✓ penetration_by_bucket.csv -> {len(world):,} buckets")

# -------------------------------------------------------------------
# STEP H · legacy totals
# -------------------------------------------------------------------
overall = merged[["tiktok_male","tiktok_female"]].sum().rename({
    "tiktok_male":"total_male","tiktok_female":"total_female"
}).to_frame().T
overall["gap_abs"] = overall.total_male - overall.total_female
den_o = overall.total_male + overall.total_female
overall["gap_pct"] = np.where(den_o>0, 100*overall.gap_abs/den_o, 0)
overall[["gap_abs","gap_pct"]] = overall[["gap_abs","gap_pct"]].round(4)
overall.to_csv(OUT_DIR/"overall_gap.csv", index=False)

by_cty = (
    merged.groupby("country_code")[["tiktok_male","tiktok_female"]]
          .sum()
          .reset_index()
          .rename(columns={"tiktok_male":"total_male","tiktok_female":"total_female"})
)
by_cty["gap_abs"] = by_cty.total_male - by_cty.total_female
den_c = by_cty.total_male + by_cty.total_female
by_cty["gap_pct"] = np.where(den_c>0, 100*by_cty.gap_abs/den_c, 0)
by_cty[["gap_abs","gap_pct"]] = by_cty[["gap_abs","gap_pct"]].round(4)
by_cty.to_csv(OUT_DIR/"gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")
