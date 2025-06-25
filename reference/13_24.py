# Input: [reference/13-24.csv]
# Output: [reference/13_17_18_24.csv]
# More detailed age buckets with exact bucket match for TT data



import re
import pandas as pd

def parse_age_gender(text):
    # ensure we have a string
    text = str(text)
    # look for age and gender in the series name
    # e.g. "Age population, age 15, male"
    m = re.search(r'age\s*(\d+),\s*(male|female)', text, flags=re.IGNORECASE)
    if not m:
        return pd.Series({'age': None, 'gender': None})
    age = int(m.group(1))
    gender = m.group(2).lower()
    return pd.Series({'age': age, 'gender': gender})

def bucket_label(age, gender):
    if age is None or gender not in ('male', 'female'):
        return None
    # define buckets
    if 13 <= age <= 17:
        return f"{gender}1317"
    elif 18 <= age <= 24:
        return f"{gender}1824"
    else:
        return None

def main():
    # read the input file
    df = pd.read_csv('reference/13-24.csv')

    # parse age and gender
    parsed = df['Series Name'].apply(parse_age_gender)
    df = pd.concat([df, parsed], axis=1)

    # assign bucket labels
    df['bucket'] = df.apply(lambda row: bucket_label(row['age'], row['gender']), axis=1)

    # filter only the relevant buckets
    df = df[df['bucket'].notna()]

    # select years columns
    years = ['2021 [YR2021]', '2022 [YR2022]', '2023 [YR2023]', '2024 [YR2024]', '2025 [YR2025]']

    # melt data for aggregation
    df_melt = df.melt(
        id_vars=['Country Code', 'bucket'],
        value_vars=years,
        var_name='year',
        value_name='population'
    )

    # aggregate by country, bucket, and year
    df_out = df_melt.groupby(['Country Code', 'bucket', 'year'], as_index=False)['population'].sum()

    # pivot so buckets become columns
    df_pivot = df_out.pivot_table(
        index=['Country Code', 'year'],
        columns='bucket',
        values='population'
    ).reset_index()

    # write to CSV
    df_pivot.to_csv('reference/13_17_18_24.csv', index=False)

if __name__ == '__main__':
    main()
