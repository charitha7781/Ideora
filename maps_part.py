"""
PART 1: Nearby businesses (Google Maps).  Owner: Role 1

Replace the body of get_competitors with the real SerpApi code.
Keep the function name and the returned format exactly as it is below.
"""

from sample_data import SAMPLE_COMPETITORS


def get_competitors(idea, area):
    """Return a list of nearby similar businesses.

    Each item must look like:
    {"name": str, "rating": float, "reviews_count": int, "address": str, "link": str}
    """
    # TODO (Role 1): call SerpApi (engine=google_maps), cache the response,
    # and return real results in the format above.
    return SAMPLE_COMPETITORS
