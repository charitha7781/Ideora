
"""
PART 2: Market Information - Google Search and Google News
Owner: Role 2
"""

import os
import json
import hashlib
from pathlib import Path

from serpapi import GoogleSearch
from dotenv import load_dotenv


# Get the project folder path
BASE_DIR = Path(__file__).resolve().parent

# Load the API key from the .env file
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("SERPAPI_KEY")

# Create a folder to store cached API responses
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def get_cache_filename(engine, query):
    """Create a unique filename for each search."""

    search_id = hashlib.md5(
        f"{engine}_{query}".encode("utf-8")
    ).hexdigest()

    return CACHE_DIR / f"{engine}_{search_id}.json"


def get_cached_response(engine, query):
    """Read previously saved search results."""

    cache_file = get_cache_filename(engine, query)

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as file:
            print(f"Using cached {engine} results.")
            return json.load(file)

    return None


def save_response(engine, query, response):
    """Save API response in a JSON file."""

    cache_file = get_cache_filename(engine, query)

    with open(cache_file, "w", encoding="utf-8") as file:
        json.dump(response, file, indent=4, ensure_ascii=False)


def search_serpapi(engine, query):
    """Search SerpApi, using cache first."""

    # Check cache before making a paid API request
    cached_response = get_cached_response(engine, query)

    if cached_response is not None:
        return cached_response

    # Check API key
    if not API_KEY:
        raise ValueError(
            "SERPAPI_KEY is missing. Check your .env file."
        )

    print(f"Fetching {engine} results from SerpApi...")

    # Prepare SerpApi search parameters
    params = {
        "engine": engine,
        "q": query,
        "api_key": API_KEY
    }

    # Perform the search
    response = GoogleSearch(params).get_dict()

    # Check for API errors
    if "error" in response:
        raise RuntimeError(response["error"])

    # Save response for future use
    save_response(engine, query, response)

    return response


def get_signals(idea, area):
    """
    Collect Google Search and Google News results.

    Returns a list containing:
    type, title, snippet, source and link.
    """

    # Create search queries
    search_query = f"{idea} {area}"
    news_query = idea

    # Get Google Search results
    google_data = search_serpapi(
        "google",
        search_query
    )

    # Get Google News results
    news_data = search_serpapi(
        "google_news",
        news_query
    )

    signals = []

    # Process maximum 8 Google Search results
    organic_results = google_data.get("organic_results", [])

    for result in organic_results[:8]:

        title = result.get("title")
        link = result.get("link")

        # Skip results without required fields
        if not title or not link:
            continue

        signals.append({
            "type": "search",
            "title": title,
            "snippet": result.get("snippet", ""),
            "source": (
                result.get("source")
                or result.get("displayed_link", "")
            ),
            "link": link
        })

    # Process maximum 5 Google News results
    news_results = news_data.get("news_results", [])

    for result in news_results[:5]:

        title = result.get("title")
        link = result.get("link")

        # Skip results without required fields
        if not title or not link:
            continue

        # Extract source name
        source_data = result.get("source", "")

        if isinstance(source_data, dict):
            source = source_data.get("name", "")
        else:
            source = source_data

        signals.append({
            "type": "news",
            "title": title,
            "snippet": result.get("snippet", ""),
            "source": source,
            "link": link
        })

    return signals


# Test the function when this file is executed directly
if __name__ == "__main__":

    example_idea = "student-friendly cafe"
    example_area = "near RNS Institute of Technology, Bengaluru"

    try:
        results = get_signals(
            example_idea,
            example_area
        )

        print("\nMARKET INFORMATION RESULTS")
        print("=" * 50)

        print(json.dumps(
            results,
            indent=4,
            ensure_ascii=False
        ))

        print("\nTotal signals collected:", len(results))
                # Save results in an example JSON file
        example_file = BASE_DIR / "example_signals.json"

        with open(example_file, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4, ensure_ascii=False)

        print("Example JSON file saved successfully!")

    except Exception as error:
        print("\nError:", error)
