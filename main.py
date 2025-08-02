from config.config import Config
import uvicorn
import time
import threading
from src.get_data.inputs import generate_inputs
from client import run_client
from src.utils.logger import get_logger
import requests
from src.clean_data import clean_fb,clean_inst,clean_pop,clean_tt
from src.transform_data import transformations

config = Config()
logger = get_logger(__name__) # name of module, to show which module message came from

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

if __name__ == "__main__":
    logger.info("STARTING: DATA COLLECTION")
    logger.info("="*60)

    generate_inputs()

    server_thread = threading.Thread(target=server)
    server_thread.daemon = True
    server_thread.start()
    logger.info("Starting FastAPI server thread.")
    time.sleep(2)
    if server_up():
        logger.info("FastAPI server up and running.")
    else:
        logger.error("FastAPI server failed to respond.")
        raise RuntimeError("FastAPI server did not start or does not respond.")
    
    logger.info("Running client...")
    run_client()

    logger.info("STARTING: DATA CLEANING")
    logger.info("="*60)
    clean_fb.clean_facebook()
    clean_inst.clean_insta()
    clean_pop.clean_population()
    clean_tt.clean_tiktok()

    logger.info("STARTING: DATA TRANSFORMATION")
    logger.info("="*60)
    transformations.run_transform()


#go to http://localhost:8000/docs to check
#http://localhost:8000/download_csv/ for download

