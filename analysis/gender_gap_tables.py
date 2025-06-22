from pathlib import Path
import pandas as pd
import numpy as np
import re

RAW_FILE = Path("output.csv")
POP_FILE = Path("reference/pop_by_country_buckets.csv")
OUT_DIR  = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)

# ── 1 · Helpers ────────────────────────────────────────────────────
RANGE_MAP = {           # TikTok label  → bucket key
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}
def derive_bucket(df: pd.DataFrame) -> pd.Series:
    if "bucket" in df.columns:
        return df["bucket"].astype(str)
    if "age_bucket" in df.columns:
        return df["age_bucket"].astype(str)
    if "ages_ranges" in df.columns:
        mapped = df["ages_ranges"].map(RANGE_MAP)
        if mapped.isna().any():
            miss = mapped[mapped.isna()].unique()
            raise ValueError(f"Unmapped ages_ranges values: {miss}")
        return mapped
    if {"age_min","age_max"} <= set(df.columns):
        a, b = df["age_min"], df["age_max"]
        lbl = np.where(b >= 55, "55plus",
               np.where((a==25)&(b==34), "2534",
               np.where((a==35)&(b==44), "3544",
               np.where((a==45)&(b==54), "4554",
               np.where((a==15)&(b==19), "1519",
                        [f"{int(x):02d}{int(y):02d}" for x,y in zip(a,b)])))))
        return lbl.astype(str)
    raise ValueError("No age-bucket information in output.csv")

def normal(s:str)->str:
    """lower-case alnum only (for fuzzy name match)."""
    return re.sub(r"[^a-z0-9]", "", s.lower())

# ── 2 · Population (gives good ISO codes) ──────────────────────────
pop = pd.read_csv(POP_FILE)
name2iso = {normal(n): c for n,c in
            zip(pop["country_name"], pop["country_code"])}

pop_long = (pop.set_index(["country_code","country_name"])
               .rename(columns=lambda c: c.replace("pop_",""))
               .stack().reset_index()
               .rename(columns={"level_2":"tmp", 0:"pop"}))
pop_long[["sex","bucket"]] = pop_long["tmp"].str.split("_", 1, expand=True)
pop_tidy = (pop_long.pivot_table(index=["country_code","bucket"],
                                 columns="sex", values="pop")
                     .reset_index()
                     .rename(columns={"male":"pop_male",
                                      "female":"pop_female"}))

# ── 3 · TikTok audience  → tidy with ISO code ──────────────────────
aud = pd.read_csv(RAW_FILE)
aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2
aud = aud[aud["genders"].isin(["GENDER_MALE","GENDER_FEMALE"])]

aud["bucket"] = derive_bucket(aud)

# choose ISO code column if present; else map name → ISO
if "code" in aud.columns:
    aud["country_code"] = aud["code"]
else:
    aud["country_code"] = aud["name"].map(lambda x: name2iso.get(normal(x)))
aud = aud.dropna(subset=["country_code"])          # rows we can’t map are unusable

aud["gender"] = aud["genders"].map({"GENDER_MALE":"male",
                                    "GENDER_FEMALE":"female"})
aud_tidy = (aud.groupby(["country_code","bucket","gender"], as_index=False)
                ["est_users"].sum()
                .pivot(index=["country_code","bucket"],
                       columns="gender", values="est_users")
                .fillna(0)
                .reset_index()
                .rename(columns={"male":"tiktok_male",
                                 "female":"tiktok_female"}))

# ── 4 · Merge & metrics ────────────────────────────────────────────
merged = (aud_tidy
          .merge(pop_tidy, on=["country_code","bucket"], how="inner"))

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (
    merged["pen_male"] + merged["pen_female"])

# ── 5 · Write outputs ───────────────────────────────────────────────
merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv  →", len(merged), "rows")

world = (merged.groupby("bucket")[["tiktok_male","tiktok_female",
                                   "pop_male","pop_female"]]
                 .sum()
                 .assign(pen_male   = lambda d: d["tiktok_male"]/d["pop_male"],
                         pen_female = lambda d: d["tiktok_female"]/d["pop_female"]))
world["gap_abs"] = world["pen_male"] - world["pen_female"]
world["gap_pct"] = 100 * world["gap_abs"] / (world["pen_male"] + world["pen_female"])
world.to_csv(OUT_DIR / "penetration_by_bucket.csv")
print("✓ penetration_by_bucket.csv   →", len(world), "buckets")

# legacy totals (unchanged)
tot = (aud.groupby("gender")["est_users"].sum()
          .rename({"male":"total_male","female":"total_female"})
          .to_frame().T)
tot["gap_abs"] = tot["total_male"] - tot["total_female"]
tot["gap_pct"] = 100 * tot["gap_abs"] / (tot["total_male"] + tot["total_female"])
tot.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_cty = (aud.groupby(["country_code","gender"])["est_users"].sum()
            .unstack(fill_value=0)
            .rename(columns={"male":"total_male","female":"total_female"})
            .reset_index())
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
by_cty["gap_pct"] = 100 * by_cty["gap_abs"] / (
    by_cty["total_male"] + by_cty["total_female"])
by_cty.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv refreshed")

print("\nWorld buckets by |gap_pct|:")
print(world.reindex(world["gap_pct"].abs().sort_values(ascending=False).index)
           [["gap_pct"]])
