from config.config import Config
import requests
import json
import time
from src.utils.logger import get_logger
import os

config = Config()
logger = get_logger(__name__)

def run_client():
    time.sleep(5) # to start server
    # Load the generated input file and send request
    if not os.path.isfile(config.input_json):
        logger.error(f"Input file not found: {config.input_json}")
        return

    with open(config.input_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    level = config.level
    logger.info(f"Running client request for {level}-level input...")

    response = requests.post("http://localhost:8000/audience_estimate/", json=payload)

    logger.info(f"Client received response: {response.status_code}")
    logger.info(f"Response content: {response.text}")

    #print(response.json())
