from pathlib import Path
import pandas as pd

POP_FILE = Path("data/raw/un_1950_2023_processed.csv")
pop = pd.read_csv(POP_FILE)
pop = pop[pop["Year"]==2023] # to match prior analysis on fb/instagram

# print(pop.columns.tolist())

# target age ranges. ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
# group to match tiktok data
pop["age_13_17_men"] = pop["14_15_m"]+pop["16_17_m"]
pop["age_13_17_women"] = pop["14_15_f"]+pop["16_17_f"]
pop["age_18_24_men"] = pop["18_19_m"]+pop["20_24_m"]
pop["age_18_24_women"] = pop["18_19_f"]+pop["20_24_f"]
pop["age_25_34_men"] = pop["25_29_m"]+pop["30_34_m"]
pop["age_25_34_women"] = pop["25_29_f"]+pop["30_34_f"]
pop["age_35_44_men"] = pop["35_39_m"]+pop["40_44_m"]
pop["age_35_44_women"] = pop["35_39_f"]+pop["40_44_f"]
pop["age_45_54_men"] = pop["45_49_m"]+pop["50_54_m"]
pop["age_45_54_women"] = pop["45_49_f"]+pop["50_54_f"]
pop["age_55_100_men"] = pop["55_59_m"]+pop["60_64_m"]+pop["65_inf_m"]
pop["age_55_100_women"] = pop["55_59_f"]+pop["60_64_f"]+pop["65_inf_f"]

keep = ["iso3","age_13_17_men", "age_13_17_women","age_18_24_men","age_18_24_women","age_25_34_men","age_25_34_women","age_35_44_men","age_35_44_women","age_45_54_men","age_45_54_women","age_55_100_men","age_55_100_women"]
pop=pop[keep]

# compute female-to-male ratio per age group
age_groups = ['13_17', '18_24', '25_34', '35_44', '45_54', '55_100']

for group in age_groups:
    men_col = f'age_{group}_men'
    women_col = f'age_{group}_women'
    ratio_col = f'age_{group}_ratio' 
    pop[ratio_col] = pop[women_col] / pop[men_col]

#print(pop.head())

pop["total_men"] = pop[[f'age_{group}_men' for group in age_groups]].sum(axis=1)
pop["total_women"] = pop[[f'age_{group}_women' for group in age_groups]].sum(axis=1)
pop["total_all"] = pop["total_men"]+ pop["total_women"]
pop["total_ratio"] = pop["total_women"] / pop["total_men"]

pop.to_csv('data/cleaned/pop_clean.csv', index=False, encoding='utf-8-sig', sep=";") # use -sig for Excel compatibility, add and strip out BOM
print(f"Population data cleaned")