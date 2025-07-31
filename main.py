import uvicorn
import pandas as pd
import time
import threading
from src.get_data.inputs import generate_inputs
from client import run_client

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

