# Input: [reference/13-24.csv]
# Output: [reference/13_17_18_24.csv]
# More detailed age buckets with exact bucket match for TT data



import re
import pandas as pd


def main():
    # load raw age data
    df = pd.read_csv('reference/13-24.csv')

    # ensure the key column exists
    if 'Series Name' not in df.columns:
        raise KeyError("No 'Series Name' column found")

    # extract age and gender from the series name
    def parse_age_gender(text):
        m = re.search(r'age\s*(\d+),\s*(male|female)', text, flags=re.IGNORECASE)
        if not m:
            return None, None
        return int(m.group(1)), m.group(2).lower()

    df[['age', 'gender']] = df['Series Name'] \
        .apply(lambda s: pd.Series(parse_age_gender(s)))

    # drop any rows we couldn't parse
    df = df.dropna(subset=['age', 'gender'])

    # assign buckets based on age and gender
    def make_bucket(row):
        age = row['age']
        gender = row['gender']
        if 13 <= age <= 17:
            return f"{gender}1317"
        elif 18 <= age <= 24:
            return f"{gender}1824"
        else:
            return None

    df['bucket'] = df.apply(make_bucket, axis=1)
    df = df.dropna(subset=['bucket'])

    # select the year columns (e.g. '2021 [YR2021]', etc.)
    year_cols = [c for c in df.columns if re.match(r"^\d{4} \[YR\d{4}\]$", c)]

    # aggregate sums by country code and bucket across years
    out = (
        df
        .groupby(['Country Code', 'bucket'])[year_cols]
        .sum()
        .reset_index()
    )

    # write out
    out.to_csv('reference/13_17_18_24.csv', index=False)


if __name__ == '__main__':
    main()
