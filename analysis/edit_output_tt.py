# uses [output.csv]
# uses [countries.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]

# Issue: Maps every TT entry from output file to country (even cities/regions)
# possibly fixed now


from pathlib import Path
import pandas as pd
import re
import pycountry

# ───────────────────────── file paths ───────────────────────────
RAW            = Path("output.csv")
COUNTRIES_FILE = Path("countries.csv")
POP            = Path("reference/pop_by_country_buckets.csv")
OUT            = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# ────────────────────────── quick utils ──────────────────────────
def normal(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

# -------------------------------------------------------------------
# 1) Load raw TikTok export (parse commas as thousands separators)
# -------------------------------------------------------------------
df = pd.read_csv(RAW, thousands=",")

# -------------------------------------------------------------------
# 2) Slim columns & rename for consistency
# -------------------------------------------------------------------
keep = [
    "name", "ages_ranges",
    "genders", "lower_end", "upper_end"
]
df = df[keep].rename(columns={
    "name": "country_iso2",
    "ages_ranges": "age_bucket"
})

# -------------------------------------------------------------------
# 3) Keep only male/female, estimate audience & map sex
# -------------------------------------------------------------------
df = df[df["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])].copy()
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2
df["sex"] = df["genders"].map({
    "GENDER_MALE": "male",
    "GENDER_FEMALE": "female"
})

# -------------------------------------------------------------------
# 4) Map to ISO-3 country codes
# -------------------------------------------------------------------
def iso2_to_iso3(iso2):
    try:
        return pycountry.countries.get(alpha_2=iso2.upper()).alpha_3
    except:
        return "UNK"
    
df["country_code"] = df["country_iso2"].map(iso2_to_iso3)
#print(df.head())

# -------------------------------------------------------------------
# 5) Map age buckets
# -------------------------------------------------------------------
RANGE_MAP = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}

df["age_bucket"] = df["age_bucket"].str.replace('-', '_')
df["bucket"] = df["age_bucket"].map(RANGE_MAP)
if df["bucket"].isna().any():
    raise ValueError(f"Unknown age_bucket labels: {df['age_bucket'][df['bucket'].isna()].unique()}")

# -------------------------------------------------------------------
# 6) wide format, columns female and male
# -------------------------------------------------------------------
df = df.pivot_table(
    index=["country_code", "bucket"],
    columns="sex",
    values="est_users",
    aggfunc="first"  # or 'sum' if you may have duplicates
).reset_index()

# Rename columns
df.columns.name = None  # remove the pivot column name
df = df.rename(columns={
    "male": "tiktok_male",
    "female": "tiktok_female"
})

# -------------------------------------------------------------------
# 6) Save cleaned & filtered output
# -------------------------------------------------------------------
keep = [
    "country_code", "bucket","tiktok_male","tiktok_female"
]
df = df[keep]

df.to_csv(OUT, index=False)
#print(df.head())
print(f"✓ {OUT} written with {len(df):,}")
