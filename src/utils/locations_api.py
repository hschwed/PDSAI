from config.config import Config
import requests
import json
from src.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)

advertiser_id = config.advertiser_id
access_token = config.access_token

#################################### NOT USED - provides different ids; but does not restrict to targeting#########################

_LEVEL_NUM = {"COUNTRY": 1, "PROVINCE": 2, "DMA": 2, "CITY": 3, "DISTRICT": 3}
_GROUP     = {"COUNTRY": "countries", "PROVINCE": "provinces", "DMA": "DMA", "CITY": "cities", "DISTRICT": "cities"}


def get_location_ids_from_api(page_size: int = 1000) -> list[dict]:
    """
    Fetch all location IDs from GET /open_api/v1.3/search/region/.
    Returns the full list across all region levels with pagination.
    Response fields per item: region_id, region_name, region_level, country_code,
                              parent_id, area_type, support_below_18.
    """
    url = config.api_base_url + config.region_endpoint
    headers = {'Access-Token': access_token, 'Content-Type': 'application/json'}
    all_locations, page = [], 1

    while True:
        body = requests.get(url, headers=headers, params={
            'advertiser_id': advertiser_id,
            'page': page,
            'page_size': page_size,
        }).json()

        if body.get('code') != 0:
            logger.error(f"API error {body.get('code')}: {body.get('message')}")
            break

        data = body.get('data', {})
        batch = data.get('region_list', [])
        all_locations.extend(batch)

        total = data.get('page_info', {}).get('total_number', len(all_locations))
        if len(all_locations) >= total or len(batch) < page_size:
            break
        page += 1

    logger.info(f"Fetched {len(all_locations)} locations.")
    return all_locations


def save_locations_to_json(output_path: str = None):
    """
    Fetch all locations and save grouped by level to JSON.
    Output: {"countries": [...], "provinces": [...], "DMA": [...], "cities": [...]}
    Each item: id (int), name, level (int), country_code (where present), parent_id (where present).
    """
    if output_path is None:
        output_path = config.locations_json

    grouped: dict[str, list] = {"countries": [], "provinces": [], "DMA": [], "cities": []}

    for item in get_location_ids_from_api():
        level_str = item.get("region_level", "")
        group = _GROUP.get(level_str, "cities")

        out = {
            "id":    int(item["region_id"]),
            "name":  item["region_name"],
            "level": _LEVEL_NUM.get(level_str, 3),
        }
        if item.get("country_code"):
            out["country_code"] = item["country_code"]
        if item.get("parent_id") and item["parent_id"] not in ("0", 0):
            out["parent_id"] = int(item["parent_id"])

        grouped[group].append(out)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(grouped, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved to {output_path}: { {k: len(v) for k, v in grouped.items()} }")
    return grouped


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None)
    save_locations_to_json(output_path=parser.parse_args().output)
