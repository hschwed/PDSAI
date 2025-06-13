import uvicorn
import nest_asyncio
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pandas as pd
from datetime import datetime
import time
import itertools
import json
nest_asyncio.apply()
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.responses import FileResponse
from tqdm import tqdm

# Credentials
advertiser_id = '7381489555305775105'
secret = '01bebffff7dd4469b207a1622ad3892dfdf862a0'
app_id = '7384250931329630225'
auth_code = 'f57f9e8b140d03312509d43a9e70a96e65fde888' ## need to open link from App once reviewed; only valid for 1 hour, can only be used once
access_token = '7e4105012622ac077282d8a3e4bd6f937cbdec70'

################# PREPARING INPUT ######################
def generate_inputs():
    #get values for locations, age_ranges and gender and build json formatted input

    #location_id or region_code. Research API lets you use region_code = country_codes
    url = ' https://business-api.tiktok.com/open_api/v1.3/search/region/'

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

    countries_df = pd.json_normalize(results)
    countries_df = countries_df.drop(['area_type','parent_id'],axis=1)
    #print(countries_df)

    country = countries_df[countries_df['region_level']=='COUNTRY'][['country_code','region_id']]
    #.drop_duplicates().reset_index(drop=True)
    #countries_df['country_code'].unique()
    #print(country)

    province = countries_df[countries_df['region_level']=='PROVINCE'][['country_code','region_name','region_id']]
    #print(province)


    district = countries_df[countries_df['region_level']=='DISTRICT'][['country_code','region_name','region_id']]
    #print(district)

    city = countries_df[countries_df['region_level']=='CITY'][['country_code','region_name','region_id']]
    #print(city)

    countries_df.to_csv('countries.csv',encoding='utf-8-sig')
    #files.download('countries.csv')

    #need ad group id for this, to get this id we would need to create a campaign and ad --> refer to fixed values for now
    #if targeting_info and "age" in targeting_info:
    #    age_buckets = list(targeting_info["age"].keys())
    #else:

    # reduce to one group for test, full: ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
    age = ["AGE_18_24"]

    gender = ["GENDER_FEMALE", "GENDER_MALE", "GENDER_UNLIMITED"]

    #create input as json with all country, gender, age combinations
    countries = country['country_code'].to_list()
    location_ids = country['region_id'].to_list()

    combine = list(itertools.product(countries,location_ids,gender,age))

    #save input as csv for reference
    df = pd.DataFrame(combine)
    df.to_csv('input.csv',encoding='utf-8-sig')
    #files.download('input.csv')

    inputs = [{"country": country,"location_id":location, "gender": gender, "age": age} for country,location,gender,age in combine]
    #save as json for use in client.py
    with open("input_json.json", "w", encoding="utf-8") as f:
        json.dump({"inputs": inputs}, f, ensure_ascii=False, indent=2)

    print(inputs)
    print(f"Input has {len(inputs)} rows")