from pathlib import Path
import pandas as pd
import numpy as np
import re
import unicodedata

# ───────────────────────────── file paths ───────────────────────────
TT_FILE   = Path("outputs/tt_clean.csv")
POP_FILE  = Path("outputs/pop_clean.csv")
FB_FILE = Path("outputs/fb_clean.csv")
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
fb = pd.read_csv(FB_FILE) # currently not used as we cannot construct relative index from the data at hand

############ start with TT
merged = tt.merge(pop, on=["country_code","bucket"], how="inner")
if merged.empty:
    raise RuntimeError("Merged table is empty – check ISO codes & bucket labels in your input files")
merged.to_csv("merged_pop.csv")

# penetration and gap
merged["pen_male"] = np.where(merged["pop_male"]>0,merged["tiktok_male"]/merged["pop_male"], 0)
merged["pen_female"] = np.where(merged["pop_female"]>0, merged["tiktok_female"]/merged["pop_female"], 0)

merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
den = merged["pen_male"] + merged["pen_female"]
merged["gap_pct"] = np.where(den>0, 100*merged["gap_abs"]/den, 0)

merged["tt_fm"] = np.where(merged["tiktok_male"]>0,  merged["tiktok_female"]/merged["tiktok_male"], 0).round(4)
merged["pop_fm"] = np.where(merged["pop_male"]>0,  merged["pop_female"]/merged["pop_male"], 0).round(4)
merged["relative_gap"] = np.where(merged["pop_fm"]>0, merged["tt_fm"]/merged["pop_fm"], 0).round(4)

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

world["tt_fm"] = np.where(world["tiktok_male"]>0, world["tiktok_female"]/world["tiktok_male"], 0).round(4)
world["pop_fm"] = np.where(world["pop_male"]>0,  world["pop_female"]/world["pop_male"], 0).round(4)
world["relative_gap"] = np.where(world["pop_fm"]>0, world["tt_fm"]/world["pop_fm"], 0).round(4)

world.to_csv(OUT_DIR/"penetration_by_bucket.csv", index=False)
print(f"✓ penetration_by_bucket.csv -> {len(world):,} buckets")

# -------------------------------------------------------------------
#  STEP G · overall  totals
# -------------------------------------------------------------------
overall = merged[["tiktok_male", "tiktok_female", "pop_male", "pop_female"]].sum().to_frame().T
#print(overall.head())

overall["pen_male"] = np.where(overall["pop_male"]>0,
                               overall["tiktok_male"]/overall["pop_male"], 0)
overall["pen_female"] = np.where(overall["pop_female"]>0,
                                 overall["tiktok_female"]/overall["pop_female"], 0)

overall["gap_abs"] = overall["pen_male"] - overall["pen_female"]
den_w = overall["pen_male"] + overall["pen_female"]
overall["gap_pct"] = np.where(den_w>0, 100*overall["gap_abs"]/den_w, 0)
overall[["pen_male","pen_female","gap_abs","gap_pct"]] = \
    overall[["pen_male","pen_female","gap_abs","gap_pct"]].round(4)

overall["tt_fm"] = np.where(overall["tiktok_male"]>0, overall["tiktok_female"]/overall["tiktok_male"], 0).round(4)
overall["pop_fm"] = np.where(overall["pop_male"]>0,  overall["pop_female"]/overall["pop_male"], 0).round(4)
overall["relative_gap"] = np.where(overall["pop_fm"]>0, overall["tt_fm"]/overall["pop_fm"], 0).round(4)

overall.to_csv(OUT_DIR/"overall_gap.csv", index=False)
print("✓ overall_gap.csv refreshed")

# -------------------------------------------------------------------
#  STEP G ·  by-country totals
# -------------------------------------------------------------------

by_cty = (
    merged.groupby("country_code")[["tiktok_male", "tiktok_female", "pop_male", "pop_female"]]
          .sum()
          .reset_index()
)
#print(by_cty.head())

by_cty["pen_male"] = np.where(by_cty["pop_male"]>0,
                               by_cty["tiktok_male"]/by_cty["pop_male"], 0)
by_cty["pen_female"] = np.where(by_cty["pop_female"]>0,
                                 by_cty["tiktok_female"]/by_cty["pop_female"], 0)

by_cty["gap_abs"] = by_cty["pen_male"] - by_cty["pen_female"]
den_w = by_cty["pen_male"] + by_cty["pen_female"]
by_cty["gap_pct"] = np.where(den_w>0, 100*by_cty["gap_abs"]/den_w, 0)
by_cty[["pen_male","pen_female","gap_abs","gap_pct"]] = \
    by_cty[["pen_male","pen_female","gap_abs","gap_pct"]].round(4)

by_cty["tt_fm"] = np.where(by_cty["tiktok_male"]>0, by_cty["tiktok_female"]/by_cty["tiktok_male"], 0).round(4)
by_cty["pop_fm"] = np.where(by_cty["pop_male"]>0,  by_cty["pop_female"]/by_cty["pop_male"], 0).round(4)
by_cty["relative_gap"] = np.where(by_cty["pop_fm"]>0, by_cty["tt_fm"]/by_cty["pop_fm"], 0).round(4)

by_cty.to_csv(OUT_DIR/"gap_by_country.csv", index=False)

print("✓ gap_by_country.csv refreshed")

##### Facebook, only keep those countries for which we have matching tt data

tt_clean = pd.read_csv("outputs/tt_clean.csv", encoding="utf-8-sig")  # adjust path if needed

# Filter Facebook df to only keep countries in tt_clean
merged = by_cty.merge(fb, on=["country_code"], how="inner")
if merged.empty:
    raise RuntimeError("Merged table is empty – check ISO codes & bucket labels in your input files")
merged.to_csv("merged_fb.csv")

