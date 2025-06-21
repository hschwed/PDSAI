"""
build_population_buckets.py
-----------------------------------------------
Creates reference/pop_by_country_buckets.csv with:

 10-14 , 15-19 , 20-24               (kept as-is)
 25-34 = 25-29 + 30-34
 35-44 = 35-39 + 40-44
 45-54 = 45-49 + 50-54
 55+   = every bucket ≥55-59

Run once from repo root:
    python scripts/build_population_buckets.py
"""
from pathlib import Path
import requests, pandas as pd

YEAR   = 2024
OUT    = Path("reference/pop_by_country_buckets.csv")
OUT.parent.mkdir(exist_ok=True)

# 5-yr suffixes World Bank uses
BUCKETS = [
    "1014", "1519", "2024", "2529", "3034", "3539", "4044",
    "4549", "5054", "5559", "6064", "6569", "7074", "7579",
    "8084", "8589", "9094", "9599", "100UP"
]

def fetch_series(code: str) -> pd.Series:
    """Return pd.Series indexed by ISO code for a single indicator & YEAR."""
    url = f"https://api.worldbank.org/v2/country/all/indicator/{code}"
    r   = requests.get(url, params={"format": "json", "per_page": 20000})
    data = r.json()
    if len(data) != 2:                               # no data
        return pd.Series(dtype=float)
    rows = [ (rec["country"]["id"], rec["value"])
             for rec in data[1] if rec["date"] == str(YEAR) ]
    return pd.Series(dict(rows))

def main():
    store = {}
    for suf in BUCKETS:
        for sex, sx in [("male", "MA"), ("female", "FE")]:
            ind = f"SP.POP.{suf}.{sx}.IN"
            ser = fetch_series(ind)
            if ser.empty:
                print(f"⚠ {ind} empty")
                continue
            store[f"pop_{sex}_{suf}"] = ser

    df = pd.DataFrame(store).fillna(0).reset_index().rename(columns={"index":"country_code"})

    def bucket(sex, parts):
        return df[[f"pop_{sex}_{p}" for p in parts]].sum(axis=1)

    for s in ["male","female"]:
        df[f"pop_{s}_2534"]   = bucket(s, ["2529","3034"])
        df[f"pop_{s}_3544"]   = bucket(s, ["3539","4044"])
        df[f"pop_{s}_4554"]   = bucket(s, ["4549","5054"])
        high = [p for p in BUCKETS if p=="100UP" or int(p[:2])>=55]
        df[f"pop_{s}_55plus"] = bucket(s, high)

    keep = [
        "country_code",
        "pop_male_1014","pop_female_1014",
        "pop_male_1519","pop_female_1519",
        "pop_male_2024","pop_female_2024",
        "pop_male_2534","pop_female_2534",
        "pop_male_3544","pop_female_3544",
        "pop_male_4554","pop_female_4554",
        "pop_male_55plus","pop_female_55plus"
    ]
    df[keep].to_csv(OUT, index=False)
    print(f"✓ {OUT} written ({len(df)} countries)")

if __name__ == "__main__":
    main()
