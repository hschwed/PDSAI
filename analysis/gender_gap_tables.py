from pathlib import Path
import pandas as pd

RAW_FILE = Path("output.csv")                     # TikTok audience
POP_FILE = Path("reference/pop_by_country_buckets.csv")
OUT_DIR  = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)

# TikTok ↔ population bucket codes
ATOMIC  = ["1014","1519","2024"]
COMBO   = {"2534": ["2529","3034"],
           "3544": ["3539","4044"],
           "4554": ["4549","5054"]}
PLUS    = ["5559","6064","6569","7074","7579","8084","8589","9094","9599","100UP"]

# ------------------------------------------------------------------
# 1.  TikTok audience  → tidy
# ------------------------------------------------------------------
aud = pd.read_csv(RAW_FILE)
aud["est_users"] = (aud["lower_end"] + aud["upper_end"]) / 2
aud = aud[aud["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])]

# country key: prefer ISO code if present, else fallback to name
if "code" in aud.columns:
    aud["country_key"] = aud["code"]
else:
    aud["country_key"] = aud["name"]

aud = aud.rename(columns={"age_bucket": "bucket"})
aud["gender"] = aud["genders"].map({"GENDER_MALE": "male",
                                    "GENDER_FEMALE": "female"})

aud_tidy = (
    aud.groupby(["country_key","bucket","gender"], as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_key","bucket"], columns="gender",
               values="est_users")
        .reset_index()
        .rename(columns={"male":"tiktok_male","female":"tiktok_female"})
)

# ------------------------------------------------------------------
# 2.  Population  → tidy
# ------------------------------------------------------------------
pop = pd.read_csv(POP_FILE)
pop_long = (
    pop.set_index(["country_name","country_code"])
        .rename(columns=lambda c: c.replace("pop_",""))
        .stack().reset_index()
        .rename(columns={"level_2":"tmp", 0:"pop"})
)

pop_long[["sex","bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
pop_tidy = (
    pop_long.pivot_table(index=["country_name","bucket"], columns="sex",
                         values="pop", aggfunc="first")
            .reset_index()
            .rename(columns={"male":"pop_male","female":"pop_female"})
)

# harmonise key names for merge
pop_tidy = pop_tidy.rename(columns={"country_name":"country_key"})

# ------------------------------------------------------------------
# 3.  Merge  & compute penetration + gender gap
# ------------------------------------------------------------------
merged = (aud_tidy
          .merge(pop_tidy, on=["country_key","bucket"], how="left")
          .dropna(subset=["pop_male","pop_female"]))

merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
merged["gap_abs"] = merged["pen_male"] - merged["pen_female"]
merged["gap_pct"] = 100 * merged["gap_abs"] / (merged["pen_male"] + merged["pen_female"])

merged.to_csv(OUT_DIR / "penetration_by_country.csv", index=False)
print("✓ penetration_by_country.csv written")

# ------------------------------------------------------------------
# 4.  World totals per bucket
# ------------------------------------------------------------------
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
print("✓ penetration_by_bucket.csv written")

# ------------------------------------------------------------------
# 5.  Keep previous overall & by-country gender-gap tables
# ------------------------------------------------------------------
tot = (
    aud.groupby("gender")["est_users"].sum()
        .rename({"male":"total_male","female":"total_female"})
        .to_frame().T
)
tot["gap_abs"] = tot["total_male"] - tot["total_female"]
tot["gap_pct"] = 100 * tot["gap_abs"] / (tot["total_male"] + tot["total_female"])
tot.to_csv(OUT_DIR / "overall_gap.csv", index=False)

by_country = (
    aud.groupby(["country_key","gender"])["est_users"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"male":"total_male","female":"total_female"})
        .reset_index()
)
by_country["gap_abs"] = by_country["total_male"] - by_country["total_female"]
by_country["gap_pct"] = 100 * by_country["gap_abs"] / (
    by_country["total_male"] + by_country["total_female"])
by_country.to_csv(OUT_DIR / "gap_by_country.csv", index=False)

print("✓ overall_gap.csv & gap_by_country.csv updated")

# ------------------------------------------------------------------
# 6.  Sanity check
# ------------------------------------------------------------------
print("\nTop 5 buckets by |gap_pct| (world totals)")
print(world.reindex(world["gap_pct"].abs().sort_values(ascending=False).index)
           .head(5)[["gap_pct"]])
