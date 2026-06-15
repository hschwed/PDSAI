from config.config import Config
from pathlib import Path
import pandas as pd
from src.utils.logger import get_logger
from src.utils.country_code import get_iso3
import os
import json

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

    tt = tt[["level","country_code","name","ages_ranges","genders","lower_end","upper_end"]]
    tt["tt_estimate"] = ((tt["lower_end"]+ tt["upper_end"]) / 2).round(0).astype(int)

    tt.drop(columns=["lower_end", "upper_end"], inplace=True)

    if config.level == "dma":
        tt["country_code"] = tt["country_code"].fillna("US") # only for DMA as it is for US only and None causes problems when flattening, pivoting
    tt.rename(columns={"country_code": "iso2"}, inplace=True)

    tt = tt.pivot_table(index=["level", "iso2", "name"], columns=["ages_ranges","genders"], values ="tt_estimate")
    #flatten columns
    tt.columns = [f"{age.lower()}_{'women' if gender == 'GENDER_FEMALE' else 'men'}" 
                for age, gender in tt.columns]
    tt.reset_index(inplace=True)
    tt.insert(tt.columns.get_loc("iso2") + 1, "iso3", tt["iso2"].map(get_iso3))

    # compute female-to-male ratio per age group
    age_groups = ['13_17', '18_24', '25_34', '35_44', '45_54', '55_100']

    for group in age_groups:
        men_col = f'age_{group}_men'
        women_col = f'age_{group}_women'
        ratio_col = f'age_{group}_ratio' 
        tt[ratio_col] = (tt[women_col] / tt[men_col]).round(4)

    #print(tt.head())
    #print(tt.columns.tolist())

    # adding totals
    tt["total_men"] = tt[[f'age_{group}_men' for group in age_groups]].sum(axis=1)
    tt["total_women"] = tt[[f'age_{group}_women' for group in age_groups]].sum(axis=1)
    tt["total_all"] = tt["total_men"]+ tt["total_women"]
    tt["total_ratio"] = (tt["total_women"] / tt["total_men"]).round(4)
    tt["total_18_44_men"] = tt["age_18_24_men"] + tt["age_25_34_men"] + tt["age_35_44_men"]
    tt["total_18_44_women"] = tt["age_18_24_women"] + tt["age_25_34_women"] + tt["age_35_44_women"]
    tt["total_18_44_ratio"] = (tt["total_18_44_women"] / tt["total_18_44_men"]).round(4)

    tt.to_csv(config.tt_clean, index=False, encoding='utf-8-sig', sep=";") # use -sig for Excel compatibility, add and strip out BOM
    if os.path.isfile(config.tt_clean):
        logger.info(f"Saved: {config.tt_clean}")
    else:
        logger.error(f"Failed to save: {config.tt_clean}")

#manual assignment
INTEREST_GROUPS = {
    "business":  ["Business Services"], #top level
    "finance":   ["Financial Services"], #top level
    "education": ["Education"], #top level
    "health":    ["Medical Care", "Healthy Lifestyle", "Health & Fitness", "Health & Wellness"], #child level
    "children":  ["Baby & Kids Products", "Parenting"], # mix
    "travel":    ["Travel"], #top level
    "pets":      ["Pets"], #top level
    "food":      ["Food & Beverage"] #top level
}

def clean_tiktok_interest():
    logger.info("Cleaning TikTok interest data...")
    tt = pd.read_csv(config.tt_interest)
    if os.path.isfile(config.tt_interest):
        logger.info(f"Loaded: {config.tt_interest}")
    else:
        logger.error(f"Failed to load: {config.tt_interest}")

    tt = tt[["level","country_code","name","ages_ranges","genders","interest_id","lower_end","upper_end"]]
    tt["tt_estimate"] = ((tt["lower_end"]+ tt["upper_end"]) / 2).round(0).astype(int)
    tt.drop(columns=["lower_end", "upper_end"], inplace=True)

    if config.level == "dma":
        tt["country_code"] = tt["country_code"].fillna("US")
    tt.rename(columns={"country_code": "iso2"}, inplace=True)

    # map interest_id to interest_name
    with open("data/raw/interest.json", encoding="utf-8") as f:
        interest_lookup = {item["id"]: item["name"] for item in json.load(f)}
    tt["interest_name"] = tt["interest_id"].astype(str).map(interest_lookup)

    tt = tt.pivot_table(index=["level", "iso2", "name", "interest_id", "interest_name"], columns=["ages_ranges","genders"], values="tt_estimate")
    tt.columns = [f"{age.lower()}_{'women' if gender == 'GENDER_FEMALE' else 'men'}"
                for age, gender in tt.columns]
    tt.reset_index(inplace=True)
    tt.insert(tt.columns.get_loc("iso2") + 1, "iso3", tt["iso2"].map(get_iso3))

    # compute summable columns per interest row (ratios recomputed after grouping)
    age_groups = ['13_17', '18_24', '25_34', '35_44', '45_54', '55_100']
    tt["total_men"] = tt[[f'age_{g}_men' for g in age_groups]].sum(axis=1)
    tt["total_women"] = tt[[f'age_{g}_women' for g in age_groups]].sum(axis=1)
    tt["total_all"] = tt["total_men"] + tt["total_women"]
    tt["total_18_44_men"] = tt["age_18_24_men"] + tt["age_25_34_men"] + tt["age_35_44_men"]
    tt["total_18_44_women"] = tt["age_18_24_women"] + tt["age_25_34_women"] + tt["age_35_44_women"]

    # aggregate by group and country
    index_cols = ["level", "iso2", "iso3", "name"]
    men_cols = [f'age_{g}_men' for g in age_groups]
    women_cols = [f'age_{g}_women' for g in age_groups]
    sum_cols = men_cols + women_cols + ["total_men", "total_women", "total_all", "total_18_44_men", "total_18_44_women"]

    result = tt[index_cols].drop_duplicates().reset_index(drop=True)

    for group_name, interest_names in INTEREST_GROUPS.items():
        mask = tt["interest_name"].isin(interest_names)
        group_df = tt[mask].groupby(index_cols)[sum_cols].sum().reset_index()

        # recompute ratios from aggregated sums
        for g in age_groups:
            group_df[f'age_{g}_ratio'] = (group_df[f'age_{g}_women'] / group_df[f'age_{g}_men']).round(4)
        group_df["total_ratio"] = (group_df["total_women"] / group_df["total_men"]).round(4)
        group_df["total_18_44_ratio"] = (group_df["total_18_44_women"] / group_df["total_18_44_men"]).round(4)

        # rename: insert group_name before _men/_women/_ratio/_all suffix
        rename = {}
        for col in group_df.columns:
            if col in index_cols:
                continue
            for suffix in ("_men", "_women", "_ratio", "_all"):
                if col.endswith(suffix):
                    base = col[:-len(suffix)]
                    rename[col] = f"{base}_{group_name}{suffix}"
                    break
        group_df = group_df.rename(columns=rename)
        result = result.merge(group_df, on=index_cols, how="left")

    result.to_csv(config.tt_interest_clean, index=False, encoding='utf-8-sig', sep=";")
    if os.path.isfile(config.tt_interest_clean):
        logger.info(f"Saved: {config.tt_interest_clean}")
    else:
        logger.error(f"Failed to save: {config.tt_interest_clean}")

if __name__ == "__main__":
    #clean_tiktok()
    clean_tiktok_interest()