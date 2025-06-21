from pathlib import Path
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────
IN_CSV  = Path("reference/worldbank_population_by_age.csv")
OUT_CSV = Path("reference/pop_by_country_buckets.csv")
OUT_CSV.parent.mkdir(exist_ok=True)

# ── TikTok-matching buckets we want ────────────────────────────────
ATOMIC = ["1014", "1519", "2024"]           # keep as-is
COMBO  = {                                  # new bucket : parts
    "2534": ["2529", "3034"],
    "3544": ["3539", "4044"],
    "4554": ["4549", "5054"],
}
PLUS_SUFFIXES = ["5559","6064","6569","7074","7579",
                 "8084","8589","9094","9599","100UP"]

def main():
    # 1) read full CSV (header line is row 0)
    df = pd.read_csv(IN_CSV, low_memory=False)

    # 2) find the latest numeric year column (e.g. '2024 [YR2024]')
    year_cols = [c for c in df.columns if c.startswith("20")]
    YEAR_COL  = next(col for col in reversed(year_cols)
                     if pd.to_numeric(df[col].str.replace(",",""), errors="coerce").notna().any())
    print(f"Using year column: {YEAR_COL}")

    # 3) keep only raw head-count series & only bucket codes we need
    df = df[df["Series Code"].str.endswith(".IN", na=False)]

    # 4) pivot so each Series Code becomes a column
    pivot = df.pivot_table(
        index=["Country Code","Country Name"],
        columns="Series Code",
        values=YEAR_COL,
        aggfunc="first"
    ).fillna(0)

    # 5) remove thousands separators & convert to numeric
    pivot = pivot.replace({",":""}, regex=True).apply(pd.to_numeric, errors="coerce").fillna(0)

    out = pivot.reset_index().rename(columns={
        "Country Code":"country_code",
        "Country Name":"country_name"
    })

    G = lambda code: out[code] if code in out.columns else 0

    # 6) atomic 5-year buckets
    for b in ATOMIC:
        out[f"pop_male_{b}"]   = G(f"SP.POP.{b}.MA.IN")
        out[f"pop_female_{b}"] = G(f"SP.POP.{b}.FE.IN")

    # 7) combined 10-year buckets
    for new, parts in COMBO.items():
        out[f"pop_male_{new}"]   = sum(G(f"SP.POP.{p}.MA.IN") for p in parts)
        out[f"pop_female_{new}"] = sum(G(f"SP.POP.{p}.FE.IN") for p in parts)

    # 8) 55-plus
    out["pop_male_55plus"]   = sum(G(f"SP.POP.{s}.MA.IN") for s in PLUS_SUFFIXES)
    out["pop_female_55plus"] = sum(G(f"SP.POP.{s}.FE.IN") for s in PLUS_SUFFIXES)

    # 9) save
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
    print(f"✓ {OUT_CSV} written with {len(out)} countries")

if __name__ == "__main__":
    main()
