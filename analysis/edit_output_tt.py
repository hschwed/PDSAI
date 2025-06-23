# uses [output.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]

# Issue: Maps every TT entry from output file to country (even cities/regions)
# possibly fixed now



from pathlib import Path
import pandas as pd
import re

# 1) files & paths
RAW = Path("output.csv")                    # your TikTok dump
POP = Path("reference/pop_by_country_buckets.csv")
OUT = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# 2) load raw TikTok output
df = pd.read_csv(RAW)

# 3) helper to normalize names
def normal(x):
    return re.sub(r'[^a-z]', '', str(x).strip().lower())

# 4) build name→ISO lookup from your pop reference
pop = (
    pd.read_csv(POP, usecols=["country_name", "country_code"])
      .drop_duplicates()
)
name2iso = { normal(n): code for n, code in pop.values }

# 5) map TikTok “name” → ISO, then drop the non-matches
df["country_code"] = df["name"].map(lambda x: name2iso.get(normal(x)))
df = df[df["country_code"].notna()]

# 6) compute midpoint estimate
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2

# 7) normalize genders→sex
#    expects strings like “GENDER_FEMALE” / “GENDER_MALE”
df["sex"] = (
    df["genders"]
      .str.replace("GENDER_", "", regex=False)
      .str.lower()
)

# 8) pick & rename the final columns
keep = [
    "name",         # original label from TikTok
    "country_code",
    "ages_ranges",
    "sex",
    "lower_end",
    "upper_end",
    "est_users"
]
df_clean = (
    df[keep]
      .rename(columns={
          "name": "country_name",
          "ages_ranges": "age_bucket"
      })
)

# 9) write out
df_clean.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df_clean):,} rows")

