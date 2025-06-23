# uses [output.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]

# Issue: Maps every TT entry from output file to country (even cities/regions)
# possibly fixed now



from pathlib import Path
import pandas as pd

# 1) files & paths
RAW = Path("output.csv")             # your TikTok dump
OUT = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# 2) load raw TikTok output
df = pd.read_csv(RAW)

# 3) keep only 2-letter uppercase country codes
#    (drops any city/region entries)
df = df[df["name"].str.match(r'^[A-Z]{2}$', na=False)]

# 4) compute midpoint estimate
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2

# 5) normalize gender → sex
df["sex"] = df["genders"].str.replace("GENDER_", "", regex=False).str.lower()

# 6) select & rename
df_clean = (
    df[["name", "ages_ranges", "sex", "lower_end", "upper_end", "est_users"]]
      .rename(columns={
         "name": "country_code",
         "ages_ranges": "age_bucket"
      })
)

# 7) write out
df_clean.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df_clean):,} rows")


