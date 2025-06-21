from pathlib import Path
import requests, io, zipfile, pandas as pd

YEAR = "2023"                                   # target year
OUT  = Path("reference/pop_by_country_buckets.csv")
OUT.parent.mkdir(exist_ok=True)

BUCKETS = [
    "1014","1519","2024","2529","3034","3539","4044","4549",
    "5054","5559","6064","6569","7074","7579","8084",
    "8589","9094","9599","100UP"
]

URL = "https://api.worldbank.org/v2/en/indicator/{}?downloadformat=csv"

def fetch(code: str):
    """Download one indicator; return DF(country_code, YEAR) or None."""
    r = requests.get(URL.format(code), timeout=60)
    if r.status_code != 200:
        print(f"⚠ {code} → HTTP {r.status_code}, skipped.")
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            csv_name = [n for n in z.namelist() if n.endswith("_Data.csv")][0]
            df = pd.read_csv(z.open(csv_name), skiprows=4, low_memory=False)
            return df[["Country Code", YEAR]]
    except Exception:
        print(f"⚠ {code} bad zip, skipped.")
        return None

def sum_cols(df, sex, parts):
    return df[[f"pop_{sex}_{p}" for p in parts]].sum(axis=1)

def main():
    merged = None
    for suf in BUCKETS:
        for sex, sx in [("male","MA"), ("female","FE")]:
            ind = f"SP.POP.{suf}.{sx}.IN"
            col = f"pop_{sex}_{suf}"
            d   = fetch(ind)
            if d is None:
                continue
            d = d.rename(columns={"Country Code":"country_code", YEAR:col})
            merged = d if merged is None else merged.merge(d,on="country_code",how="outer")

    for sex in ["male","female"]:
        merged[f"pop_{sex}_2534"] = sum_cols(merged, sex, ["2529","3034"])
        merged[f"pop_{sex}_3544"] = sum_cols(merged, sex, ["3539","4044"])
        merged[f"pop_{sex}_4554"] = sum_cols(merged, sex, ["4549","5054"])
        high = [b for b in BUCKETS if (b!="100UP" and int(b[:2])>=55) or b=="100UP"]
        merged[f"pop_{sex}_55plus"] = sum_cols(merged, sex, high)

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
    merged[keep].to_csv(OUT, index=False)
    print(f"✓ {OUT} created")

if __name__ == "__main__":
    main()
