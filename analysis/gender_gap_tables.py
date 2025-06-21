from pathlib import Path
import pandas as pd
import numpy as np

RAW_FILE = Path("output.csv")
POP_FILE = Path("reference/pop_by_country_buckets.csv")
OUT_DIR  = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# helper to derive bucket label if needed
def make_bucket(df):
    if {"bucket", "age_bucket"} & set(df.columns):
        col = next(c for c in ["bucket","age_bucket"] if c in df.columns)
        return df[col].astype(str)
    if {"age_min","age_max"} <= set(df.columns):
        a = df["age_min"].astype(int)
        b = df["age_max"].astype(int)
        lab = np.where(b >= 55, "55plus",
                       np.where((a == 25) & (b == 34), "2534",
                       np.where((a == 35) & (b == 44), "3544",
                       np.where((a == 45) & (b == 54), "4554",
                       [f"{a_}{b_}" for a_, b_ in zip(a, b)]))))
        return lab.astype(str)
    raise ValueError("No bucket or age_min/age_max columns in output.csv")

# ------------------------------------------------------------------
# 1) TikTok audience  → tidy
aud = pd.read_csv(RAW_FILE)
aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2
aud = aud[aud["genders"].isin(["GENDER_MALE","GENDER_FEMALE"])]

aud["bucket"]       = make_bucket(aud)
aud["country_key"]  = aud["code"] if "code" in aud.columns else aud["name"]
aud["gender"]       = aud["genders"].map({"GENDER_MALE":"male",
                                          "GENDER_FEMALE":"female"})

aud_tidy = (
    aud.groupby(["country_key","bucket","gender"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_key","bucket"], columns="gender",
               values="est_users")
        .reset_index()
        .rename(columns={"male":"tiktok_male","female":"tiktok_female"})
)

# ------------------------------------------------------------------
# 2) Population  → tidy
pop = pd.read_csv(POP_FILE)
pop_long = (
    pop.set_index(["country_name","country_code"])
        .rename(columns=lambda c: c.replace("pop_",""))
        .stack().reset_index()
        .rename(columns={"level_2":"tmp", 0:"pop"})
)
pop_long[["sex","bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
pop_tidy = (pop_long.pivot_table(index=["country_name","bucket"],
                                 columns="sex", values="pop")
                    .reset_index()
                    .rename(columns={"male":"pop_male","female":"pop_female"})
                    .rename(columns={"country_name":"country_key"}))

# ------------------------------------------------------------------
# 3) Merge & metrics
merged = (aud_tidy
          .merge(pop_tidy, on=["country_key","bucket"], how="left")
          .dropna(subset=["pop_male","pop_female"]))

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (merged["pen_male"] + merged["pen_female"])

merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv")

# ------------------------------------------------------------------
# 4) World totals by bucket
world = (
    merged.groupby("bucket")[["tiktok_male","tiktok_female",
                              "pop_male","pop_female"]]
          .sum()
          .assign(pen_male   = lambda d: d["tiktok_male"]/d["pop_male"],
                  pen_female = lambda d: d["tiktok_female"]/d["pop_female"])
)
world["gap_abs"] = world["pen_male"] - world["pen_female"]
world["gap_pct"] = 100 * world["gap_abs"] / (world["pen_male"] + world["pen_female"])
world.to_csv(OUT_DIR / "penetration_by_bucket.csv")
print("✓ penetration_by_bucket.csv")

# ------------------------------------------------------------------
# 5) Legacy overall / by-country gap (unchanged)
tot = (aud.groupby("gender")["est_users"].sum()
          .rename({"male":"total_male","female":"total_female"})
          .to_frame().T)
tot["gap_abs"] = tot["total_male"] - tot["total_female"]
tot["gap_pct"] = 100 * tot["gap_abs"] / (tot["total_male"] + tot["total_female"])
tot.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_cty = (aud.groupby(["country_key","gender"])["est_users"].sum()
            .unstack(fill_value=0)
            .rename(columns={"male":"total_male","female":"total_female"})
            .reset_index())
by_cty["gap_abs"] = by_cty["total_male"] - by_cty["total_female"]
by_cty["gap_pct"] = 100 * by_cty["gap_abs"] / (by_cty["total_male"] + by_cty["total_female"])
by_cty.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv updated")

# ------------------------------------------------------------------
print("\nWorld buckets sorted by |gap_pct|:")
print(world.reindex(world["gap_pct"].abs().sort_values(ascending=False).index)
           [["gap_pct"]].head())
