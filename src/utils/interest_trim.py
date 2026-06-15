from config.config import Config
import json
from src.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)


def trim_interest(input_path: str = None, output_path: str = None) -> list[dict]:
    """
    Reads interest.json and saves a trimmed version with only id and name fields.
    """
    if input_path is None:
        input_path = config.interest_json
    if output_path is None:
        output_path = config.interest_trim_json

    with open(input_path, 'r', encoding='utf-8') as f:
        categories = json.load(f)

    trimmed = [{"id": item["id"], "name": item["name"]} for item in categories]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trimmed, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(trimmed)} entries to {output_path}")
    return trimmed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Trim interest.json to id and name only.")
    parser.add_argument("--input", default=None, help="Input JSON file path (default: config.interest_json)")
    parser.add_argument("--output", default=None, help="Output JSON file path (default: config.interest_trim_json)")
    args = parser.parse_args()

    trim_interest(input_path=args.input, output_path=args.output)
