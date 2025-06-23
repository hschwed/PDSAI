# uses [output.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]

# Issue: Maps every TT entry from output file to country (even cities/regions)
# possibly fixed now


from pathlib import Path
import pandas as pd
import re

# 1) files & paths
RAW = Path("output.csv")             # your TikTok dump
OUT = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# 2) load raw TikTok output
df = pd.read_csv(RAW)

# 3) keep only 2-letter uppercase country codes
#    (drops any city/region entries)
df = df[df["name"].astype(str).str.match(r'^[A-Z]{2}$', na=False)]

# 4) keep only female & male segments (drop unlimited)
df = df[df["genders"].isin(["GENDER_FEMALE", "GENDER_MALE"]) ]

# 5) drop any global-stage summaries
#    (TikTok stage4 often returns world/global figures leaked into every country)
df = df[df["user_count_stage"] != 4]

# 6) normalize gender → sex
#    transforms GENDER_MALE → male, GENDER_FEMALE → female
df["sex"] = df["genders"].str.replace("GENDER_", "", regex=False).str.lower()

# 7) aggregate to one bound per country×age×sex
#    taking the maximum lower & upper ends to cover all ad-objective segments
grp = (
    df
      .groupby(["name", "ages_ranges", "sex"], as_index=False)
      .agg({"lower_end": "max", "upper_end": "max"})
)
# 8) compute midpoint estimate
grp["est_users"] = (grp["lower_end"] + grp["upper_end"]) / 2

# 9) rename & reorder columns
df_clean = (
    grp
      .rename(columns={
          "name": "country_code",
          "ages_ranges": "age_bucket"
      })
      [["country_code", "age_bucket", "sex", "lower_end", "upper_end", "est_users"]]
)

# 10) write out
df_clean.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df_clean):,} rows")

