"""
Fake example data in the SHARED DATA FORMAT.

Everything here is made up for testing only. It lets the screen (app.py) work
before the real parts are ready. Do NOT show this as real results in the demo.
"""

SAMPLE_COMPETITORS = [
    {
        "name": "Example Cafe One",
        "rating": 4.3,
        "reviews_count": 210,
        "address": "12 Main Road, Bengaluru",
        "link": "https://example.com/cafe-one",
    },
    {
        "name": "Example Cafe Two",
        "rating": 3.9,
        "reviews_count": 85,
        "address": "45 College Road, Bengaluru",
        "link": "https://example.com/cafe-two",
    },
    {
        "name": "Example Cafe Three",
        "rating": 4.6,
        "reviews_count": 340,
        "address": "8 Lake View Street, Bengaluru",
        "link": "https://example.com/cafe-three",
    },
]

SAMPLE_SIGNALS = [
    {
        "type": "news",
        "title": "Example news: cafes see more student visitors",
        "snippet": "Made-up snippet for testing.",
        "source": "Example News",
        "link": "https://example.com/news-1",
    },
    {
        "type": "search",
        "title": "Example page: what students look for in a cafe",
        "snippet": "Made-up snippet for testing.",
        "source": "Example Blog",
        "link": "https://example.com/blog-1",
    },
]

SAMPLE_REPORT = {
    "summary": "This is a made-up example report. There are a few cafes nearby, "
    "and customers mention slow service and little seating.",
    "competition": {
        "count": 3,
        "average_rating": 4.3,
        "notes": "Example only: ratings are good, so a new cafe must stand out.",
    },
    "customer_feedback": [
        "Example complaint: service is slow at busy hours",
        "Example praise: good coffee at fair prices",
    ],
    "gaps": [
        "Example gap: no cafe with long opening hours and quiet study space",
    ],
    "score": 7,
    "score_reason": "Example only: demand looks fine, but competition is real.",
    "sources": [
        {"title": "Example Cafe One", "link": "https://example.com/cafe-one"},
        {"title": "Example news: cafes see more student visitors", "link": "https://example.com/news-1"},
    ],
}
