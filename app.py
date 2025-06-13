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

################ EXTRACT DATA VIA API REQUESTS####################
# Define input schema for FastAPI
class InputItem(BaseModel):
    location_id: str
    age: str
    gender: str
    country: str

class InputList(BaseModel):
    inputs: list[InputItem]

app = FastAPI()

#get audience estimate
url = 'https://business-api.tiktok.com/open_api/v1.3/ad/audience_size/estimate/'
headers = {
    'Access-Token': access_token,
    'Content-Type': 'application/json'
}

results = []
output_columns = ["name", "ages_ranges", "geo_location", "genders", "interests", "behavior", "scholarities", "languages", "family_statuses", "all_fields", "targeting", "response", "lower_end","upper_end","user_count_stage"]
retries = 3
sleep = 0.2

def get_audience_estimate(data):
    for attempt in range(retries):
        response = requests.post(url, headers=headers, json=data).json()
        if response.get("code") == 0:
            return response
        elif response.get("code") == 51052:
            print(f"Error on attempt {attempt+1}, retrying {data}")
            time.sleep(sleep)
        else:
            print(f"API error {response.get('code')}: {response.get('message')} for input {data}")
            time.sleep(sleep)
            return None
    print("Max retries reached, skipping.")
    return None

def process_input(input):
    data = {
        "advertiser_id": '7381489555305775105',
        "objective_type": "REACH",
        "optimization_goal": "REACH",
        "placements": ["PLACEMENT_TIKTOK", "PLACEMENT_PANGLE", "PLACEMENT_GLOBAL_APP_BUNDLE"],
        "location_ids": [input.location_id],
        "gender": input.gender,
        "age_groups": [input.age]
    }
    try:
        response = get_audience_estimate(data)
        if not response:
            return None
        entry = {
            "name": input.country,
            "ages_ranges": input.age,
            "geo_location": input.location_id,
            "genders": input.gender,
            "interests": None,
            "behavior": None,
            "scholarities": None,
            "languages": None,
            "family_statuses": None,
            "all_fields": data,
            "targeting": None,
            "response": response,
            "lower_end": response["data"]["user_count"]["lower_end"],
            "upper_end": response["data"]["user_count"]["upper_end"],
            "user_count_stage": response["data"]["user_count_stage"]
        }
        return entry
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

MAX_WORKERS = 5
@app.post("/audience_estimate/")

def audience_estimate(input_list: InputList):
    results = []
    futures = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for inp in input_list.inputs:
            futures.append(executor.submit(process_input, inp)) 
        for future in tqdm(as_completed(futures),total=len(futures),desc="Processing inputs"):
            res = future.result()
            if res:
                results.append(res)
    if results:
        results_df = pd.DataFrame(results)
        results_df.reset_index(inplace=True)
        results_df['timestamp'] = datetime.now()
        results_df.to_csv('output.csv', encoding='utf-8-sig')
        print(f"Results to csv done")
        return {"message":f"Processed {len(results)} inputs", "output_file": "output.csv"}

@app.get("/download_csv/")
def download_csv():
    return FileResponse("output.csv", media_type='text/csv', filename="output.csv")