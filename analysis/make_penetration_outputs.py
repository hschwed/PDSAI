# uses [penetration_by_country.csv]
# summarize & rank bucket gaps
# Outputs: [penetration_summary.csv]
# Outputs: [ranking_by_bucket.csv ]



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

# ── 3 · overall summary ───────────────────────────
tbl = pd.read_csv("outputs/penetration_by_country.csv")
tbl["tiktok_total"] = tbl["tiktok_male"] + tbl["tiktok_female"]
tbl["pop_total"]    = tbl["pop_male"]    + tbl["pop_female"]
tbl["pen_total"]    = tbl["tiktok_total"] / tbl["pop_total"]
tbl = tbl.describe().T
tbl = tbl.reset_index().rename(columns={'index': 'Variable'})
tbl.to_csv(OUT_DIR / "summary_table.csv")
print("✓ summary_table.csv   written →", len(ranking), "rows")
