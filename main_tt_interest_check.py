from config.config import Config
import uvicorn
import time
import threading
import json
from src.get_data.inputs import generate_input_interest_check
from client import run_client_interest_check
from src.utils.logger import get_logger
import requests

config = Config()
logger = get_logger(__name__)

def server():
    uvicorn.run("src.get_data.app:app", host="0.0.0.0", port=8000, log_level="info")

def server_up(url="http://localhost:8000/docs"):
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Credentials
advertiser_id = config.advertiser_id
access_token = config.access_token

if not advertiser_id or not access_token:
    logger.error("Missing ADVERTISER_ID or ACCESS_TOKEN in .env")
    raise EnvironmentError("Missing required environment variables.")
else:
    logger.info("Environment variables loaded successfully.")

def load_interest_ids():
    """Read all interest IDs from interest.json."""
    with open(config.interest_json, encoding="utf-8") as f:
        interests = json.load(f)
    ids = [str(item["id"]) for item in interests if "id" in item]
    logger.info(f"Loaded {len(ids)} interest IDs from {config.interest_json}.")
    return ids

if __name__ == "__main__":
    logger.info("STARTING: INTEREST CATEGORY DATA-AVAILABILITY CHECK")
    logger.info("="*60)

    interest_ids = load_interest_ids()
    generate_input_interest_check(interest_ids)

    server_thread = threading.Thread(target=server)
    server_thread.daemon = True
    server_thread.start()
    logger.info("Starting FastAPI server thread.")
    time.sleep(5)
    if server_up():
        logger.info("FastAPI server up and running.")
    else:
        logger.error("FastAPI server failed to respond.")
        raise RuntimeError("FastAPI server did not start or does not respond.")

    logger.info("Running interest-check client...")
    run_client_interest_check()

    logger.info("="*60)
    logger.info("FINISHED")
