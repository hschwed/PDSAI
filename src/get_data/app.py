
from config.config import Config
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pandas as pd
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import os
from src.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)

# Credentials
advertiser_id = config.advertiser_id
access_token = config.access_token

if not advertiser_id or not access_token:
    logger.error("Missing ADVERTISER_ID or ACCESS_TOKEN in .env")
    raise EnvironmentError("Missing required environment variables.")
else:
    logger.info("Environment variables loaded successfully.")

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
url = config.api_base_url + config.estimates_endpoint
headers = {
    'Access-Token': access_token,
    'Content-Type': 'application/json'
}

results = []
output_columns = ["name", "ages_ranges", "geo_location", "genders", "interests", "behavior", "scholarities", "languages", "family_statuses", "all_fields", "targeting", "response", "lower_end","upper_end","user_count_stage"]
retries = 3
sleep = 0.3

def get_audience_estimate(data):
    for attempt in range(retries):
        response = requests.post(url, headers=headers, json=data).json() #if should use multiple IP addresses, need proxy servers and specify inside requests.post()
        if response.get("code") == 0:
            return response
        elif response.get("code") == 51052:
            logger.warning(f"Error on attempt {attempt+1}, retrying {data}")
            time.sleep(sleep)
        else:
            logger.error(f"API error {response.get('code')}: {response.get('message')} for input {data}")
            time.sleep(sleep)
            return None
    logger.error("Max retries reached, skipping.")
    return None

def process_input(input):
    data = {
        "advertiser_id": advertiser_id,
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
            logger.warning(f"No valid response for input: {data}")
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
        logger.error(f"Request failed: {e}")
        return None

MAX_WORKERS = 3 # handle multiple I/O-bound tasks concurrently, request.post() blocks thread while waiting for response, using threads allows to start multiple requests in parallel and wait for them simultaneously. so total runtime != sum of individual requests
@app.post("/audience_estimate/")

def audience_estimate(input_list: InputList):
    results = []
    futures = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for inp in input_list.inputs:
            futures.append(executor.submit(process_input, inp)) # submit multiple tasks into thread pool, parallelize API requests in thread
        for future in tqdm(as_completed(futures),total=len(futures),desc="Processing inputs"): #as_completed waits for each task to finish
            res = future.result()
            if res:
                results.append(res)
    logger.info("Finished processing all inputs and submitting tasks into thread pool.")

    logger.info("Saving results...")
    if results:
        results_df = pd.DataFrame(results)
        results_df['timestamp'] = datetime.now()
        results_df.to_csv(config.tt_output, encoding='utf-8-sig')
        if os.path.isfile(config.tt_output):
            logger.info(f"Saved: {config.tt_output}")
        else:
            logger.error(f"Failed to save: {config.tt_output}")
        
        logger.info(f"Processed {len(results)} inputs. Output_file: {config.tt_output}")

        return {"message": "No results to save"}

