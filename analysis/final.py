from pathlib import Path
import pandas as pd
import numpy as np
import re
import unicodedata

# ───────────────────────────── file paths ───────────────────────────
TT_FILE   = Path("outputs/tt_clean.csv")
POP_FILE  = Path("outputs/pop_clean.csv")
OUT_DIR   = Path("outputs"); OUT_DIR.mkdir(exist_ok=True)

# ────────────────────── helper functions ────────────────────────────
def _normal(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = s.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())

# -------------------------------------------------------------------
#  STEP A · merge and compute metrics
# -------------------------------------------------------------------
pop = pd.read_csv(POP_FILE)
tt = pd.read_csv(TT_FILE)

merged = tt.merge(pop, on=["country_code","bucket"], how="inner")
if merged.empty:
    raise RuntimeError("Merged table is empty – check ISO codes & bucket labels in your input files")
merged.to_csv("merged.csv")

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
