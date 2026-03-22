"""
Classify TikTok interest categories into target topics using LLM zero-shot classification.

Approach: GPT-3.5-turbo chat completion
  - Sends batches of ~20 interest names per request
  - The model reasons about topical relevance (not just word similarity)
  - Each interest is assigned exactly one best-fitting topic
  - Interests that don't fit any topic are excluded from output
"""

import json
from config.config import Config
from src.utils.logger import get_logger
from openai import OpenAI

config = Config()
logger = get_logger(__name__)

CATEGORIES = ["business", "economy", "education", "healthcare", "childcare"]
BATCH_SIZE = 20

SYSTEM_PROMPT = """You are a classifier. Given a list of TikTok advertising interest category names, determine which ones are relevant to the following topics: {categories}.

Rules:
- An interest is "relevant" if it meaningfully represents or relates to the category (e.g. "Infant Formula" -> childcare, "Stock Trading" -> economy, "E-commerce" -> business).
- An interest can only match one category. Assign to the best fitting category if it could relate to multiple.
- Only include interests that clearly fit at least one category. Skip the rest.

You MUST respond with a JSON object in this exact format:
{{"matches": [{{"id": "original id", "name": "original name", "category": "matching category"}}]}}

If no interests match, respond with:
{{"matches": []}}"""


def _classify_batch(client: OpenAI, batch: list[dict], categories: list[str]) -> list[dict]:
    """Send one batch of interests to GPT-3.5-turbo for classification."""
    prompt = json.dumps(batch, ensure_ascii=False)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(categories=", ".join(categories))},
            {"role": "user", "content": prompt},
        ],
    )

    content = response.choices[0].message.content
    logger.debug(f"Raw response: {content[:200]}")
    parsed = json.loads(content)

    if isinstance(parsed, dict):
        results = parsed.get("matches", [])
    elif isinstance(parsed, list):
        results = parsed
    else:
        logger.warning(f"Unexpected response format, skipping batch")
        return []

    if not isinstance(results, list):
        logger.warning(f"'matches' is not a list, skipping batch")
        return []

    return results


def match_interests(
    input_path: str = None,
    output_path: str = None,
    categories: list[str] = None,
    batch_size: int = BATCH_SIZE,
) -> list[dict]:
    """
    Load interest_trim.json, classify each interest via LLM,
    and save matched interests with their single best-fitting topic.
    """
    if input_path is None:
        input_path = config.interest_trim_json
    if output_path is None:
        output_path = config.interest_matched_json
    if categories is None:
        categories = CATEGORIES

    if not config.openai_api_key:
        raise EnvironmentError("Missing OPENAI_API_KEY in .env")

    client = OpenAI(api_key=config.openai_api_key)

    with open(input_path, "r", encoding="utf-8") as f:
        interests = json.load(f)

    logger.info(f"Classifying {len(interests)} interests into topics: {categories}")

    matched = []
    for i in range(0, len(interests), batch_size):
        batch = interests[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(interests) + batch_size - 1) // batch_size
        logger.info(f"Processing batch {batch_num}/{total_batches}...")

        results = _classify_batch(client, batch, categories)

        # validate topic in results
        for item in results:
            if item.get("category") in categories:
                matched.append(item)

    matched.sort(key=lambda x: (x["category"], x["name"]))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(matched, f, indent=2, ensure_ascii=False)

    counts = {}
    for m in matched:
        counts[m["category"]] = counts.get(m["category"], 0) + 1
    logger.info(f"Saved {len(matched)} matched entries to {output_path}. Category counts: {counts}")

    return matched


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify interests into topics via LLM.")
    parser.add_argument("--input", default=None, help="Input JSON (default: config.interest_trim_json)")
    parser.add_argument("--output", default=None, help="Output JSON (default: config.interest_matched_json)")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"Items per API call (default: {BATCH_SIZE})")
    parser.add_argument("--categories", nargs="+", default=CATEGORIES, help="Target category labels")
    args = parser.parse_args()

    match_interests(
        input_path=args.input,
        output_path=args.output,
        batch_size=args.batch_size,
        categories=args.categories,
    )
