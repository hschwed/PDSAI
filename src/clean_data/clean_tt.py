from config.config import Config
from pathlib import Path
import pandas as pd
from src.utils.logger import get_logger
import os

config = Config()
logger = get_logger(__name__)

def clean_tiktok():
    logger.info("Cleaning TikTok data...")
    TT_FILE = config.tt
    tt = pd.read_csv(TT_FILE)
    if os.path.isfile(config.tt):
        logger.info(f"Loaded: {config.tt}")
    else:
        logger.error(f"Failed to load: {config.tt}")

    tt = tt[["country_code","name","ages_ranges","genders","lower_end","upper_end"]]
    tt["tt_estimate"] = (tt["lower_end"]+ tt["upper_end"]) / 2

    tt.drop(columns=["lower_end", "upper_end"], inplace=True)
    tt.rename(columns={"country_code": "iso2"}, inplace=True)

    tt = tt.pivot_table(index="iso2", columns=["ages_ranges","genders"], values ="tt_estimate")
    #flatten columns
    tt.columns = [f"{age.lower()}_{'women' if gender == 'GENDER_FEMALE' else 'men'}" 
                for age, gender in tt.columns]
    tt.reset_index(inplace=True)

    # compute female-to-male ratio per age group
    age_groups = ['13_17', '18_24', '25_34', '35_44', '45_54', '55_100']

    for group in age_groups:
        men_col = f'age_{group}_men'
        women_col = f'age_{group}_women'
        ratio_col = f'age_{group}_ratio' 
        tt[ratio_col] = tt[women_col] / tt[men_col]

    #print(tt.head())
    #print(tt.columns.tolist())

    # adding totals
    tt["total_men"] = tt[[f'age_{group}_men' for group in age_groups]].sum(axis=1)
    tt["total_women"] = tt[[f'age_{group}_women' for group in age_groups]].sum(axis=1)
    tt["total_all"] = tt["total_men"]+ tt["total_women"]
    tt["total_ratio"] = tt["total_women"] / tt["total_men"]

    tt.to_csv(config.tt_clean, index=False, encoding='utf-8-sig', sep=";") # use -sig for Excel compatibility, add and strip out BOM
    if os.path.isfile(config.tt_clean):
        logger.info(f"Saved: {config.tt_clean}")
    else:
        logger.error(f"Failed to save: {config.tt_clean}")