import requests
import json
import time

def run_client():
    time.sleep(5) # to start server
    # Load the generated input file
    with open("input_json.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    response = requests.post("http://localhost:8000/audience_estimate/", json=payload)

    print(response.status_code)
    print(response.json())
