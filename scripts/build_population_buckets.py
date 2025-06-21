from pathlib import Path
import pandas as pd

# — Input & output paths —
IN_CSV  = Path("reference/worldbank_population_by_age.csv")
OUT_CSV = Path("reference/pop_by_country_buckets.csv")
OUT_CSV.parent.mkdir(exist_ok=True)

# — Year column name as it appears in the CSV —
YEAR_COL = "2024 [YR2024]"

def main():
    # 1️⃣ Load full file (header at row 0)
    df = pd.read_csv(IN_CSV, low_memory=False)

    # 2️⃣ Keep only the raw count series (.MA or .FE)
    mask = df["Series Code"].str.endswith(".MA") | df["Series Code"].str.endswith(".FE")
    df = df[mask]

    # 3️⃣ Pivot so each Series Code becomes a column
    pivot = (
        df
        .pivot_table(
            index=["Country Code", "Country Name"],
            columns="Series Code",
            values=YEAR_COL,
            aggfunc="first"
        )
        .fillna(0)
    )

    # 4️⃣ Prepare base DataFrame with country_code + country_name
    out = pivot.reset_index().rename(columns={
        "Country Code": "country_code",
        "Country Name": "country_name"
    })

    # helper to safely get a column or zero
    def G(code):
        return out[code] if code in out.columns else 0

    # 5️⃣ Atomic buckets 10-14, 15-19, 20-24
    for b in ["1014", "1519", "2024"]:
        out[f"pop_male_{b}"]   = G(f"SP.POP.{b}.MA")
        out[f"pop_female_{b}"] = G(f"SP.POP.{b}.FE")

    # 6️⃣ Combined buckets
    out["pop_male_2534"]   = G("SP.POP.2529.MA") + G("SP.POP.3034.MA")
    out["pop_female_2534"] = G("SP.POP.2529.FE") + G("SP.POP.3034.FE")

    out["pop_male_3544"]   = G("SP.POP.3539.MA") + G("SP.POP.4044.MA")
    out["pop_female_3544"] = G("SP.POP.3539.FE") + G("SP.POP.4044.FE")

    out["pop_male_4554"]   = G("SP.POP.4549.MA") + G("SP.POP.5054.MA")
    out["pop_female_4554"] = G("SP.POP.4549.FE") + G("SP.POP.5054.FE")

    plus_suffixes = ["5559","6064","6569","7074","7579","8084","8589","9094","9599","100UP"]
    out["pop_male_55plus"]   = sum(G(f"SP.POP.{s}.MA") for s in plus_suffixes)
    out["pop_female_55plus"] = sum(G(f"SP.POP.{s}.FE") for s in plus_suffixes)

    # 7️⃣ Write the final buckets file
    cols = [
        "country_code", "country_name",
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
