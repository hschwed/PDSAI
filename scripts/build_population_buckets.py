from pathlib import Path
import pandas as pd

# — Input & output paths —
IN_CSV  = Path("reference/worldbank_population_by_age.csv")
OUT_CSV = Path("reference/pop_by_country_buckets.csv")
OUT_CSV.parent.mkdir(exist_ok=True)

# — Year column name as it appears in the CSV —
YEAR_COL = "2024 [YR2024]"

def main():
    # 1️⃣ Load full file
    df = pd.read_csv(IN_CSV, low_memory=False)

    # ──── DIAGNOSTIC ────
    year_cols = [c for c in df.columns if c.startswith("20")]
    print("\nDEBUG - first 15 year columns ➜", year_cols[:15])
    print("DEBUG - sample rows:")
    print(
        df.loc[:3, ["Country Code", "Series Code"] + year_cols[:5]]
        .to_string(index=False)
    )
    print("──────── end diagnostic ────────\n")
# ─────────────────────
    

    # 2️⃣ Filter to population series (.MA.IN & .FE.IN)
    mask = df["Series Code"].str.endswith(".MA.IN") | df["Series Code"].str.endswith(".FE.IN")
    df = df[mask]

    # 3️⃣ Pivot so each Series Code is a column
    pivot = df.pivot_table(
        index=["Country Code", "Country Name"],
        columns="Series Code",
        values=YEAR_COL,
        aggfunc="first"
    ).fillna(0)

    # 4️⃣ Ensure all pivot values are numeric
    pivot = pivot.apply(pd.to_numeric, errors="coerce").fillna(0)

    # 5️⃣ Prepare base DataFrame with country_code & country_name
    out = pivot.reset_index().rename(columns={
        "Country Code": "country_code",
        "Country Name": "country_name"
    })

    # helper to safely get a column or zero
    def G(code):
        return out[code] if code in out.columns else 0

    # 6️⃣ Atomic buckets 10-14, 15-19, 20-24
    for b in ["1014", "1519", "2024"]:
        out[f"pop_male_{b}"]   = G(f"SP.POP.{b}.MA.IN")
        out[f"pop_female_{b}"] = G(f"SP.POP.{b}.FE.IN")

    # 7️⃣ Combined buckets
    out["pop_male_2534"]   = G("SP.POP.2529.MA.IN") + G("SP.POP.3034.MA.IN")
    out["pop_female_2534"] = G("SP.POP.2529.FE.IN") + G("SP.POP.3034.FE.IN")

    out["pop_male_3544"]   = G("SP.POP.3539.MA.IN") + G("SP.POP.4044.MA.IN")
    out["pop_female_3544"] = G("SP.POP.3539.FE.IN") + G("SP.POP.4044.FE.IN")

    out["pop_male_4554"]   = G("SP.POP.4549.MA.IN") + G("SP.POP.5054.MA.IN")
    out["pop_female_4554"] = G("SP.POP.4549.FE.IN") + G("SP.POP.5054.FE.IN")

    plus_codes = [
        "5559","6064","6569","7074","7579","8084",
        "8589","9094","9599","100UP"
    ]
    out["pop_male_55plus"]   = sum(G(f"SP.POP.{s}.MA.IN") for s in plus_codes)
    out["pop_female_55plus"] = sum(G(f"SP.POP.{s}.FE.IN") for s in plus_codes)

    # 8️⃣ Write the final buckets file
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
