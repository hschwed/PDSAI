from pathlib import Path
import pandas as pd
import numpy as np
import re
import unicodedata

# ───────────────────────────── file paths ───────────────────────────
TT_FILE   = Path("outputs/tt_clean.csv")
POP_FILE  = Path("reference/pop_by_country_buckets_stripped.csv")
OUT_DIR   = Path("outputs"); OUT_DIR.mkdir(exist_ok=True)

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
    s = unicodedata.normalize("NFKD", str(s))
    s = s.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())

# -------------------------------------------------------------------
#  STEP A · read population file (absolute headcounts)
# -------------------------------------------------------------------
pop = pd.read_csv(POP_FILE)

# reshape to long form and tidy
pop_long = (
    pop.set_index(["country_code", "country_name"]).stack()
       .reset_index().rename(columns={"level_2": "tmp", 0: "pop"})
)
pop_long[["sex", "bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
pop_tidy = (
    pop_long.pivot_table(index=["country_code","bucket"],
                         columns="sex", values="pop")
            .reset_index()
            .rename(columns={"male": "pop_male", "female": "pop_female"})
)

# dictionary for country-name fallbacks
NAME2ISO = { _normal(n): c for n,c in zip(pop["country_name"], pop["country_code"]) }

# -------------------------------------------------------------------
#  STEP B · read TikTok data
# -------------------------------------------------------------------
# The following line was corrected to remove `thousands=','`
aud = pd.read_csv(TT_FILE)

# normalize age_bucket labels
aud["age_bucket"] = aud["age_bucket"].str.replace('-', '_')
aud["bucket"] = aud["age_bucket"].map(RANGE_MAP)
if aud["bucket"].isna().any():
    raise ValueError(f"Unknown age_bucket labels: {aud['age_bucket'][aud['bucket'].isna()].unique()}")

# -------------------------------------------------------------------
#  STEP C · ensure ISO-3 codes
# -------------------------------------------------------------------
try:
    import pycountry
    def _try_pycountry(name: str) -> str | None:
        try:
            return pycountry.countries.lookup(name).alpha_3
        except LookupError:
            return None
except ImportError:
    def _try_pycountry(_: str) -> None:
        return None

MANUAL = {
    "cotedivoire": "CIV", "ivorycoast": "CIV",
    "russia": "RUS", "russianfederation": "RUS",
    "southkorea": "KOR", "northkorea": "PRK",
    "northmacedonia": "MKD",
    "viet": "VNM", "laos": "LAO",
    "bolivia": "BOL", "venezuela": "VEN",
}

aud["country_code"] = aud.get("country_code", "").fillna("").str.strip()
mask = aud["country_code"] == ""
aud.loc[mask, "country_code"] = (
    aud.loc[mask, "country_name"].apply(lambda n: _try_pycountry(n)
                                        or MANUAL.get(_normal(n))
                                        or NAME2ISO.get(_normal(n)))
)
# drop any remaining missing
aud = aud.dropna(subset=["country_code"])

# -------------------------------------------------------------------
#  STEP D · aggregate TikTok audience
# -------------------------------------------------------------------
if "est_users" not in aud.columns:
    aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

aud_tidy = (
    aud.groupby(["country_code","bucket","sex"], as_index=False)["est_users"]
       .sum()
       .pivot(index=["country_code","bucket"], columns="sex", values="est_users")
       .fillna(0)
       .reset_index()
       .rename(columns={"male": "tiktok_male", "female": "tiktok_female"})
)

# -------------------------------------------------------------------
#  STEP E · merge and compute metrics
# -------------------------------------------------------------------
merged = aud_tidy.merge(pop_tidy, on=["country_code","bucket"], how="inner")
if merged.empty:
    raise RuntimeError("Merged table is empty – check ISO codes & bucket labels in your input files")

# penetration and gap
merged["pen_male"] = np.where(merged["pop_male"]>0,
                                merged["tiktok_male"]/merged["pop_male"], 0)
merged["pen_female"] = np.where(merged["pop_female"]>0,
                                  merged["tiktok_female"]/merged["pop_female"], 0)
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
den = merged["pen_male"] + merged["pen_female"]
merged["gap_pct"] = np.where(den>0, 100*merged["gap_abs"]/den, 0)

# round
merged[["pen_male","pen_female","gap_abs","gap_pct"]] = \
    merged[["pen_male","pen_female","gap_abs","gap_pct"]].round(4)

# write country-level
merged.to_csv(OUT_DIR/"penetration_by_country.csv", index=False)
print(f"✓ penetration_by_country.csv -> {len(merged):,} rows")

# -------------------------------------------------------------------
#  STEP F · bucket-level world totals
# -------------------------------------------------------------------
world = (
    merged.groupby("bucket")[["tiktok_male","tiktok_female","pop_male","pop_female"]]
          .sum()
          .reset_index()
)
world["pen_male"] = np.where(world["pop_male"]>0,
                               world["tiktok_male"]/world["pop_male"], 0)
world["pen_female"] = np.where(world["pop_female"]>0,
                                 world["tiktok_female"]/world["pop_female"], 0)
world["gap_abs"] = world["pen_male"] - world["pen_female"]
den_w = world["pen_male"] + world["pen_female"]
world["gap_pct"] = np.where(den_w>0, 100*world["gap_abs"]/den_w, 0)
world[["pen_male","pen_female","gap_abs","gap_pct"]] = \
    world[["pen_male","pen_female","gap_abs","gap_pct"]].round(4)

world.to_csv(OUT_DIR/"penetration_by_bucket.csv", index=False)
print(f"✓ penetration_by_bucket.csv -> {len(world):,} buckets")

# -------------------------------------------------------------------
#  STEP G · overall & by-country totals
# -------------------------------------------------------------------
overall = merged[["tiktok_male","tiktok_female"]].sum().rename({
    "tiktok_male":"total_male","tiktok_female":"total_female"
}).to_frame().T
overall["gap_abs"] = overall["total_male"] - overall["total_female"]
coln = overall["total_male"] + overall["total_female"]
overall["gap_pct"] = np.where(coln>0, 100*overall["gap_abs"]/coln, 0)
overall[["gap_abs","gap_pct"]] = overall[["gap_abs","gap_pct"]].round(4)
overall.to_csv(OUT_DIR/"overall_gap.csv", index=False)

by_cty = (
    merged.groupby("country_code")[["tiktok_male","tiktok_female"]]
          .sum()
          .rename(columns={"tiktok_male":"total_male","tiktok_female":"total_female"})
          .reset_index()
)
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
coln2 = by_cty["total_male"] + by_cty["total_female"]
by_cty["gap_pct"] = np.where(coln2>0, 100*by_cty["gap_abs"]/coln2, 0)
by_cty[["gap_abs","gap_pct"]] = by_cty[["gap_abs","gap_pct"]].round(4)
by_cty.to_csv(OUT_DIR/"gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")
