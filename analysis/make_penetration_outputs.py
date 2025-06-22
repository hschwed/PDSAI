# analysis/make_penetration_outputs.py
"""
Create two high-level outputs from penetration_by_country.csv
------------------------------------------------------------

Reads
  • outputs/penetration_by_country.csv   (built by gender_gap_tables.py)

Writes to outputs/
  1. penetration_summary.csv
       country_code · bucket · pen_total · pen_male · pen_female
       · gap_abs · gap_pct
  2. ranking_by_bucket.csv
       bucket-wise ranking of countries by gap_pct
       (rank 1 = largest male-advantage gap)

Run from repo root:
    python analysis/make_penetration_outputs.py
"""

from pathlib import Path
import pandas as pd

SRC      = Path("outputs/penetration_by_country.csv")
OUT_DIR  = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

# ── 1 · load source table ───────────────────────────────────────────
df = pd.read_csv(SRC)

# total users & penetration (both sexes combined)
df["tiktok_total"] = df["tiktok_male"] + df["tiktok_female"]
df["pop_total"]    = df["pop_male"]    + df["pop_female"]
df["pen_total"]    = df["tiktok_total"] / df["pop_total"]

# ── 2 · summary file (one row per country × bucket) ────────────────
summary_cols = [
    "country_code", "bucket",
    "pen_total", "pen_male", "pen_female",
    "gap_abs", "gap_pct"
]
summary = df[summary_cols].copy()
summary.to_csv(OUT_DIR / "penetration_summary.csv", index=False)
print("✓ penetration_summary.csv written →", len(summary), "rows")

# ── 3 · per-bucket ranking by gender gap ───────────────────────────
ranks = []
for bucket, grp in df.groupby("bucket"):
    ordered = grp.sort_values("gap_pct", ascending=False).reset_index(drop=True)
    ordered["rank_gap"] = ordered.index + 1     # rank 1 = largest male > female
    ranks.append(
        ordered[["bucket", "rank_gap", "country_code", "gap_pct", "pen_total"]]
    )

ranking = pd.concat(ranks, ignore_index=True)
ranking.to_csv(OUT_DIR / "ranking_by_bucket.csv", index=False)
print("✓ ranking_by_bucket.csv   written →", len(ranking), "rows")
