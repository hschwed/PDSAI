from pathlib import Path
import pandas as pd

FB_FILE = Path("data/raw/FB_mau_upper_202501_averaged.csv")
fb = pd.read_csv(FB_FILE)

# target age ranges. ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
# group to match tiktok data
fb["age_13_17_men"] = fb['FB_age_14_15_men']  + fb['FB_age_16_17_men']
fb["age_13_17_women"]= fb['FB_age_14_15_women']  + fb['FB_age_16_17_women']
fb["age_18_24_men"] = fb['FB_age_18_19_men'] + fb['FB_age_20_24_men']
fb["age_18_24_women"]= fb['FB_age_18_19_women'] + fb['FB_age_20_24_women']
fb["age_25_34_men"] = fb['FB_age_25_29_men'] + fb['FB_age_30_34_men']
fb["age_25_34_women"]= fb['FB_age_25_29_women'] + fb['FB_age_30_34_women']
fb["age_35_44_men"] = fb['FB_age_35_39_men'] + fb['FB_age_40_44_men']
fb["age_35_44_women"] = fb['FB_age_35_39_women'] + fb['FB_age_40_44_women']
fb["age_45_54_men"] = fb['FB_age_45_49_men'] + fb['FB_age_50_54_men']
fb["age_45_54_women"] = fb['FB_age_45_49_women'] + fb['FB_age_50_54_women']
fb["age_55_100_men"] = fb['FB_age_55_59_men'] + fb['FB_age_60_64_men'] + fb['FB_age_65_plus_men']
fb["age_55_100_women"] = fb['FB_age_55_59_women'] + fb['FB_age_60_64_women'] + fb['FB_age_65_plus_women']

keep = ["iso3","Country","age_13_17_men", "age_13_17_women","age_18_24_men","age_18_24_women","age_25_34_men","age_25_34_women","age_35_44_men","age_35_44_women","age_45_54_men","age_45_54_women","age_55_100_men","age_55_100_women"]
fb=fb[keep]
fb.rename(columns={"Country":"iso2"})

# compute female-to-male ratio per age group
age_groups = ['13_17', '18_24', '25_34', '35_44', '45_54', '55_100']

for group in age_groups:
    men_col = f'age_{group}_men'
    women_col = f'age_{group}_women'
    ratio_col = f'age_{group}_ratio' 
    fb[ratio_col] = fb[women_col] / fb[men_col]

#print(fb.columns)
#print(fb.head())

# adding totals
fb["total_men"] = fb[[f'age_{group}_men' for group in age_groups]].sum(axis=1)
fb["total_women"] = fb[[f'age_{group}_women' for group in age_groups]].sum(axis=1)
fb["total_all"] = fb["total_men"]+ fb["total_women"]
fb["total_ratio"] = fb["total_women"] / fb["total_men"]

fb.to_csv('data/cleaned/fb_clean.csv', index=False, encoding='utf-8-sig', sep=";") # use -sig for Excel compatibility, add and strip out BOM
print(f"Facebook data cleaned")