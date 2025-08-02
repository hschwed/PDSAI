from config.config import Config
import requests
import pandas as pd

config = Config()

advertiser_id = config.advertiser_id
access_token = config.access_token

####### THIS IS NO LONGER USED AS IT GIVES AN INCOMPLETE LIST OF LOCATIONS CONTRARY TO WHAT IS IN THE DOCUMENTATION ##################

def get_location_ids_from_api():  
    url = config.api_base_url + config.region_endpoint

    headers = {
        'Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    params = {
        'advertiser_id': advertiser_id,
    }

    response = requests.get(url, headers=headers, params=params)

    results = response.json()['data']['region_list'] #return json object of result of get request
    #geolist.to_csv('./config/specs/specs_explore/tiktok_regions_list.csv')

    results = pd.json_normalize(results)
    results = results.drop(['area_type','parent_id'],axis=1)