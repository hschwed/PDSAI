import os
import yaml
from dotenv import load_dotenv

class Config:
    def __init__(self, config_path="config/config.yaml"):
        load_dotenv()

        with open(config_path, "r") as file:
            self._config = yaml.safe_load(file)

        self.advertiser_id = os.getenv("ADVERTISER_ID")
        self.access_token = os.getenv("ACCESS_TOKEN")

        if not self.advertiser_id or not self.access_token:
            raise EnvironmentError("Missing ADVERTISER_ID or ACCESS_TOKEN in .env")

    @property
    def api_base_url(self):
        return self._config["api"]["base_url"]

    @property
    def region_endpoint(self):
        return self._config["api"]["region_endpoint"]
    
    @property
    def estimates_endpoint(self):
        return self._config["api"]["estimates_endpoint"]
    
    @property
    def max_workers(self):
        return self._config["api"].get("max_workers", 5)

    @property
    def log_file(self):
        return self._config["paths"]["log_file"]

    @property
    def input_csv(self):
        return self._config["paths"]["input_csv"]

    @property
    def input_json(self):
        return self._config["paths"]["input_json"]

    @property
    def location_ids(self):
        return self._config["paths"]["location_ids"]

    @property
    def tt_output(self):
        return self._config["paths"]["tt_output"]
    @property
    def tt_clean(self):
        return self._config["paths"]["tt_clean"]
    @property
    def tt_final(self):
        return self._config["paths"]["tt_final"]

    @property
    def fb(self):
        return self._config["paths"]["fb_csv"]
    @property
    def fb_clean(self):
        return self._config["paths"]["fb_clean"]
    @property
    def fb_final(self):
        return self._config["paths"]["fb_final"]
       
    @property
    def insta(self):
        return self._config["paths"]["insta_csv"]
    @property
    def insta_clean(self):
        return self._config["paths"]["insta_clean"]
    @property
    def insta_final(self):
        return self._config["paths"]["insta_final"]
      
    @property
    def pop(self):
        return self._config["paths"]["pop_csv"]

    @property
    def pop_clean(self):
        return self._config["paths"]["pop_clean"]
    @property
    def pop_final(self):
        return self._config["paths"]["pop_final"]