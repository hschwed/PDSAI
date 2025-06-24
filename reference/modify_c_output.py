# Input: [country_output.csv]
# modifies the file adding country names and so on

"""
reference/modify_c_output.py

Script to read country_output.csv, match geo_location to a mapping of region IDs,
and add columns for country_code, region_id, and region_name.
"""
import argparse
import pandas as pd

# Mapping data: each dict entry links a numeric region_id to its country_code and region_name
MAPPINGS = [
    {"country_code": "MA", "region_id": 2542007, "region_name": "Morocco"},
    {"country_code": "NL", "region_id": 2750405, "region_name": "Netherlands"},
    {"country_code": "SA", "region_id": 102358,  "region_name": "Saudi Arabia"},
    {"country_code": "DK", "region_id": 2623032, "region_name": "Denmark"},
    {"country_code": "UY", "region_id": 3439705, "region_name": "Uruguay"},
    {"country_code": "KE", "region_id": 192950,  "region_name": "Kenya"},
    {"country_code": "RO", "region_id": 798549,  "region_name": "Romania"},
    {"country_code": "AR", "region_id": 3865483, "region_name": "Argentina"},
    {"country_code": "AT", "region_id": 2782113, "region_name": "Austria"},
    {"country_code": "PA", "region_id": 3703430, "region_name": "Panama"},
    {"country_code": "GT", "region_id": 3595528, "region_name": "Guatemala"},
    {"country_code": "KR", "region_id": 1835841, "region_name": "South Korea"},
    {"country_code": "CZ", "region_id": 3077311, "region_name": "Czech Republic"},
    {"country_code": "KW", "region_id": 285570,  "region_name": "Kuwait"},
    {"country_code": "BE", "region_id": 2802361, "region_name": "Belgium"},
    {"country_code": "MX", "region_id": 3996063, "region_name": "Mexico"},
    {"country_code": "CR", "region_id": 3624060, "region_name": "Costa Rica"},
    {"country_code": "KZ", "region_id": 1522867, "region_name": "Kazakhstan"},
    {"country_code": "CA", "region_id": 6251999, "region_name": "Canada"},
    {"country_code": "FR", "region_id": 3017382, "region_name": "France"},
    {"country_code": "LK", "region_id": 1227603, "region_name": "Sri Lanka"},
    {"country_code": "IE", "region_id": 2963597, "region_name": "Ireland"},
    {"country_code": "OM", "region_id": 286963,  "region_name": "Oman"},
    {"country_code": "QA", "region_id": 289688,  "region_name": "Qatar"},
    {"country_code": "PR", "region_id": 4566966, "region_name": "Puerto Rico"},
    {"country_code": "SE", "region_id": 2661886, "region_name": "Sweden"},
    {"country_code": "GB", "region_id": 2635167, "region_name": "United Kingdom"},
    {"country_code": "UA", "region_id": 690791,  "region_name": "Ukraine"},
    {"country_code": "AZ", "region_id": 587116,  "region_name": "Azerbaijan"},
    {"country_code": "DO", "region_id": 3508796, "region_name": "Dominican Republic"},
    {"country_code": "NO", "region_id": 3144096, "region_name": "Norway"},
    {"country_code": "FI", "region_id": 660013,  "region_name": "Finland"},
    {"country_code": "NG", "region_id": 2328926, "region_name": "Nigeria"},
    {"country_code": "CH", "region_id": 2658434, "region_name": "Switzerland"},
    {"country_code": "JP", "region_id": 1861060, "region_name": "Japan"},
    {"country_code": "BH", "region_id": 290291,  "region_name": "Bahrain"},
    {"country_code": "LB", "region_id": 272103,  "region_name": "Lebanon"},
    {"country_code": "HU", "region_id": 719819,  "region_name": "Hungary"},
    {"country_code": "IT", "region_id": 3175395, "region_name": "Italy"},
    {"country_code": "BR", "region_id": 3469034, "region_name": "Brazil"},
    {"country_code": "US", "region_id": 6252001, "region_name": "United States"},
    {"country_code": "EG", "region_id": 357994,  "region_name": "Egypt"},
    {"country_code": "IQ", "region_id": 99237,   "region_name": "Iraq"},
    {"country_code": "PT", "region_id": 2264397, "region_name": "Portugal"},
    {"country_code": "PK", "region_id": 1168579, "region_name": "Pakistan"},
    {"country_code": "BO", "region_id": 3923057, "region_name": "Bolivia"},
    {"country_code": "PY", "region_id": 3437598, "region_name": "Paraguay"},
    {"country_code": "BD", "region_id": 1210997, "region_name": "Bangladesh"},
    {"country_code": "DE", "region_id": 2921044, "region_name": "Germany"},
    {"country_code": "ES", "region_id": 2510769, "region_name": "Spain"},
    {"country_code": "DZ", "region_id": 2589581, "region_name": "Algeria"},
    {"country_code": "PL", "region_id": 798544,  "region_name": "Poland"},
    {"country_code": "TR", "region_id": 298795,  "region_name": "Turkey"},
    {"country_code": "ZA", "region_id": 953987,  "region_name": "South Africa"},
    {"country_code": "BY", "region_id": 630336,  "region_name": "Belarus"},
    {"country_code": "AE", "region_id": 290557,  "region_name": "United Arab Emirates"},
    {"country_code": "GR", "region_id": 390903,  "region_name": "Greece"}
]

# Build lookup maps for easy assignment
CODE_LOOKUP = {item['region_id']: item['country_code'] for item in MAPPINGS}
NAME_LOOKUP = {item['region_id']: item['region_name'] for item in MAPPINGS}

 def add_region_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with a `geo_location` column of region IDs,
    add `region_id`, `country_code`, and `region_name` columns.
    """
    # Ensure geo_location is integer for lookup
    df['region_id'] = df['geo_location'].astype(int)
    # Map lookups
    df['country_code'] = df['region_id'].map(CODE_LOOKUP)
    df['region_name'] = df['region_id'].map(NAME_LOOKUP)
    return df


def main(input_path: str, output_path: str):
    # Load the original country output CSV
    df = pd.read_csv(input_path)
    # Add the region metadata columns
    df = add_region_columns(df)
    # Save augmented CSV
    df.to_csv(output_path, index=False)
    print(f"Wrote augmented data to: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Add country_code, region_id, and region_name based on geo_location to CSV.'
    )
    parser.add_argument('--input', '-i', default='country_output.csv', help='Path to input CSV file')
    parser.add_argument('--output', '-o', default='country_output_with_regions.csv', help='Path to output CSV file')
    args = parser.parse_args()
    main(args.input, args.output)
