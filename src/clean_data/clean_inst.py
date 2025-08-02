from config.config import Config
from pathlib import Path
import pandas as pd
from src.utils.logger import get_logger
import os

config = Config()
logger = get_logger(__name__)

def clean_insta():
    logger.info("Cleaning Instagram data...")
    INST_FILE = config.insta
    inst = pd.read_csv(INST_FILE)
    if os.path.isfile(config.insta):
        logger.info(f"Loaded: {config.insta}")
    else:
        logger.error(f"Failed to load: {config.insta}")

    #print(inst.columns.tolist())

    # target age ranges. ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
    # group to match tiktok data
    inst["age_13_17_men"] = inst["Ins_14_15_men"]+inst["Ins_16_17_men"]
    inst["age_13_17_women"] = inst["Ins_14_15_women"]+inst["Ins_16_17_women"]
    inst["age_18_24_men"] = inst["Ins_18_19_men"]+inst["Ins_20_24_men"]
    inst["age_18_24_women"] = inst["Ins_18_19_women"]+inst["Ins_20_24_women"]
    inst["age_25_34_men"] = inst["Ins_25_29_men"]+inst["Ins_30_34_men"]
    inst["age_25_34_women"] = inst["Ins_25_29_women"]+inst["Ins_30_34_women"]
    inst["age_35_44_men"] = inst["Ins_35_39_men"]+inst["Ins_40_44_men"]
    inst["age_35_44_women"] = inst["Ins_35_39_women"]+inst["Ins_40_44_women"]
    inst["age_45_54_men"] = inst["Ins_45_49_men"]+inst["Ins_50_54_men"]
    inst["age_45_54_women"] = inst["Ins_45_49_women"]+inst["Ins_50_54_women"]
    inst["age_55_100_men"] = inst["Ins_55_59_men"]+inst["Ins_60_64_men"]+inst["Ins_65_999_men"]
    inst["age_55_100_women"] = inst["Ins_55_59_women"]+inst["Ins_60_64_women"]+inst["Ins_65_999_women"]

    keep = ["iso3","age_13_17_men", "age_13_17_women","age_18_24_men","age_18_24_women","age_25_34_men","age_25_34_women","age_35_44_men","age_35_44_women","age_45_54_men","age_45_54_women","age_55_100_men","age_55_100_women"]
    inst=inst[keep]

    # compute female-to-male ratio per age group
    age_groups = ['13_17', '18_24', '25_34', '35_44', '45_54', '55_100']

    for group in age_groups:
        men_col = f'age_{group}_men'
        women_col = f'age_{group}_women'
        ratio_col = f'age_{group}_ratio' 
        inst[ratio_col] = inst[women_col] / inst[men_col]

    # print(inst.head())

    inst["total_men"] = inst[[f'age_{group}_men' for group in age_groups]].sum(axis=1)
    inst["total_women"] = inst[[f'age_{group}_women' for group in age_groups]].sum(axis=1)
    inst["total_all"] = inst["total_men"]+ inst["total_women"]
    inst["total_ratio"] = inst["total_women"] / inst["total_men"]

    inst.to_csv(config.insta_clean, index=False, encoding='utf-8-sig', sep=";") # use -sig for Excel compatibility, add and strip out BOM
    if os.path.isfile(config.insta_clean):
        logger.info(f"Saved: {config.insta_clean}")
    else:
        logger.error(f"Failed to save: {config.insta_clean}")