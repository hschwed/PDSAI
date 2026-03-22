from config.config import Config
import requests
import json
from src.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)

advertiser_id = config.advertiser_id
access_token = config.access_token


def get_general_interest_from_api() -> list[dict]:
    """
    Fetch all general_interest targeting categories from TikTok's /tool/interest_category/ endpoint.

    Returns the full list including parent and child categories. Each entry has:
        id, name, level, children_ids, supported_special_industries

    Args:
        placement: Ad placement to filter categories for. Default: "PLACEMENT_TIKTOK".

    Returns:
        List of dicts for all general_interest categories.
    """
    url = config.api_base_url + config.interest_endpoint
    headers = {
        'Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    params = {
        'advertiser_id': advertiser_id,
        'targeting_type': 'INTEREST_AND_BEHAVIOR',
        'version': 2
    }

    response = requests.get(url, headers=headers, params=params)
    body = response.json()

    if body.get('code') != 0:
        logger.error(f"API error {body.get('code')}: {body.get('message')}")
        return []

    data = body.get('data', {})
    logger.info(f"Raw data keys: {list(data.keys())}")

    general_interest = data.get('general_interest', {}).get('list_result', [])

    logger.info(f"Fetched {len(general_interest)} general_interest categories.")
    return general_interest


def save_general_interest_to_json(output_path: str = None) -> list[dict]:
    """Fetch general_interest categories and save to JSON file."""
    if output_path is None:
        output_path = config.interest_json

    categories = get_general_interest_from_api()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(categories)} general_interest categories to {output_path}")
    return categories


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch TikTok general_interest categories via API.")
    parser.add_argument("--output", default=None, help="Output JSON file path (default: config.interest_json)")
    args = parser.parse_args()

    save_general_interest_to_json(output_path=args.output)
