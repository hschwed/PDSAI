# Input: [reference/13-24.csv]
# Output: [reference/13_17_18_24.csv]
# More detailed age buckets with exact bucket match for TT data



import pandas as pd
import os

def main():
    # Read the source data (expects columns: country_code, age, tiktok_female, tiktok_male)
    df = pd.read_csv('reference.csv')

    # Melt female/male columns into a long format
    df_f = df[['country_code', 'age', 'tiktok_female']].rename(
        columns={'tiktok_female': 'tiktok_count'}
    ).assign(gender='female')

    df_m = df[['country_code', 'age', 'tiktok_male']].rename(
        columns={'tiktok_male': 'tiktok_count'}
    ).assign(gender='male')

    df_long = pd.concat([df_f, df_m], ignore_index=True)

    # Define age buckets
    ages_1317 = list(range(13, 18))        # 13–17
    ages_1824 = list(range(18, 25))        # 18–24

    # Filter to relevant ages
    df_long = df_long[df_long['age'].isin(ages_1317 + ages_1824)]

    # Assign bucket labels
    def label_bucket(age):
        if age in ages_1317:
            return '1317'
        elif age in ages_1824:
            return '1824'
        else:
            return None

    df_long['age_group'] = df_long['age'].apply(label_bucket)
    df_long = df_long.dropna(subset=['age_group'])

    # Aggregate counts by country, gender, and age_group
    agg = (
        df_long
        .groupby(['country_code', 'gender', 'age_group'])['tiktok_count']
        .sum()
        .reset_index()
    )

    # Pivot to wide format
    pivot = agg.pivot(
        index='country_code',
        columns=['gender', 'age_group'],
        values='tiktok_count'
    )

    # Flatten MultiIndex and rename columns
    pivot.columns = [f"{g}{ag}" for g, ag in pivot.columns]
    pivot = pivot.reset_index()

    # Ensure output directory exists
    out_dir = os.path.dirname('reference/13_17_18_24.csv')
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Write to CSV
    pivot.to_csv('reference/13_17_18_24.csv', index=False)
    print("Written reference/13_17_18_24.csv with buckets male1317, male1824, female1317, female1824.")

if __name__ == '__main__':
    main()
