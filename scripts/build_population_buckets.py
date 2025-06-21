from pathlib import Path
import pandas as pd

# 1) point at the file you just moved
IN_CSV  = Path("reference/worldbank_population_by_age.csv")
OUT_CSV = Path("reference/pop_by_country_buckets.csv")
OUT_CSV.parent.mkdir(exist_ok=True)

YEAR_COL = "2024 [YR2024]"

def main():
    # load, skipping the first 4 metadata rows
    df = pd.read_csv(IN_CSV, skiprows=4, low_memory=False)

    # keep only the total-count series (.IN)
    df = df[df["Series Code"].str.endswith(".IN", na=False)]

    # pivot so each Series Code is a column
    pivot = (
        df.pivot_table(
            index=["Country Code","Country Name"],
            columns="Series Code",
            values=YEAR_COL,
            aggfunc="first"
        )
        .fillna(0)
    )

    # build the output DataFrame
    out = pivot.reset_index().rename(columns={
        "Country Code":"country_code",
        "Country Name":"country_name"
    })

    # helper to get a series or zero if missing
    def G(code):
        return out[code] if code in out.columns else 0

    # atomic buckets
    for b in ("1014","1519","2024"):
        out[f"pop_male_{b}"]   = G(f"SP.POP.{b}.MA.IN")
        out[f"pop_female_{b}"] = G(f"SP.POP.{b}.FE.IN")

    # combined buckets
    out["pop_male_2534"]   = G("SP.POP.2529.MA.IN") + G("SP.POP.3034.MA.IN")
    out["pop_female_2534"] = G("SP.POP.2529.FE.IN") + G("SP.POP.3034.FE.IN")

    out["pop_male_3544"]   = G("SP.POP.3539.MA.IN") + G("SP.POP.4044.MA.IN")
    out["pop_female_3544"] = G("SP.POP.3539.FE.IN") + G("SP.POP.4044.FE.IN")

    out["pop_male_4554"]   = G("SP.POP.4549.MA.IN") + G("SP.POP.5054.MA.IN")
    out["pop_female_4554"] = G("SP.POP.4549.FE.IN") + G("SP.POP.5054.FE.IN")

    plus_m = [f"SP.POP.{s}.MA.IN" for s in
              ["5559","6064","6569","7074","7579","8084","8589","9094","9599","100UP"]]
    plus_f = [c.replace(".MA.IN",".FE.IN") for c in plus_m]

    out["pop_male_55plus"]   = sum(G(c) for c in plus_m)
    out["pop_female_55plus"] = sum(G(c) for c in plus_f)

    # write
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
    out[cols].to_csv(OUT_CSV, index=False)
    print(f"✓ {OUT_CSV} created with {len(out)} countries")

if __name__ == "__main__":
    main()
