from config.config import Config
import requests
import json
import time
from src.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)

def run_client():
    time.sleep(5) # to start server
    # Load the generated input file and send request
    with open(config.input_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    logger.info("Running client request...")
    response = requests.post("http://localhost:8000/audience_estimate/", json=payload)
    
    logger.info(f"Client received response: {response.status_code}")

    #print(response.json())
