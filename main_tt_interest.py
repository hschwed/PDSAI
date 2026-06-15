from config.config import Config
import uvicorn
import time
import threading
from src.get_data.inputs import generate_input_interest
from client import run_client_interest
from src.utils.logger import get_logger
import requests
from src.clean_data import clean_pop,clean_tt
from src.transform_data import transformations

config = Config()
logger = get_logger(__name__)

def server():
    uvicorn.run("src.get_data.app:app", host="0.0.0.0", port=8000,log_level="info")

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

# keep only selected ids, selected top level (2-digit) unless too broad
INTEREST_IDS = [
    "20111100",      # Parenting, App                    (childcare)   -> used
    "13",            # Financial Services (top-level) (finance)   -> used (matches "Financial Services" by name)
    "20109102",      # Healthy Lifestyle , App           (healthcare)  -> used
    "24",            # Business Services            (business)    -> used
    "10",            # Education                    (education)   -> used
    "20109101",       # Medical Care                 (healthcare)  -> used
    "17",        # Travel
    "19",        # Pets
    "12",        # Baby & Kids Products
    "27",        # Food & Beverage
    "29101",     # Health & Wellness
    "20109"    # Health & Fitness
]

# keep only top level, no children interest ids
INTEREST_IDS_ALL_TOP_LEVEL = [
    "10",        # Education                    
    "11",        # Vehicles & Transportation
    "12",        # Baby & Kids Products
    "13",        # Financial Services
    "14",        # Beauty & Personal Care
    "15",        # Tech & Electronics
    "16",        # Appliances
    "17",        # Travel
    "18",        # Household Products
    "19",        # Pets
    "20",        # Apps
    "21",        # Home Improvement
    "22",        # Apparel 
    "23",        # News & Entertainment
    "24",        # Business Services
    "25",        # Games
    "26",        # Life Services (flowers, photography, used goods, etc)
    "27",        # Food & Beverage
    "28",        # Sports & Outdoors
    "29"        # E Commerce (Non app)
]

if __name__ == "__main__":
    logger.info("STARTING: INTEREST DATA COLLECTION")
    logger.info("="*60)

    generate_input_interest(INTEREST_IDS)

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

    logger.info("Running interest client...")
    run_client_interest()

    logger.info("STARTING: DATA CLEANING")
    logger.info("="*60)
    clean_pop.clean_population()
    clean_tt.clean_tiktok_interest()

    if config.level == "country":
        logger.info("STARTING: DATA TRANSFORMATION")
        logger.info("="*60)
        transformations.run_transform_interest()

    logger.info("="*60)
    logger.info("FINISHED")
