from pathlib import Path
import requests, pandas as pd

YEAR = "2024"                                     # world-bank year column
OUT  = Path("reference/pop_by_country_buckets.csv")
OUT.parent.mkdir(exist_ok=True)

# 5-year suffixes World Bank uses
BUCKETS = [
    "1014","1519","2024","2529","3034","3539","4044",
    "4549","5054","5559","6064","6569","7074","7579",
    "8084","8589","9094","9599","100UP"
]
BASE = "https://api.worldbank.org/v2/country/all/indicator/{}"

def fetch(ind):
    """Return DataFrame(country_code, country_name, value) for one indicator."""
    r = requests.get(BASE.format(ind), params={"format":"json","per_page":20000}, timeout=30)
    data = r.json()
    if len(data) != 2:
        return pd.DataFrame()
    rows = [
        {"country_code": rec["country"]["id"],
         "country_name": rec["country"]["value"],
         ind:           rec["value"] or 0}
        for rec in data[1] if rec["date"] == YEAR
    ]
    return pd.DataFrame(rows)

def main():
    frames = []
    for suf in BUCKETS:
        for sex, sx in [("male","MA"), ("female","FE")]:
            ind = f"SP.POP.{suf}.{sx}.IN"
            df  = fetch(ind)
            if not df.empty:
                frames.append(df)

    if not frames:
        print("No data downloaded.")
        return

    pop = frames[0]
    for df in frames[1:]:
        pop = pop.merge(df, on=["country_code","country_name"], how="outer").fillna(0)

    # helper: safe get
    G = lambda code: pop[code] if code in pop.columns else 0

    # atomic buckets
    for b in ["1014","1519","2024"]:
        pop[f"pop_male_{b}"]   = G(f"SP.POP.{b}.MA.IN")
        pop[f"pop_female_{b}"] = G(f"SP.POP.{b}.FE.IN")

    # combined buckets
    pop["pop_male_2534"]   = G("SP.POP.2529.MA.IN") + G("SP.POP.3034.MA.IN")
    pop["pop_female_2534"] = G("SP.POP.2529.FE.IN") + G("SP.POP.3034.FE.IN")

    pop["pop_male_3544"]   = G("SP.POP.3539.MA.IN") + G("SP.POP.4044.MA.IN")
    pop["pop_female_3544"] = G("SP.POP.3539.FE.IN") + G("SP.POP.4044.FE.IN")

    pop["pop_male_4554"]   = G("SP.POP.4549.MA.IN") + G("SP.POP.5054.MA.IN")
    pop["pop_female_4554"] = G("SP.POP.4549.FE.IN") + G("SP.POP.5054.FE.IN")

    plus = [f"SP.POP.{s}.{sx}.IN" for s in BUCKETS if s=="100UP" or int(s[:2])>=55 for sx in ["MA","FE"]]
    pop["pop_male_55plus"]   = sum(G(c) for c in plus if ".MA." in c)
    pop["pop_female_55plus"] = sum(G(c) for c in plus if ".FE." in c)

    cols = [
        "country_code","country_name",
        "pop_male_1014","pop_female_1014",
        "pop_male_1519","pop_female_1519",
        "pop_male_2024","pop_female_2024",
        "pop_male_2534","pop_female_2534",
        "pop_male_3544","pop_female_3544",
        "pop_male_4554","pop_female_4554",
        "pop_male_55plus","pop_female_55plus"
    ]
    pop[cols].to_csv(OUT, index=False)
    print(f"✓ {OUT} written ({len(pop)} countries)")

if __name__ == "__main__":
    main()
