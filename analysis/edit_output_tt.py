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
POP  = Path("reference/pop_by_country_buckets.csv")  # for ISO lookup
OUT  = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# quick utils ------------------------------------------------------
def normal(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

# ------------------------------------------------------------------
# 1) load TikTok export (parse commas as thousands separators)
df = pd.read_csv(RAW, thousands=",")

# 2) keep only male/female, estimate audience & map sex
df = df[df["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])].copy()
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2
df["sex"] = df["genders"].map({
    "GENDER_MALE": "male",
    "GENDER_FEMALE": "female"
})

# 3) build or preserve ISO-3 country codes
if "code" in df.columns:
    df["country_code"] = df["code"].astype(str).str.strip()
else:
    pop = pd.read_csv(POP)[["country_code", "country_name"]]
    lookup = {normal(n): c for n, c in pop.values}
    df["country_code"] = df["name"].map(lambda x: lookup.get(normal(x), ""))

# 4) fill any missing country codes so downstream merges don’t drop rows
df["country_code"] = df["country_code"].replace("", "UNK")

# 5) slim down columns & rename
keep = ["name", "country_code", "ages_ranges",
        "sex", "lower_end", "upper_end", "est_users"]
df = df[keep].rename(columns={
    "name": "country_name",
    "ages_ranges": "age_bucket"
})

# 6) save
df.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df):,} rows")
