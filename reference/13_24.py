# Input: [reference/13-24.csv]
# Output: [reference/13_17_18_24.csv]
# More detailed age buckets with exact bucket match for TT data

import pandas as pd


def main():
    # Read the source CSV
    df = pd.read_csv('reference/13-24.csv')

    # Extract age from the "indicator name" column (e.g., "Age population, age 15, male")
    # Assumes there is a column named 'indicator name' or similar; adjust if different
    if 'indicator name' in df.columns:
        ind_col = 'indicator name'
    elif 'indicator_name' in df.columns:
        ind_col = 'indicator_name'
    else:
        raise KeyError("No 'indicator name' column found")

    # Pull out the numeric age
    df['age'] = df[ind_col].str.extract(r'age\s*(\d+)', expand=False).astype(int)
    # Determine gender
    df['gender'] = df[ind_col].str.contains('female', case=False).map({True: 'female', False: 'male'})

    # Identify the population value column (assuming it's the last one)
    value_col = df.columns[-1]

    # Define age buckets
    buckets = {
        '1317': (13, 17),
        '1824': (18, 24)
    }

    # Prepare aggregation
    results = []
    for country in df['country_code'].unique():
        sub = df[df['country_code'] == country]
        row = {'country_code': country}
        for gender in ['female', 'male']:
            for suffix, (low, high) in buckets.items():
                mask = (sub['gender'] == gender) & sub['age'].between(low, high)
                total = sub.loc[mask, value_col].sum()
                row[f'{gender}{suffix}'] = total
        results.append(row)

    # Convert to DataFrame and save
    out_df = pd.DataFrame(results)
    out_df.to_csv('reference/13_17_18_24.csv', index=False)


if __name__ == '__main__':
    main()
