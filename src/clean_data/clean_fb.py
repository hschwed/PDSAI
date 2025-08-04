from config.config import Config
from pathlib import Path
import pandas as pd
from src.utils.logger import get_logger
import os

config = Config()
logger = get_logger(__name__)

def clean_facebook():
    logger.info("Cleaning Facebook data...")
    FB_FILE = config.fb
    fb = pd.read_csv(FB_FILE)
    if os.path.isfile(config.fb):
        logger.info(f"Loaded: {config.fb}")
    else:
        logger.error(f"Failed to load: {config.fb}")

    # target age ranges. ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
    # group to match tiktok data
    fb["age_13_17_men"] = fb['FB_age_14_15_men'].round(0).astype(int)  + fb['FB_age_16_17_men'].round(0).astype(int)
    fb["age_13_17_women"]= fb['FB_age_14_15_women'].round(0).astype(int)  + fb['FB_age_16_17_women'].round(0).astype(int)
    fb["age_18_24_men"] = fb['FB_age_18_19_men'].round(0).astype(int) + fb['FB_age_20_24_men'].round(0).astype(int)
    fb["age_18_24_women"]= fb['FB_age_18_19_women'].round(0).astype(int) + fb['FB_age_20_24_women'].round(0).astype(int)
    fb["age_25_34_men"] = fb['FB_age_25_29_men'].round(0).astype(int) + fb['FB_age_30_34_men'].round(0).astype(int)
    fb["age_25_34_women"]= fb['FB_age_25_29_women'].round(0).astype(int) + fb['FB_age_30_34_women'].round(0).astype(int)
    fb["age_35_44_men"] = fb['FB_age_35_39_men'].round(0).astype(int) + fb['FB_age_40_44_men'].round(0).astype(int)
    fb["age_35_44_women"] = fb['FB_age_35_39_women'].round(0).astype(int) + fb['FB_age_40_44_women'].round(0).astype(int)
    fb["age_45_54_men"] = fb['FB_age_45_49_men'].round(0).astype(int) + fb['FB_age_50_54_men'].round(0).astype(int)
    fb["age_45_54_women"] = fb['FB_age_45_49_women'].round(0).astype(int) + fb['FB_age_50_54_women'].round(0).astype(int)
    fb["age_55_100_men"] = fb['FB_age_55_59_men'].round(0).astype(int) + fb['FB_age_60_64_men'].round(0).astype(int) + fb['FB_age_65_plus_men'].round(0).astype(int)
    fb["age_55_100_women"] = fb['FB_age_55_59_women'].round(0).astype(int) + fb['FB_age_60_64_women'].round(0).astype(int) + fb['FB_age_65_plus_women'].round(0).astype(int)

    keep = ["iso3","Country","age_13_17_men", "age_13_17_women","age_18_24_men","age_18_24_women","age_25_34_men","age_25_34_women","age_35_44_men","age_35_44_women","age_45_54_men","age_45_54_women","age_55_100_men","age_55_100_women"]
    fb=fb[keep]
    fb.rename(columns={"Country":"iso2"})

    # compute female-to-male ratio per age group
    age_groups = ['13_17', '18_24', '25_34', '35_44', '45_54', '55_100']

    for group in age_groups:
        men_col = f'age_{group}_men'
        women_col = f'age_{group}_women'
        ratio_col = f'age_{group}_ratio' 
        fb[ratio_col] = (fb[women_col] / fb[men_col]).round(4)

    #print(fb.columns)
    #print(fb.head())

    # adding totals
    fb["total_men"] = fb[[f'age_{group}_men' for group in age_groups]].sum(axis=1)
    fb["total_women"] = fb[[f'age_{group}_women' for group in age_groups]].sum(axis=1)
    fb["total_all"] = fb["total_men"]+ fb["total_women"]
    fb["total_ratio"] = (fb["total_women"] / fb["total_men"]).round(4)

    fb.to_csv(config.fb_clean, index=False, encoding='utf-8-sig', sep=";") # use -sig for Excel compatibility, add and strip out BOM
    if os.path.isfile(config.fb_clean):
        logger.info(f"Saved: {config.fb_clean}")
    else:
        logger.error(f"Failed to save: {config.fb_clean}")
    
if __name__ == "__main__":
    clean_facebook()
