#World-Bank population counts
"""
build_population_buckets.py
-------------------------------------------------
Creates   reference/pop_by_country_buckets.csv   with
male & female population totals for these buckets:

 10-14, 15-19, 20-24            (kept as-is)
 25-34  = 25-29 + 30-34
 35-44  = 35-39 + 40-44
 45-54  = 45-49 + 50-54
 55-100 = all buckets ≥55-59 combined

Run once from the repo root:
    python scripts/build_population_buckets.py
"""

from pathlib import Path
import pandas as pd
import requests, io, zipfile

YEAR = "2024"                                   # align with TikTok snapshot
OUT  = Path("reference/pop_by_country_buckets.csv")
OUT.parent.mkdir(exist_ok=True)

BUCKETS = [
    "1014", "1519", "2024", "2529", "3034", "3539", "4044", "4549",
    "5054", "5559", "6064", "6569", "7074", "7579", "8084",
    "8589", "9094", "9599", "100UP"
]
URL = "https://api.worldbank.org/v2/en/indicator/{}?downloadformat=csv"

def fetch(code: str) -> pd.DataFrame | None:
    r = requests.get(URL.format(code), timeout=60)
    if r.status_code != 200:
        print(f"⚠ {code} not found, skipped.")
        return None
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        data = [n for n in z.namelist() if n.endswith("_Data.csv")][0]
        df = pd.read_csv(z.open(data), skiprows=4, low_memory=False)
        return df[["Country Code", YEAR]]

def sum_cols(df: pd.DataFrame, sex: str, parts: list[str]) -> pd.Series:
    return df[[f"pop_{sex}_{p}" for p in parts]].sum(axis=1)

def main():
    merged = None
    for suf in BUCKETS:
        for sex, sx in [("male", "MA"), ("female", "FE")]:
            ind = f"SP.POP.{suf}.{sx}.IN"
            col = f"pop_{sex}_{suf}"
            d   = fetch(ind)
            if d is None:
                continue
            d = d.rename(columns={"Country Code": "country_code", YEAR: col})
            merged = d if merged is None else merged.merge(d, on="country_code", how="outer")

    # custom buckets
    for sex in ["male", "female"]:
        merged[f"pop_{sex}_2534"] = sum_cols(merged, sex, ["2529", "3034"])
        merged[f"pop_{sex}_3544"] = sum_cols(merged, sex, ["3539", "4044"])
        merged[f"pop_{sex}_4554"] = sum_cols(merged, sex, ["4549", "5054"])
        high = [s for s in BUCKETS if int(s[:2]) >= 55 or s == "100UP"]
        merged[f"pop_{sex}_55plus"] = sum_cols(merged, sex, high)

    out_cols = [
        "country_code",
        "pop_male_1014", "pop_female_1014",
        "pop_male_1519", "pop_female_1519",
        "pop_male_2024", "pop_female_2024",
        "pop_male_2534", "pop_female_2534",
        "pop_male_3544", "pop_female_3544",
        "pop_male_4554", "pop_female_4554",
        "pop_male_55plus", "pop_female_55plus",
    ]
    merged[out_cols].dropna(subset=["pop_male_55plus"]).to_csv(OUT, index=False)
    print(f"✓ {OUT} created")

if __name__ == "__main__":
    main()
