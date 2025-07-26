import uvicorn
import pandas as pd
import time
import threading
from src.get_data.inputs import generate_inputs
from client import run_client

# Credentials
advertiser_id = '7381489555305775105'
secret = '01bebffff7dd4469b207a1622ad3892dfdf862a0'
app_id = '7384250931329630225'
auth_code = 'f57f9e8b140d03312509d43a9e70a96e65fde888' ## need to open link from App once reviewed; only valid for 1 hour, can only be used once
access_token = '7e4105012622ac077282d8a3e4bd6f937cbdec70'

def server():
    uvicorn.run("src.get_data.app:app", host="0.0.0.0", port=8000,log_level="info")

if __name__ == "__main__":
    generate_inputs()
    server_thread = threading.Thread(target=server)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(5)
    run_client()

#go to http://localhost:8000/docs to check
#http://localhost:8000/download_csv/ for download

