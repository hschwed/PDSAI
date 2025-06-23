# uses [output.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]

# Issue: Maps every TT entry from output file to country (even cities/regions)
# possibly fixed now



from pathlib import Path
import pandas as pd
import re

# ------------------------------------------------------------------
RAW  = Path("output.csv")
POP  = Path("reference/pop_by_country_buckets.csv")  # for name→ISO fallback
OUT  = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# 1) load raw TikTok output
df = pd.read_csv(RAW)

# 2) normalization helper
def normal(x):
    return re.sub(r'[^a-z]', '', str(x).strip().lower())

# 3) load population reference for name→ISO mapping
pop = pd.read_csv(POP, usecols=["country_name", "country_code"]).drop_duplicates()

# 4) map each TikTok “name” to its ISO code
name2iso = {normal(n): c for n, c in pop.values}
df["country_code"] = df["name"].map(lambda x: name2iso.get(normal(x)))

# 4.1) drop anything that didn’t map to a valid country ISO
df = df[df["country_code"].notna()]

# 5) pick the slim column set and rename
keep = [
    "name",
    "country_code",
    "ages_ranges",
    "sex",
    "lower_end",
    "upper_end",
    "est_users"
]
df = df[keep].rename(columns={
    "name": "country_name",
    "ages_ranges": "age_bucket"
})

# 6) save cleaned CSV
df.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df):,} rows")
