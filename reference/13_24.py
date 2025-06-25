# Input: [reference/13-24.csv]
# Output: [reference/13_17_18_24.csv]
# More detailed age buckets with exact bucket match for TT data


import pandas as pd


def main():
    # Load the raw per-age TikTok counts
    df = pd.read_csv('reference/13-24.csv')

    # Ensure age is numeric
    df['age'] = pd.to_numeric(df['age'], errors='coerce')

    # Define buckets
    mask_13_17 = df['age'].between(13, 17)
    mask_18_24 = df['age'].between(18, 24)

    # Aggregate sums by country
    female1317 = df.loc[mask_13_17].groupby('country_code')['tiktok_female'].sum()
    female1824 = df.loc[mask_18_24].groupby('country_code')['tiktok_female'].sum()
    male1317   = df.loc[mask_13_17].groupby('country_code')['tiktok_male'].sum()
    male1824   = df.loc[mask_18_24].groupby('country_code')['tiktok_male'].sum()

    # Combine into output DataFrame
    output = pd.DataFrame({
        'country_code': female1317.index,
        'female1317': female1317.values,
        'female1824': female1824.reindex(female1317.index).values,
        'male1317':   male1317.values,
        'male1824':   male1824.reindex(male1317.index).values,
    })

    # Write the aggregated buckets to CSV
    output.to_csv('reference/13_17_18_24.csv', index=False)


if __name__ == '__main__':
    main()
