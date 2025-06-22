# analysis/debug_gender_gap.py
# ------------------------------------------------------------------
# Print key checkpoints used by gender_gap_tables.py so you can see
# exactly what columns exist and how many rows survive each step.
# ------------------------------------------------------------------
from pathlib import Path
import pandas as pd
import re

TT  = Path("outputs/tt_clean.csv")
POP = Path("reference/pop_by_country_buckets_stripped.csv")

RANGE_MAP = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}
normalize = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())

# 1) ── population file -------------------------------------------------
pop = pd.read_csv(POP)
print("\nPOP FILE")
print("  shape :", pop.shape)
print("  first 3 bucket columns :", [c for c in pop.columns if "_" in c][:3])

# melt → tidy
pop_long = (
    pop.set_index(["country_code", "country_name"])
       .stack()
       .reset_index()
       .rename(columns={"level_2": "tmp", 0: "pop"})
)
pop_long[["sex", "bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
print("  pop_long :", pop_long.shape)
print(pop_long.head(3))

# 2) ── TikTok file -----------------------------------------------------
aud = pd.read_csv(TT)
print("\nTIKTOK FILE")
print("  shape :", aud.shape)
print("  columns :", list(aud.columns)[:10])

# check ISO codes
if aud["country_code"].isna().all():
    name2iso = {normalize(n): c for n, c in
                zip(pop["country_name"], pop["country_code"])}
    aud["country_code"] = aud["country_name"].map(lambda x: name2iso.get(normalize(x)))
print("  country_code missing rows :", aud["country_code"].isna().sum())

# age bucket mapping
aud["bucket"] = aud["age_bucket"].map(RANGE_MAP)
print("  unknown age_bucket rows   :", aud["bucket"].isna().sum())
print("  unique age_buckets after map:", aud["bucket"].unique()[:10])

# ensure est_users present
if "est_users" not in aud.columns:
    aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2

print("  unique sex values :", aud["sex"].unique())

# group+pivot
pivot = (
    aud.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_code", "bucket"], columns="sex", values="est_users")
        .fillna(0)
        .reset_index()
)
print("\nAFTER PIVOT")
print("  columns :", list(pivot.columns))
print("  shape   :", pivot.shape)
print(pivot.head(3))

# force tiktok_male/female
rename_map = {c: f"tiktok_{c.strip().lower()}"
              for c in pivot.columns if c.strip().lower() in ("male", "female")}
pivot = pivot.rename(columns=rename_map)
for col in ("tiktok_male", "tiktok_female"):
    if col not in pivot.columns:
        print(f"⚠️  '{col}' missing – will be zeros in main script.")

# 3) ── merge preview ---------------------------------------------------
merged = pivot.merge(
    pop_long.pivot_table(index=["country_code","bucket"],
                         columns="sex", values="pop").reset_index(),
    on=["country_code","bucket"], how="inner"
)
print("\nMERGE RESULT")
print("  shape :", merged.shape)
print("  sample rows :")
print(merged.head())
