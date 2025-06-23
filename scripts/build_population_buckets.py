# bucketize WB [worldbank_population_by_age.csv  ] age-by-sex data by country & TikTok age groups
# ->Output: [pop_by_country_buckets.csv]

from pathlib import Path
import pandas as pd

# ── File locations ────────────────────────────────────────────────
IN_CSV  = Path("reference/worldbank_population_by_age.csv")   # raw file you uploaded
OUT_CSV = Path("reference/pop_by_country_buckets.csv")        # cleaned output
OUT_CSV.parent.mkdir(exist_ok=True)

# ── Age-bucket definitions (TikTok-matching) ──────────────────────
ATOMIC = ["1014", "1519", "2024"]                 # keep as-is
COMBO  = {                                        # new bucket → list of parts
    "2534": ["2529", "3034"],
    "3544": ["3539", "4044"],
    "4554": ["4549", "5054"],
}
PLUS_SUFFIXES = ["5559","6064","6569","7074","7579",
                 "8084","8589","9094","9599","100UP"]

def main():
    # 1️⃣ Load the full CSV (header row is row 0)
    df = pd.read_csv(IN_CSV, low_memory=False)

    # 2️⃣ Pick the newest year column that actually has numbers
    year_cols = [c for c in df.columns if c.startswith("20")]
    YEAR_COL  = next(
        col for col in reversed(year_cols)
        if pd.to_numeric(df[col].str.replace(",",""), errors="coerce").notna().any()
    )
    print(f"Using year column ➜ {YEAR_COL}")

    # 3️⃣ Keep only raw head-count series (ending with .MA or .FE)
    df = df[df["Series Code"].str.endswith(".MA") | df["Series Code"].str.endswith(".FE")]

    # 4️⃣ Pivot so each Series Code becomes one column
    pivot = (
        df.pivot_table(
            index=["Country Code","Country Name"],
            columns="Series Code",
            values=YEAR_COL,
            aggfunc="first"
        )
        .replace({",": ""}, regex=True)           # drop thousands separators
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

    out = pivot.reset_index().rename(columns={
        "Country Code": "country_code",
        "Country Name": "country_name"
    })

    # helper: return column or zeros if missing
    def G(code):
        return out[code] if code in out.columns else 0

    # 5️⃣ Atomic 5-year buckets
    for b in ATOMIC:
        out[f"pop_male_{b}"]   = G(f"SP.POP.{b}.MA")
        out[f"pop_female_{b}"] = G(f"SP.POP.{b}.FE")

    # 6️⃣ Combined 10-year buckets
    for new, parts in COMBO.items():
        out[f"pop_male_{new}"]   = sum(G(f"SP.POP.{p}.MA") for p in parts)
        out[f"pop_female_{new}"] = sum(G(f"SP.POP.{p}.FE") for p in parts)

    # 7️⃣ 55 plus (everything ≥55-59)
    out["pop_male_55plus"]   = sum(G(f"SP.POP.{s}.MA") for s in PLUS_SUFFIXES)
    out["pop_female_55plus"] = sum(G(f"SP.POP.{s}.FE") for s in PLUS_SUFFIXES)

    # 8️⃣ Save tidy table
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
