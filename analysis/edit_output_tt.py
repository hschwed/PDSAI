# uses [output.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]

# Issue: Maps every TT entry from output file to country (even cities/regions)
# possibly fixed now



from pathlib import Path
import pandas as pd
import re

# ------------------------------------------------------------------
RAW            = Path("output.csv")
COUNTRIES_FILE = Path("countries.csv")                       # list of 57 countries
POP            = Path("reference/pop_by_country_buckets.csv")
OUT            = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# quick utils ------------------------------------------------------
def normal(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

# ------------------------------------------------------------------
# 1) load TikTok export (parse commas as thousands separators)
df = pd.read_csv(RAW, thousands=",")

# 2) keep only male/female and estimate audience; map sexes
df = df[df["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])].copy()
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2
df["sex"] = df["genders"].map({
    "GENDER_MALE": "male",
    "GENDER_FEMALE": "female"
})

# 3) ensure ISO-3 country codes
if "code" in df.columns:
    df["country_code"] = df["code"].astype(str).str.strip()
else:
    pop = pd.read_csv(POP)[["country_code", "country_name"]]
    lookup = {normal(n): c for n, c in pop.values}
    df["country_code"] = df["name"].map(lambda x: lookup.get(normal(x), ""))

# 4) fill any missing codes to avoid downstream drops
df["country_code"] = df["country_code"].replace("", "UNK")

# 5) filter to the 57 countries from countries.csv
countries = pd.read_csv(COUNTRIES_FILE)
valid_codes = countries.loc[
    countries["region_level"] == "COUNTRY", 
    "country_code"
].tolist()
df = df[df["country_code"].isin(valid_codes)].copy()

# 6) slim down columns & rename for consistency
keep = [
    "name", "country_code", "ages_ranges",
    "sex", "lower_end", "upper_end", "est_users"
]
df = df[keep].rename(columns={
    "name": "country_name",
    "ages_ranges": "age_bucket"
})

# 7) save cleaned output
df.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df):,} rows (filtered to {len(valid_codes)} countries)")

