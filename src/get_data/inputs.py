
from config.config import Config
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

age = ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
gender = ["GENDER_FEMALE", "GENDER_MALE"]
age_gender_combined = list(itertools.product(gender, age))

################# PREPARING INPUT ######################
def generate_location_inputs(region_list, region_type):
    """
    Generate JSON-serializable input list from region list and age/gender combinations
    """
    entries = []
    for loc in region_list:
        for g, a in age_gender_combined:
            entry = {
                "name": loc.get("name", None),
                "country_code": str(loc.get("country_code", None)),
                "location_id": str(loc["id"]),
                "gender": g,
                "age": a
            }
            entries.append(entry)
    logger.info(f"{region_type}: {len(entries)} entries generated.")
    return {"inputs": entries}

def generate_inputs():
    logger.info("Generating inputs...")
    with open(config.locations_json, encoding="utf-8") as f:
        locations = json.load(f)

    base_path = config.input_path + "input"

    output_map = {
        "countries": (f"{base_path}_country.json", locations.get("countries", [])),
        "provinces": (f"{base_path}_province.json", locations.get("provinces", [])),
        "DMA": (f"{base_path}_dma.json", locations.get("DMA", [])),
        "cities": (f"{base_path}_city.json", locations.get("cities", []))
    }
  

    for level, (filepath, region_list) in output_map.items():
        inputs = generate_location_inputs(region_list, level)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(inputs, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {level} input JSON to: {filepath}. File has {len(inputs.get('inputs', []))} entries.")
        except Exception as e:
            logger.error(f"Error saving {level} input JSON: {e}")

    logger.info("All location inputs generated and saved successfully.")

