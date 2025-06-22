"""
gender_gap_tables.py – TikTok penetration & gender-gap by age bucket
--------------------------------------------------------------------
Reads
  • outputs/tt_clean.csv                       – slim TikTok export
  • reference/pop_by_country_buckets_stripped.csv   – pop buckets (2024)

Writes to outputs/
  • penetration_by_country.csv   – country × bucket
  • penetration_by_bucket.csv    – world totals
  • overall_gap.csv, gap_by_country.csv        – legacy totals
"""

from pathlib import Path
import pandas as pd
import numpy as np
import re, unicodedata

# ───────────────────────────── file paths ───────────────────────────
TT_FILE  = Path("outputs/tt_clean.csv")
POP_FILE = Path("reference/pop_by_country_buckets_stripped.csv")
OUT_DIR  = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)

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
    """ASCII-only, lowercase, no punctuation → handy dict key."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())

# -------------------------------------------------------------------
#  STEP A · read population file  (already has ISO-3 codes)
# -------------------------------------------------------------------
pop = pd.read_csv(POP_FILE)
pop.iloc[:, 2:] = pop.iloc[:, 2:] * 1_000

pop_long = (
    pop.set_index(["country_code", "country_name"])
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

# dictionary to convert *cleaned* country names → ISO-3
NAME2ISO = {_normal(n): c for n, c in
            zip(pop["country_name"], pop["country_code"])}

# -------------------------------------------------------------------
#  STEP B · read TikTok file
# -------------------------------------------------------------------
aud = pd.read_csv(TT_FILE)

# ensure age bucket column matches RANGE_MAP -------------------------
aud["bucket"] = aud["age_bucket"].map(RANGE_MAP)
unknown = aud["bucket"].isna().sum()
if unknown:
    raise ValueError(f"{unknown:,} TikTok rows have unknown age_bucket labels")

# -------------------------------------------------------------------
#  STEP C · obtain ISO-3 codes for every TikTok row
# -------------------------------------------------------------------
# 1) attempt automatic match via `pycountry`
try:
    import pycountry
    def _try_pycountry(name: str) -> str | None:
        try:
            return pycountry.countries.lookup(name).alpha_3
        except LookupError:
            return None
except ImportError:
    def _try_pycountry(_): return None          # pycountry not installed

# 2) manual fall-backs for tricky names
MANUAL = {
    "cotedivoire": "CIV", "ivorycoast": "CIV",
    "russia": "RUS", "russianfederation": "RUS",
    "southkorea": "KOR", "northkorea": "PRK",
    "northmacedonia": "MKD",
    "viet": "VNM", "laos": "LAO",
    "bolivia": "BOL", "venezuela": "VEN",
}

def to_iso3(name: str) -> str | None:
    return _try_pycountry(name) or MANUAL.get(_normal(name)) \
           or NAME2ISO.get(_normal(name))

aud["country_code"] = aud["country_code"].fillna("").str.strip()
aud.loc[aud["country_code"] == "", "country_code"] = (
    aud.loc[aud["country_code"] == "", "country_name"].apply(to_iso3)
)

missing_iso = aud["country_code"].isna().sum()
print(f"ISO-3 mapping → {len(aud)-missing_iso:,} rows mapped , {missing_iso:,} missing")
if missing_iso:
    aud = aud.dropna(subset=["country_code"])

# -------------------------------------------------------------------
#  STEP D · tidy TikTok audience
# -------------------------------------------------------------------
# guarantee est_users column
if "est_users" not in aud.columns:
    aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

aud_tidy = (
    aud.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_code", "bucket"], columns="sex", values="est_users")
        .fillna(0)
        .reset_index()
        .rename(columns={"male": "tiktok_male", "female": "tiktok_female"})
)

# -------------------------------------------------------------------
#  STEP E · merge with population + compute metrics
# -------------------------------------------------------------------
merged = aud_tidy.merge(pop_tidy, on=["country_code", "bucket"], how="inner")

if merged.empty:
    raise RuntimeError("Merged table is empty – check ISO codes & bucket labels")

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (
    merged["pen_male"] + merged["pen_female"]
)

merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv →", len(merged), "rows")

# -------------------------------------------------------------------
#  STEP F · world totals by bucket
# -------------------------------------------------------------------
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
print("✓ penetration_by_bucket.csv  →", len(world), "buckets")

# -------------------------------------------------------------------
#  STEP G · legacy totals (overall & by country)
# -------------------------------------------------------------------
overall = merged[["tiktok_male","tiktok_female"]].sum().rename({
            "tiktok_male":   "total_male",
            "tiktok_female": "total_female"
          }).to_frame().T
overall["gap_abs"] = overall["total_male"] - overall["total_female"]
overall["gap_pct"] = 100 * overall["gap_abs"] / (
    overall["total_male"] + overall["total_female"])
overall.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_cty = (
    merged.groupby("country_code")[["tiktok_male","tiktok_female"]]
          .sum()
          .rename(columns={"tiktok_male":"total_male",
                           "tiktok_female":"total_female"})
          .reset_index()
)
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
by_cty["gap_pct"] = 100 * by_cty["gap_abs"] / (
    by_cty["total_male"] + by_cty["total_female"])
by_cty.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")
print("\nWorld buckets by |gap_pct| (top-5):")
print(world.reindex(world["gap_pct"].abs().sort_values(ascending=False).index)
           [["gap_pct"]].head())
