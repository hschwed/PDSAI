"""
gender_gap_tables.py – TikTok penetration & gender gap by age bucket
--------------------------------------------------------------------
Reads
  • outputs/tt_clean.csv                         – slim TikTok export
  • reference/pop_by_country_buckets_stripped.csv
      ↳ columns: country_code, country_name,
                 male_1014, female_1014, … , male_55plus, female_55plus

Writes to outputs/
  • penetration_by_country.csv   – country × age bucket
  • penetration_by_bucket.csv    – world totals by age bucket
  • overall_gap.csv, gap_by_country.csv          – legacy totals
"""

from pathlib import Path
import pandas as pd
import re

SLIM_TT  = Path("outputs/tt_clean.csv")
POP_FILE = Path("reference/pop_by_country_buckets_stripped.csv")  # <── new file
OUT_DIR  = Path("outputs"); OUT_DIR.mkdir(exist_ok=True)

# ── helpers ─────────────────────────────────────────────────────────
RANGE_MAP = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}
normalize = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())

# ── 1 · population buckets (already stripped) ──────────────────────
pop = pd.read_csv(POP_FILE)
name2iso = {normalize(n): c for n, c in
            zip(pop["country_name"], pop["country_code"])}

# melt → tidy
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
            .rename(columns={"male": "pop_male",
                             "female": "pop_female"})
)

# ── 2 · TikTok slim file → tidy ────────────────────────────────────
aud = pd.read_csv(SLIM_TT)

# map ISO codes if missing
if aud["country_code"].isna().all():
    aud["country_code"] = aud["country_name"].map(lambda x: name2iso.get(normalize(x)))

aud = aud.dropna(subset=["country_code"])

# age bucket mapping
aud["bucket"] = aud["age_bucket"].map(RANGE_MAP)
n_bad = aud["bucket"].isna().sum()
if n_bad:
    print(f"⚠️  {n_bad:,} TikTok rows had unknown buckets – skipped.")
aud = aud.dropna(subset=["bucket"])

# ensure est_users column is present
if "est_users" not in aud.columns:
    aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

aud_tidy = (
    aud.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_code", "bucket"],
               columns="sex", values="est_users")
        .fillna(0)
        .reset_index()
)

# force columns tiktok_male / tiktok_female
rename_map = {c: f"tiktok_{c.strip().lower()}"
              for c in aud_tidy.columns
              if c.strip().lower() in ("male", "female")}
aud_tidy = aud_tidy.rename(columns=rename_map)
for col in ("tiktok_male", "tiktok_female"):
    if col not in aud_tidy.columns:
        print(f"⚠️  '{col}' missing – inserting zeros.")
        aud_tidy[col] = 0

# ── 3 · merge & metrics ────────────────────────────────────────────
merged = aud_tidy.merge(pop_tidy, on=["country_code", "bucket"], how="inner")

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (
    merged["pen_male"] + merged["pen_female"])

merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv  →", len(merged), "rows")

# ── 4 · world totals by bucket ─────────────────────────────────────
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

# ── 5 · legacy totals (unchanged) ──────────────────────────────────
tot = (aud.groupby("sex")["est_users"].sum()
          .rename({"male": "total_male", "female": "total_female"})
          .to_frame().T)
tot["gap_abs"] = tot["total_male"] - tot["total_female"]
tot["gap_pct"] = 100 * tot["gap_abs"] / (tot["total_male"] + tot["total_female"])
tot.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_cty = (aud.groupby(["country_code", "sex"])["est_users"].sum()
            .unstack(fill_value=0)
            .rename(columns={"male": "total_male",
                             "female": "total_female"})
            .reset_index())
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
by_cty["gap_pct"] = 100 * by_cty["gap_abs"] / (
    by_cty["total_male"] + by_cty["total_female"])
by_cty.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")

print("\nWorld buckets by |gap_pct| (top-5):")
print(world.reindex(world["gap_pct"].abs().sort_values(ascending=False).index)
           [["gap_pct"]].head())
