# Tools for reading/writing files and folders
import json
import os

# Loads the secret key from the .env file
from dotenv import load_dotenv

# The official SerpApi package (we use it to call Google Maps)
from serpapi import GoogleSearch

# Read the .env file so SERPAPI_KEY becomes available
load_dotenv()

# Get the SerpApi key from the .env file (never write the key in code)
API_KEY = os.getenv("SERPAPI_KEY")

# Folder where we save responses so we don't waste free credits
CACHE_FOLDER = "cache"

# Make the cache folder if it does not exist yet
os.makedirs(CACHE_FOLDER, exist_ok=True)


def make_cache_path(query):
    # Turn the search text into a safe file name
    safe_name = "".join(c if c.isalnum() else "_" for c in query.lower())
    # Return the full path like cache/cafe_near_rns.json
    return os.path.join(CACHE_FOLDER, safe_name + ".json")


def read_cache(query):
    # Find where the saved file for this search should be
    path = make_cache_path(query)
    # If we saved this search before, load and return it (no credits used)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Otherwise there is nothing saved yet
    return None


def save_cache(query, data):
    # Find the file path for this search
    path = make_cache_path(query)
    # Save the SerpApi response as JSON so we can reuse it later
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_review_snippets(data_id):
    # Use a different cache name so reviews never mix with place searches
    cache_key = "reviews " + data_id

    # Look in the cache first (free)
    results = read_cache(cache_key)

    # If nothing is saved, ask SerpApi (uses 1 credit)
    if results is None:
        params = {
            "engine": "google_maps_reviews",  # the reviews engine
            "data_id": data_id,               # which place we want reviews for
            "sort_by": "newestFirst",         # most recent reviews first
            "hl": "en",                       # English
            "api_key": API_KEY,               # our secret key
        }
        # Send the request
        results = GoogleSearch(params).get_dict()
        # If SerpApi gave an error, show it and return an empty list
        if "reviews" not in results:
            print("Reviews problem:", results.get("error", "no reviews in response"))
            return []
        # Save it so next time it is free
        save_cache(cache_key, results)

    # Collect up to 5 non-empty review texts
    snippets = []
    for review in results.get("reviews", []):
        # Some reviews have only stars and no text, skip those
        text = review.get("snippet")
        if text:
            snippets.append(text)
        if len(snippets) == 5:
            break
    return snippets


def get_competitors(idea, area):
    # Build the search text, e.g. "cafe near RNS Institute of Technology Bengaluru"
    query = f"{idea} near {area}"

    # Look in the cache first so we don't spend credits twice
    results = read_cache(query)

    # If nothing is saved, ask SerpApi (this uses 1 credit)
    if results is None:
        # Settings for the Google Maps search
        params = {
            "engine": "google_maps",  # use Google Maps
            "type": "search",         # a normal place search
            "q": query,               # what to search for
            "hl": "en",               # English results
            "api_key": API_KEY,       # our secret key
        }
        # Send the request and get the answer as a Python dictionary
        results = GoogleSearch(params).get_dict()

        # If Google Maps found nothing, return an empty list instead of crashing
        if "error" in results and "local_results" not in results:
            if "hasn't returned any results" in results["error"]:
                # Save it so we don't pay for the same empty search again
                save_cache(query, results)
                return []
            # Any other error (bad key, no credits) should still stop with a message
            raise Exception(f"SerpApi error: {results['error']}")

        # Save the answer so next time it is free
        save_cache(query, results)

    # Get the list of places (empty list if the key is missing)
    places = results.get("local_results", [])

    # If Maps found exactly one place, it comes in a different field
    if not places and "place_results" in results:
        places = [results["place_results"]]

    # This list will hold our cleaned places
    competitors = []

    # Go through at most 10 places (index tells us the position: 0, 1, 2...)
    for index, place in enumerate(places[:10]):
        # Start with an empty record for this place
        item = {}

        # Copy each field only if SerpApi really gave it
        if "title" in place:
            item["name"] = place["title"]
        if "rating" in place:
            item["rating"] = place["rating"]
        if "reviews" in place:
            item["reviews_count"] = place["reviews"]
        if "address" in place:
            item["address"] = place["address"]

        # Use the Google Maps link if available
        if "place_id" in place:
            item["link"] = "https://www.google.com/maps/place/?q=place_id:" + place["place_id"]

        # For only the top 3 places, also collect a few review texts
        if index < 3 and "data_id" in place:
            snippets = get_review_snippets(place["data_id"])
            # Add them only if we really got some
            if snippets:
                item["review_snippets"] = snippets

        # Only keep places that have a name
        if "name" in item:
            competitors.append(item)

    # Return the list in the shared data format
    return competitors


# Tiny test: this only runs when you run this file directly
if __name__ == "__main__":
    # Example idea and area for the test
    idea = "student-friendly cafe"
    area = "RNS Institute of Technology, Bengaluru"
    # Get the cleaned list (reads from cache, so 0 credits if already saved)
    result = get_competitors(idea, area)
    # Show how many places we found
    print("Found", len(result), "competitors")
    # Show how many of them have review snippets
    print("With review snippets:", sum(1 for c in result if "review_snippets" in c))
    # Write the full list into the example file, perfectly formatted
    with open("example_competitors.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    # Confirm the file was saved
    print("Saved example_competitors.json")