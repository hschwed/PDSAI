from config.config import Config
from pathlib import Path
import pandas as pd
from src.utils.country_code import get_iso2,get_iso3
from src.utils.logger import get_logger
import os

config = Config()
logger = get_logger(__name__)

INST_FILE = config.insta_clean
POP_FILE = config.pop_clean
TT_FILE = config.tt_clean
FB_FILE = config.fb_clean
TT_INTEREST_FILE = config.tt_interest_clean

FILE_NAMES = {INST_FILE: "insta", POP_FILE: "population", TT_FILE: "tiktok", FB_FILE: "facebook", TT_INTEREST_FILE: "tiktok_interest"}

INTEREST_GROUP_NAMES = ["business", "finance", "education", "health", "children"]

def get_pop_col(col):
    """Strip interest group name from column name to get the equivalent population column."""
    for g in INTEREST_GROUP_NAMES:
        for suffix in ("_men", "_women", "_ratio", "_all"):
            if col.endswith(f"_{g}{suffix}"):
                return col[: -(len(g) + len(suffix) + 1)] + suffix
    return col


def check_empty(df,name):
    """
    Drops rows with missing values in 'iso2' or 'iso3' columns as this leads to errors later on.

    Parameters:
        df (pd.DataFrame): Input DataFrame.
        name (str): Optional name for logging.

    Returns:
        pd.DataFrame: DataFrame with blank ISO rows removed.
    """
    logger.info(f"Check for empty rows in data: {name}...")
    if "iso2" in df.columns:
        before = len(df)
        df = df[df["iso2"].notnull()]
        after = len(df)
        logger.info(f"Removed {before - after} rows with blank 'iso2' in: {name}")
    elif "iso3" in df.columns:
        before = len(df)
        df = df[df["iso3"].notnull()]
        after = len(df)
        logger.info(f"Removed {before - after} rows with blank 'iso3' in: {name}")
    else:
        logger.info(f"Neither 'iso2' nor 'iso3' column found. No rows removed.")

    return df


def add_iso2(df,name):
    logger.info(f"Adding ISO2 country codes for: {name}...")
    if "iso2" not in df.columns:
        if "iso3" not in df.columns:
            logger.info("Cannot add iso2: 'iso3' column missing.")
            return df  
        df["iso2"] = df["iso3"].apply(get_iso2)

        unmapped = df[df["iso2"].isnull()]
        if not unmapped.empty:
            logger.info(f"Unmapped ISO3 codes: {unmapped['iso3'].tolist()} in: {name}")
        logger.info(f"ISO2 codes added for: {name}.")

    return df

def add_iso3(df,name):
    logger.info(f"Adding ISO3 country codes for: {name}...")
    if "iso3" not in df.columns:
        if "iso2" not in df.columns:
            logger.info("Cannot add iso3: 'iso2' column missing.")
            return df  
        df["iso3"] = df["iso2"].apply(get_iso3)

        unmapped = df[df["iso3"].isnull()]
        if not unmapped.empty:
            logger.info(f"Unmapped ISO2 codes: {unmapped['iso2'].tolist()} in: {name}")
        logger.info(f"ISO3 codes added for: {name}.")

    return df
    
def add_standardized_ratio(pop_df,df,name):
    logger.info(f"Adding standardized gender gap ratio for: {name} ...")

    ratio_cols = [col for col in df.columns if col.endswith("_ratio")]

    for col in ratio_cols:
        pop_col = get_pop_col(col)
        def compute_std(row, col=col, pop_col=pop_col):
            country = row["iso3"]
            value = row[col]

            if country in pop_df.index and pop_col in pop_df.columns:
                pop_value = pop_df.at[country, pop_col]
                if pd.notnull(pop_value) and pop_value != 0:
                    return (value / pop_value).round(4)
            return float('nan')

        df[col+"_std"] = df.apply(compute_std,axis=1)
    logger.info(f"Standardized ratios added for: {name}.") 

    return df

def add_penetration_ratio(pop_df,df,name):
    logger.info(f"Adding penetration ratio for: {name} ...")

    cols = [col for col in df.columns if col.endswith(("_women","_men","_all"))]

    for col in cols:
        pop_col = get_pop_col(col)
        def compute_pen(row, col=col, pop_col=pop_col):
            country = row["iso3"]
            value = row[col]

            if country in pop_df.index and pop_col in pop_df.columns:
                pop_value = pop_df.at[country, pop_col]
                if pd.notnull(pop_value) and pop_value != 0:
                    return (value / pop_value).round(4)
            return float('nan')

        df[col+"_pen"] = df.apply(compute_pen,axis=1)
    logger.info(f"Penetration ratios added for: {name}") 

    return df

def run_transform():
    #process population data first as this is needed for others
    pop_df = pd.read_csv(POP_FILE,sep=";")
    pop_df = add_iso2(pop_df,"pop")
    pop_df = add_iso3(pop_df,"pop")
    pop_df.to_csv(config.pop_final, index=False, encoding='utf-8-sig', sep=";")
    if os.path.isfile(config.pop_final):
        logger.info(f"Saved: {config.pop_final}")
    else:
        logger.error(f"Failed to save: {config.pop_final}")
    
    pop_df_indexed = pop_df.set_index("iso3")

    #process each of the main data files
    FILES = [INST_FILE, TT_FILE, FB_FILE]

    OUTPUT_PATHS = {INST_FILE: config.insta_final, TT_FILE: config.tt_final, FB_FILE: config.fb_final }

    for file in FILES:
        df = pd.read_csv(file,sep=";")
        name = FILE_NAMES[file]
        output_path = OUTPUT_PATHS[file]
        logger.info(f"Start processing transformations for: {name}....")

        df = check_empty(df,name)
        df = add_iso2(df,name)
        df = add_iso3(df,name)
        df = add_standardized_ratio(pop_df_indexed,df,name)
        df = add_penetration_ratio(pop_df_indexed,df,name)

        df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=";")
        if os.path.isfile(output_path):
            logger.info(f"Transformation done. Saved: {output_path}")
        else:
            logger.error(f"Failed to save: {output_path}")

def run_transform_interest():
    #process population data first as this is needed for standardized/penetration ratios
    pop_df = pd.read_csv(POP_FILE,sep=";")
    pop_df = add_iso2(pop_df,"pop")
    pop_df = add_iso3(pop_df,"pop")
    pop_df.to_csv(config.pop_final, index=False, encoding='utf-8-sig', sep=";")
    if os.path.isfile(config.pop_final):
        logger.info(f"Saved: {config.pop_final}")
    else:
        logger.error(f"Failed to save: {config.pop_final}")

    pop_df_indexed = pop_df.set_index("iso3")

    #process tiktok interest data
    df = pd.read_csv(TT_INTEREST_FILE, sep=";")
    name = FILE_NAMES[TT_INTEREST_FILE]
    output_path = config.tt_interest_final
    logger.info(f"Start processing transformations for: {name}....")

    df = check_empty(df, name)
    df = add_iso2(df, name)
    df = add_iso3(df, name)
    df = add_standardized_ratio(pop_df_indexed, df, name)
    df = add_penetration_ratio(pop_df_indexed, df, name)

    df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=";")
    if os.path.isfile(output_path):
        logger.info(f"Transformation done. Saved: {output_path}")
    else:
        logger.error(f"Failed to save: {output_path}")

if __name__ == "__main__":
    run_transform_interest()
    #run_transform()

