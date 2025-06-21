from pathlib import Path
import pandas as pd

YEAR = "2024"
RAW  = Path("API_SP.POP.TOTL_DS2_en_csv_v2_81108.csv")  # total pop CSV you just committed
OUT  = Path("reference/pop_by_country_buckets.csv")
OUT.parent.mkdir(exist_ok=True)

def load_total_pop():
    df = pd.read_csv(RAW, skiprows=4, low_memory=False)
    return df[["Country Code", YEAR]].rename(columns={
        "Country Code": "country_code", YEAR: "pop_total"
    })

def main():
    pop = load_total_pop()
    pop.to_csv(OUT, index=False)
    print(f"✓ {OUT} written ({len(pop)} countries)")

if __name__ == "__main__":
    main()
