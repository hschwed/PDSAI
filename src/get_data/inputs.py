
from config.config import Config
import requests
import pandas as pd
import itertools
import json
import os
from src.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)

advertiser_id = config.advertiser_id
access_token = config.access_token

if not advertiser_id or not access_token:
    logger.error("Missing ADVERTISER_ID or ACCESS_TOKEN in .env")
    raise EnvironmentError("Missing required environment variables.")
else:
    logger.info("Environment variables loaded successfully.")

################# PREPARING INPUT ######################
def generate_inputs():
    logger.info("Generating inputs...")
    #get values for locations, age_ranges and gender and build json formatted input

    #location_id or region_code. Research API lets you use region_code = country_codes
    url = config.api_base_url + config.region_endpoint

    headers = {
        'Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    params = {
        'advertiser_id': advertiser_id,
    }

    response = requests.get(url, headers=headers, params=params)

    results = response.json()['data']['region_list'] #return json object of result of get request
    #geolist.to_csv('./config/specs/specs_explore/tiktok_regions_list.csv')

    results = pd.json_normalize(results)
    results = results.drop(['area_type','parent_id'],axis=1)
    #print(countries_df)

    country = results[results['region_level']=='COUNTRY'][['country_code','region_id']]
    #.drop_duplicates().reset_index(drop=True)
    #countries_df['country_code'].unique()
    #print(country)

    province = results[results['region_level']=='PROVINCE'][['country_code','region_name','region_id']]
    #print(province)


    district = results[results['region_level']=='DISTRICT'][['country_code','region_name','region_id']]
    #print(district)

    city = results[results['region_level']=='CITY'][['country_code','region_name','region_id']]
    #print(city)

    results.to_csv(config.location_ids,encoding='utf-8-sig')
    if os.path.isfile(config.location_ids):
        logger.info(f"Saved: {config.location_ids}")
    else:
        logger.error(f"Failed to save: {config.location_ids}")

    #files.download('countries.csv')

    #need ad group id for this, to get this id we would need to create a campaign and ad --> refer to fixed values for now
    #if targeting_info and "age" in targeting_info:
    #    age_buckets = list(targeting_info["age"].keys())
    #else:

    # reduce to one group for test, full: ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
    age = ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]

    #excluding "GENDER_UNLIMITED" as this is just female+male
    gender = ["GENDER_FEMALE", "GENDER_MALE"]

    #create input as json with all country, gender, age combinations
    countries = country['country_code'].to_list()
    location_ids = country['region_id'].to_list()

    age_gender_df = pd.DataFrame(itertools.product(gender, age), columns=["gender", "age"])

    combine = country.merge(age_gender_df,how='cross')

    #save input as csv for reference
    df = pd.DataFrame(combine)
    df.to_csv(config.input_csv,encoding='utf-8-sig')
    #files.download('input.csv')
    if os.path.isfile(config.input_csv):
        logger.info(f"Saved: {config.input_csv}")
    else:
        logger.error(f"Failed to save: {config.input_csv}")

    # country here is ISO2 code
    inputs = [{"country": row.country_code,"location_id":row.region_id, "gender": row.gender, "age": row.age} for row in combine.itertuples(index=False)]
    #save as json for use in client.py
    try:
        with open(config.input_json, "w", encoding="utf-8") as f:
            json.dump({"inputs": inputs}, f, ensure_ascii=False, indent=2)
        if os.path.isfile(config.input_json):
            logger.info(f"Successfully saved: {config.input_json}")
        else:
            logger.error(f"Failed to save {config.input_json}: file does not exist after writing.")
    except Exception as e:
        logger.error(f"Error saving {config.input_json}: {e}")

    #print(inputs)
    logger.info(f"Input has {len(inputs)} rows")
