"""
PART 2: Market information (Google search and news).  Owner: Role 2

Replace the body of get_signals with the real SerpApi code.
Keep the function name and the returned format exactly as it is below.
"""

from sample_data import SAMPLE_SIGNALS


def get_signals(idea, area):
    """Return a list of search and news results about the idea.

    Each item must look like:
    {"type": "news" or "search", "title": str, "snippet": str, "source": str, "link": str}
    """
    # TODO (Role 2): call SerpApi (engine=google and engine=google_news),
    # cache the responses, and return real results in the format above.
    return SAMPLE_SIGNALS
