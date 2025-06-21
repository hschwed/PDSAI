from pathlib import Path
import pandas as pd

# Input: the CSV you uploaded
IN_CSV = Path("reference/worldbank_population_by_age.csv")
# Output: the cleaned buckets file
OUT_CSV = Path("reference/pop_by_country_buckets.csv")
OUT_CSV.parent.mkdir(exist_ok=True)

# The 2024 numeric column in that CSV
YEAR_COL = "2024 [YR2024]"

def main():
    # 1. load & filter to absolute counts
    df = pd.read_csv(IN_CSV, skiprows=4, low_memory=False)
    df = df[df["Series Code"].str.endswith(".IN", na=False)]

    # 2. pivot so each Series Code becomes a column
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

    # 3. set up output DataFrame
    idx = pivot.index
    out = pd.DataFrame({
        "country_code": idx.get_level_values(0),
        "country_name": idx.get_level_values(1),
    })

    # helper to safely grab a column (or return zeros)
    def get_val(code):
        return pivot[code] if code in pivot.columns else 0

    # 4. atomic buckets: 10-14,15-19,20-24
    for b in ("1014","1519","2024"):
        out[f"pop_male_{b}"]   = get_val(f"SP.POP.{b}.MA.IN")
        out[f"pop_female_{b}"] = get_val(f"SP.POP.{b}.FE.IN")

    # 5. combined buckets
    out["pop_male_2534"]   = get_val("SP.POP.2529.MA.IN") + get_val("SP.POP.3034.MA.IN")
    out["pop_female_2534"] = get_val("SP.POP.2529.FE.IN") + get_val("SP.POP.3034.FE.IN")

    out["pop_male_3544"]   = get_val("SP.POP.3539.MA.IN") + get_val("SP.POP.4044.MA.IN")
    out["pop_female_3544"] = get_val("SP.POP.3539.FE.IN") + get_val("SP.POP.4044.FE.IN")

    out["pop_male_4554"]   = get_val("SP.POP.4549.MA.IN") + get_val("SP.POP.5054.MA.IN")
    out["pop_female_4554"] = get_val("SP.POP.4549.FE.IN") + get_val("SP.POP.5054.FE.IN")

    # 55+ = all buckets from 55-59 up to 100+
    plus_codes_m = [f"SP.POP.{s}.MA.IN" for s in [
        "5559","6064","6569","7074","7579","8084",
        "8589","9094","9599","100UP"
    ]]
    plus_codes_f = [c.replace(".MA.IN",".FE.IN") for c in plus_codes_m]

    out["pop_male_55plus"]   = sum(get_val(c) for c in plus_codes_m)
    out["pop_female_55plus"] = sum(get_val(c) for c in plus_codes_f)

    # 6. write the result
    out.to_csv(OUT_CSV, index=False)
    print(f"✓ {OUT_CSV} created with {len(out)} countries")

if __name__ == "__main__":
    main()
