
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
import sys

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
    name: str
    country_code: str
    location_id: str
    age: str
    gender: str
    

class InputList(BaseModel):
    inputs: list[InputItem]

class InputItemInterest(BaseModel):
    name: str
    country_code: str
    location_id: str
    age: str
    gender: str
    interest_id: str

class InputListInterest(BaseModel):
    inputs: list[InputItemInterest]

class InputItemInterestCheck(BaseModel):
    name: str
    country_code: str
    location_id: str
    interest_id: str

class InputListInterestCheck(BaseModel):
    inputs: list[InputItemInterestCheck]

app = FastAPI()

#get audience estimate
url = config.api_base_url + config.estimates_endpoint
headers = {
    'Access-Token': access_token,
    'Content-Type': 'application/json'
}

results = []
level = config.level
output_columns = ["level","name", "country_code", "ages_ranges", "geo_location", "genders", "interests", "behavior", "scholarities", "languages", "family_statuses", "all_fields", "targeting", "response", "lower_end","upper_end","user_count_stage"]
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
        "placements": ["PLACEMENT_TIKTOK"], # removed "PLACEMENT_PANGLE" as this is targeting users in other apps and websites and inflates the numbers, removed "PLACEMENT_GLOBAL_APP_BUNDLE" as this targets bytedance other apps such as capcut, fizzo, melolo
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
            "level": f"{level}",
            "name": input.name,
            "country_code": input.country_code,
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

MAX_WORKERS = config.max_workers # handle multiple I/O-bound tasks concurrently, request.post() blocks thread while waiting for response, using threads allows to start multiple requests in parallel and wait for them simultaneously. so total runtime != sum of individual requests
@app.post("/audience_estimate/")

def audience_estimate(input_list: InputList):
    results = []
    futures = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for inp in input_list.inputs:
            futures.append(executor.submit(process_input, inp)) # submit multiple tasks into thread pool, parallelize API requests in thread
        for future in tqdm(as_completed(futures),total=len(futures),desc="Processing inputs", file=sys.stdout): #as_completed waits for each task to finish
            res = future.result()
            if res:
                results.append(res)
    logger.info("Finished processing all inputs and submitting tasks into thread pool.")

    logger.info("Saving results...")
    if results:
        results_df = pd.DataFrame(results)
        results_df['timestamp'] = datetime.now()
        results_df.to_csv(config.tt, encoding='utf-8-sig')
        if os.path.isfile(config.tt):
            logger.info(f"Saved: {config.tt}")
        else:
            logger.error(f"Failed to save: {config.tt}")
        
        logger.info(f"Processed {len(results)} inputs. Output_file: {config.tt}")

        return {"message": f"Processed {len(results)} inputs."}
    else:
        return {"message": "No results to save"}

def process_input_interest(input):
    data = {
        "advertiser_id": advertiser_id,
        "objective_type": "REACH",
        "optimization_goal": "REACH",
        "placements": ["PLACEMENT_TIKTOK"],
        "location_ids": [input.location_id],
        "gender": input.gender,
        "age_groups": [input.age],
        "interest_category_ids": [input.interest_id]
    }
    try:
        response = get_audience_estimate(data)
        if not response:
            logger.warning(f"No valid response for interest input: {data}")
            return None
        entry = {
            "level": f"{level}",
            "name": input.name,
            "country_code": input.country_code,
            "ages_ranges": input.age,
            "geo_location": input.location_id,
            "genders": input.gender,
            "interest_id": input.interest_id,
            "all_fields": data,
            "response": response,
            "lower_end": response["data"]["user_count"]["lower_end"],
            "upper_end": response["data"]["user_count"]["upper_end"],
            "user_count_stage": response["data"]["user_count_stage"]
        }
        return entry
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

@app.post("/audience_estimate_interest/")
def audience_estimate_interest(input_list: InputListInterest):
    results = []
    futures = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for inp in input_list.inputs:
            futures.append(executor.submit(process_input_interest, inp))
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing interest inputs", file=sys.stdout):
            res = future.result()
            if res:
                results.append(res)
    logger.info("Finished processing all interest inputs.")

    logger.info("Saving interest results...")
    if results:
        results_df = pd.DataFrame(results)
        results_df['timestamp'] = datetime.now()
        results_df.to_csv(config.tt_interest, encoding='utf-8-sig')
        if os.path.isfile(config.tt_interest):
            logger.info(f"Saved: {config.tt_interest}")
        else:
            logger.error(f"Failed to save: {config.tt_interest}")

        logger.info(f"Processed {len(results)} interest inputs. Output_file: {config.tt_interest}")
        return {"message": f"Processed {len(results)} interest inputs."}
    else:
        return {"message": "No results to save"}

def process_input_interest_check(input):
    """
    Send an estimate request filtered by location and interest_category_ids
    (no age_groups, no gender). Used to check which interest categories return data per country.
    """
    data = {
        "advertiser_id": advertiser_id,
        "objective_type": "REACH",
        "optimization_goal": "REACH",
        "placements": ["PLACEMENT_TIKTOK"],
        "location_ids": [input.location_id],
        "interest_category_ids": [input.interest_id]
    }
    try:
        response = get_audience_estimate(data)
        if not response:
            logger.warning(f"No valid response for interest-check input: {data}")
            return {
                "level": f"{level}",
                "name": input.name,
                "country_code": input.country_code,
                "geo_location": input.location_id,
                "interest_id": input.interest_id,
                "all_fields": data,
                "response": None,
                "lower_end": None,
                "upper_end": None,
                "user_count_stage": None
            }
        entry = {
            "level": f"{level}",
            "name": input.name,
            "country_code": input.country_code,
            "geo_location": input.location_id,
            "interest_id": input.interest_id,
            "all_fields": data,
            "response": response,
            "lower_end": response["data"]["user_count"]["lower_end"],
            "upper_end": response["data"]["user_count"]["upper_end"],
            "user_count_stage": response["data"]["user_count_stage"]
        }
        return entry
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

@app.post("/audience_estimate_interest_check/")
def audience_estimate_interest_check(input_list: InputListInterestCheck):
    results = []
    futures = []
    flush_every = 100

    def flush(rows):
        if not rows:
            return
        df = pd.DataFrame(rows)
        df['timestamp'] = datetime.now()
        write_header = not os.path.isfile(config.tt_interest_check)
        df.to_csv(config.tt_interest_check, mode='a', header=write_header, index=False, encoding='utf-8-sig')

    # Start fresh — remove any prior partial file so headers align
    if os.path.isfile(config.tt_interest_check):
        os.remove(config.tt_interest_check)

    buffer = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for inp in input_list.inputs:
            futures.append(executor.submit(process_input_interest_check, inp))
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing interest-check inputs", file=sys.stdout):
            res = future.result()
            if res:
                results.append(res)
                buffer.append(res)
                if len(buffer) >= flush_every:
                    flush(buffer)
                    buffer = []
    flush(buffer)
    logger.info("Finished processing all interest-check inputs.")

    if results:
        if os.path.isfile(config.tt_interest_check):
            logger.info(f"Saved: {config.tt_interest_check}")
        else:
            logger.error(f"Failed to save: {config.tt_interest_check}")
        logger.info(f"Processed {len(results)} interest-check inputs. Output_file: {config.tt_interest_check}")
        return {"message": f"Processed {len(results)} interest-check inputs."}
    else:
        return {"message": "No results to save"}

