# Input: [reference/13-24.csv]
# Output: [reference/13_17_18_24.csv]
# More detailed age buckets with exact bucket match for TT data



import re
from pathlib import Path
import pandas as pd

def parse_series_name(s):
    """
    Extract age and gender from a Series Name like 'Age population, age 15, male'.
    Returns (age:int, gender:str) or (None, None) if no match.
    """
    if not isinstance(s, str):
        return None, None
    m = re.search(r'age\s*(\d+),\s*(male|female)', s, flags=re.IGNORECASE)
    if not m:
        return None, None
    age = int(m.group(1))
    gender = m.group(2).lower()
    return age, gender


def bucket_name(age, gender):
    """
    Assign to 13-17 or 18-24 bucket based on age and gender.
    """
    if 13 <= age <= 17:
        return f"{gender}1317"
    elif 18 <= age <= 24:
        return f"{gender}1824"
    return None


def main():
    IN_CSV  = Path("reference/13-24.csv")
    OUT_CSV = Path("reference/13_17_18_24.csv")
    OUT_CSV.parent.mkdir(exist_ok=True)

    # 1️⃣ Load the CSV
    df = pd.read_csv(IN_CSV)

    # 2️⃣ Identify year columns (starting with four digits)
    year_cols = [c for c in df.columns if re.match(r'^\d{4}', c)]
    if not year_cols:
        raise RuntimeError("No year columns found")

    # 3️⃣ Melt into long format
    df_long = (
        df
        .melt(
            id_vars=["Country Name", "Country Code", "Series Name"],
            value_vars=year_cols,
            var_name="year_col",
            value_name="pop"
        )
    )

    # 4️⃣ Extract numeric year
    df_long['year'] = df_long['year_col'].str.extract(r'^(\d{4})').astype(int)
    df_long.drop(columns=['year_col'], inplace=True)

    # 5️⃣ Parse age and gender
    parsed = df_long['Series Name'].apply(lambda s: pd.Series(parse_series_name(s), index=['age','gender']))
    df_long = pd.concat([df_long, parsed], axis=1)

    # 6️⃣ Filter to ages 13-24 and assign buckets
    df_long = df_long.dropna(subset=['age','gender'])
    df_long['age'] = df_long['age'].astype(int)
    df_long['bucket'] = df_long.apply(
        lambda row: bucket_name(row['age'], row['gender']), axis=1
    )
    df_long = df_long.dropna(subset=['bucket'])

    # 7️⃣ Convert population to numeric
    df_long['pop'] = pd.to_numeric(df_long['pop'], errors='coerce').fillna(0)

    # 8️⃣ Group and sum by country, year, and bucket
    df_grouped = (
        df_long
        .groupby(["Country Code","Country Name","year","bucket"], as_index=False)
        ['pop']
        .sum()
    )

    # 9️⃣ Pivot to wide
    df_out = (
        df_grouped
        .pivot_table(
            index=["Country Code","Country Name","year"],
            columns="bucket",
            values="pop",
            fill_value=0
        )
        .reset_index()
    )

    # 🔟 Ensure desired column order
    cols = [
        "Country Code","Country Name","year",
        "female1317","female1824","male1317","male1824"
    ]
    # add missing columns if any
    for c in cols:
        if c not in df_out.columns:
            df_out[c] = 0
    df_out = df_out[cols]

    # 1️⃣1️⃣ Save
    df_out.to_csv(OUT_CSV, index=False)
    print(f"✓ Written {OUT_CSV} with {len(df_out)} rows")

if __name__ == "__main__":
    main()
