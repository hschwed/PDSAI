# Input: [reference/13_17_18_24.csv]
# Input: [reference/pop_by_country_buckets_stripped.csv]
# Output: [final_WB_buckets.csv]

"""
reference/Final_buckets.py

This script reads the stripped population buckets and the new 13–17/18–24 buckets,
drops the old 10–14, 15–19, and 20–24 columns, and writes a combined output CSV.
"""
import os
import pandas as pd

def main():
    # Define input and output file paths
    input_stripped = os.path.join(os.path.dirname(__file__), '..', 'pop_by_country_buckets_stripped.csv')
    input_new_buckets = os.path.join(os.path.dirname(__file__), '..', '13_17_18_24.csv')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'data/final_WB_buckets.csv')

    # Read the existing stripped buckets
    df_stripped = pd.read_csv(reference/pop_by_country_buckets_stripped.csv)

    # Read the new 13–17 and 18–24 buckets
    df_new = pd.read_csv(reference/13_17_18_24.csv)

    # Rename the new bucket columns to match snake_case style
    rename_map = {
        'male1317':   'male_1317',
        'female1317': 'female_1317',
        'male1824':   'male_1824',
        'female1824': 'female_1824'
    }
    df_new = df_new.rename(columns=rename_map)

    # Drop the old 10–14, 15–19, and 20–24 bucket columns
    cols_to_drop = [
        'male_1014', 'female_1014',
        'male_1519', 'female_1519',
        'male_2024', 'female_2024'
    ]
    df_clean = df_stripped.drop(columns=cols_to_drop, errors='ignore')

    # Combine by index (assuming both files align row-wise)
    # If there's a country or key column to join on, replace this with a merge on that key
    new_cols = list(rename_map.values())
    df_final = pd.concat([df_clean, df_new[new_cols]], axis=1)

    # Write out the final buckets
    df_final.to_csv(output_file, index=False)
    print(f"Wrote final buckets to {output_file}")

if __name__ == '__main__':
    main()
