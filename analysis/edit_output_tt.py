# uses [output.csv]
# uses [countries.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]

# Issue: Maps every TT entry from output file to country (even cities/regions)
# possibly fixed now


from pathlib import Path
import pandas as pd
import re

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
# 2) Keep only male/female, estimate audience & map sex
# -------------------------------------------------------------------
df = df[df["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])].copy()
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2
df["sex"] = df["genders"].map({
    "GENDER_MALE": "male",
    "GENDER_FEMALE": "female"
})

# -------------------------------------------------------------------
# 3) Map to ISO-3 country codes
# -------------------------------------------------------------------
if "code" in df.columns:
    df["country_code"] = df["code"].astype(str).str.strip()
else:
    pop = pd.read_csv(POP)[["country_code", "country_name"]]
    lookup = {normal(n): c for c, n in pop.values}
    df["country_code"] = df["name"].map(lambda x: lookup.get(normal(x), ""))
df["country_code"].replace("", "UNK", inplace=True)

# -------------------------------------------------------------------
# 4) Detect & filter by region_id
# -------------------------------------------------------------------
# Load the 57 valid region_ids
countries = pd.read_csv(COUNTRIES_FILE)
valid_ids = countries.loc[
    countries["region_level"] == "COUNTRY", "region_id"
].astype(int).tolist()

# Auto-detect your region-id column in the TikTok export
for candidate in ("region_id","regionId","region","region_code"):
    if candidate in df.columns:
        df["region_id"] = df[candidate].astype(int)
        break
else:
    raise KeyError(
        "No region‐ID column found in TikTok export. "
        f"Available columns: {list(df.columns)}"
    )

# Keep only rows whose region_id is in your 57-country list
df = df[df["region_id"].isin(valid_ids)].copy()

# -------------------------------------------------------------------
# 5) Slim columns & rename for consistency
# -------------------------------------------------------------------
keep = [
    "name", "country_code", "ages_ranges",
    "sex", "lower_end", "upper_end", "est_users"
]
df = df[keep].rename(columns={
    "name": "country_name",
    "ages_ranges": "age_bucket"
})

# -------------------------------------------------------------------
# 6) Save cleaned & filtered output
# -------------------------------------------------------------------
df.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df):,} rows (filtered to {len(valid_ids)} countries)")
