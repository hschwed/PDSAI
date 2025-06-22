#cleans pop_bucket file, in order to get clear col names
# analysis/clean_pop_buckets.py
# ---------------------------------------------------------------
# Strip the "pop_" prefix from bucket columns so they read e.g.
#   male_1014 , female_1014 , male_2024 , …
# ---------------------------------------------------------------
from pathlib import Path
import pandas as pd

IN_CSV  = Path("reference/pop_by_country_buckets.csv")
OUT_CSV = Path("reference/pop_by_country_buckets_stripped.csv")
OUT_CSV.parent.mkdir(exist_ok=True)

def main() -> None:
    df = pd.read_csv(IN_CSV)

    # rename every column that starts with "pop_"
    new_cols = {c: c.replace("pop_", "", 1) for c in df.columns
                if c.startswith("pop_")}
    df = df.rename(columns=new_cols)

    df.to_csv(OUT_CSV, index=False)
    print(f"✓ {OUT_CSV} written with {len(df.columns)-2} bucket columns")

if __name__ == "__main__":
    main()

