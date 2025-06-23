# uses [output.csv]
# cleans & normalizes TikTok data and maps country codes ISO
# Outputs: [tt_clean.csv]



from pathlib import Path
import pandas as pd
import re

# ------------------------------------------------------------------
RAW  = Path("output.csv")
POP  = Path("reference/pop_by_country_buckets.csv")          # for name→ISO fallback
OUT  = Path("outputs/tt_clean.csv")
OUT.parent.mkdir(exist_ok=True)

# quick utils ------------------------------------------------------
def normal(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())

# ------------------------------------------------------------------
# 1) load TikTok export
df = pd.read_csv(RAW, thousands=",")

# 2) basic cleaning / keep only rows we care about
df = df[df["genders"].isin(["GENDER_MALE", "GENDER_FEMALE"])].copy()
df["est_users"] = (df["lower_end"] + df["upper_end"]) / 2
df["sex"] = df["genders"].map({"GENDER_MALE": "male",
                               "GENDER_FEMALE": "female"})

# 3) make sure we have an ISO-3 code
if "code" in df.columns:
    df["country_code"] = df["code"]
else:
    pop = pd.read_csv(POP)[["country_code", "country_name"]]
    name2iso = {normal(n): c for n, c in pop.values}
    df["country_code"] = df["name"].map(lambda x: name2iso.get(normal(x)))

# 4) pick the slim column set
keep = ["name", "country_code", "ages_ranges",
        "sex", "lower_end", "upper_end", "est_users"]
df = df[keep].rename(columns={
    "name": "country_name",
    "ages_ranges": "age_bucket"
})

# 5) save
df.to_csv(OUT, index=False)
print(f"✓ {OUT} written with {len(df):,} rows")
