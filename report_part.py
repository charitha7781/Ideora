"""
PART 3: The AI report writer.  Owner: Role 3

build_report(idea, area, competitors, signals) -> dict in the shared format:
{
  "summary": str,
  "competition": {"count": int, "average_rating": float, "notes": str},
  "customer_feedback": [str, ...],
  "gaps": [str, ...],
  "score": int (1 to 10),
  "score_reason": str,
  "sources": [{"title": str, "link": str}, ...]
}

competitors : list from maps_part.py  (name, rating, reviews_count, link; optional review_snippets)
signals     : from signals_part.py. A list of items with a "type" (news / search),
              or a dict {"search": [...], "news": [...], "trends": {...}}.
Needs:  AI_PROVIDER and AI_API_KEY in your .env (see .env.example)
        gemini -> pip install google-genai | anthropic -> pip install anthropic
        openai / groq / openrouter -> only needs: requests
"""
import json
import os

try:                                   # optional: load keys from a .env file
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

INCLUDE_EXTRAS = False   # set True to also add "risks" and "market_interest" keys


def _get(item, *keys, default=None):
    """Read the first key that exists (accepts slightly different field names)."""
    for k in keys:
        if isinstance(item, dict) and item.get(k) not in (None, ""):
            return item[k]
    return default

# ---------------------------------------------------------------------------
# STEP 0: tidy the inputs
# ---------------------------------------------------------------------------
def normalize_signals(signals):
    """Accepts the team's plain list (each item has a "type": news / search /
    trends) or a dict {"search": [...], "news": [...], "trends": {...}}."""
    out = {"search": [], "news": [], "trends": None}
    if isinstance(signals, dict):
        out["search"] = signals.get("search") or signals.get("search_results") or []
        out["news"] = signals.get("news") or []
        out["trends"] = signals.get("trends")
        return out
    for item in signals or []:
        kind = str(_get(item, "type", default="search")).lower()
        if kind == "news":
            out["news"].append(item)
        elif kind in ("trend", "trends"):
            out["trends"] = item
        else:
            out["search"].append(item)
    return out

# ---------------------------------------------------------------------------
# STEP 1: simple numbers (plain Python, no AI)
# ---------------------------------------------------------------------------
def compute_trend(trends):
    unknown = {"direction": "unknown", "change_percent": None, "data_points": 0}
    if not trends:
        return unknown
    points = trends
    if isinstance(trends, dict):
        if "direction" in trends:
            return trends
        points = (trends.get("interest_over_time") or {}).get("timeline_data") \
                 or trends.get("timeline_data") or []
    values = []
    for p in points:
        try:
            if p.get("values"):
                values.append(float(p["values"][0].get("extracted_value", 0)))
            elif "value" in p:
                values.append(float(p["value"]))
        except (TypeError, ValueError, AttributeError):
            pass
    n = len(values)
    if n < 6:
        return {**unknown, "data_points": n}
    third = max(1, n // 3)
    first = sum(values[:third]) / third
    last = sum(values[-third:]) / third
    if first == 0:
        change, direction = None, ("rising" if last > 0 else "flat")
    else:
        change = round((last - first) / first * 100, 1)
        direction = "rising" if change >= 15 else "falling" if change <= -15 else "flat"
    return {"direction": direction, "change_percent": change, "data_points": n}


def compute_numbers(competitors, trends=None):
    ratings, total_reviews = [], 0
    for c in competitors or []:
        try:
            ratings.append(float(_get(c, "rating")))
        except (TypeError, ValueError):
            pass
        try:
            total_reviews += int(_get(c, "reviews", "reviews_count", default=0))
        except (TypeError, ValueError):
            pass
    count = len(competitors or [])
    avg = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
    level = "low" if count <= 3 else "medium" if count <= 8 else "high"
    return {
        "competitor_count": count,
        "average_rating": avg,
        "rated_competitors": len(ratings),
        "total_reviews": total_reviews,
        "competition_level": level,
        "search_interest_trend": compute_trend(trends),
    }


def collect_sources(competitors, sig):
    """Every link we were given. Used to block invented links."""
    out, seen = [], set()
    def add(link, title):
        if link and link not in seen:
            seen.add(link)
            out.append({"title": str(title), "link": link})
    for c in competitors or []:
        add(_get(c, "link", "url", "website"), _get(c, "name", "title", default="Place"))
    for s in sig["search"]:
        add(_get(s, "link", "url"), _get(s, "title", default="Search result"))
    for s in sig["news"]:
        add(_get(s, "link", "url"), _get(s, "title", default="News article"))
    return out

# ---------------------------------------------------------------------------
# STEP 2: the prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a careful business analyst writing a short report for a beginner who has a startup idea.

STRICT RULES
1. Use ONLY the information in the DATA section. Never invent facts, places, numbers, reviews or links. If something is not in the data, say "not enough data".
2. Write in simple words a beginner can understand. Short sentences. No jargon.
3. The DATA has: competitors (Google Maps: ratings, review counts, review snippets), search_results (Google Search), news (Google News) and trend (Google Trends: rising, flat or falling interest). Use all of them. Mention the trend and any useful news briefly in the summary.
4. In "customer_feedback", write 3 to 6 short sentences about what customers say in the competitor reviews. Start each one with "Complaint:" or "Praise:". If the competitors have no review text, use only what the search results and news say about customers, and say clearly that review details were not available.
5. In "gaps", list things customers want that nobody nearby seems to offer.
6. Give a score from 1 to 10 (10 = very promising) and a short reason (1-2 sentences).
7. In "sources", list only links that appear in the DATA, each with a title and link.
8. Use the NUMBERS exactly as given. Do not recalculate them.

OUTPUT FORMAT
Reply with ONE valid JSON object and nothing else (no markdown, no code fences, no extra text):
{
  "summary": "2-3 simple sentences about the idea",
  "competition": {"count": <whole number>, "average_rating": <number>, "notes": "1-2 simple sentences"},
  "customer_feedback": ["Complaint: ...", "Praise: ..."],
  "gaps": ["..."],
  "score": <whole number 1-10>,
  "score_reason": "...",
  "sources": [{"title": "...", "link": "..."}]
}""" 

EXTRAS_PROMPT = """
Also add these two keys to the JSON:
  "risks": ["short risk 1", "short risk 2"],
  "market_interest": {"trend": "rising|flat|falling|unknown", "notes": "1-2 simple sentences"}"""


def make_prompt(idea, area, competitors, sig, numbers):
    data = {
        "idea": idea,
        "area": area,
        "numbers": numbers,
        "competitors": competitors,
        "search_results": sig["search"][:8],
        "news": sig["news"][:8],
        "trend": numbers["search_interest_trend"],
    }
    text = "DATA (use only this):\n" + json.dumps(data, indent=2, ensure_ascii=False)
    return text + (EXTRAS_PROMPT if INCLUDE_EXTRAS else "")

# ---------------------------------------------------------------------------
# STEP 3: call the AI
# ---------------------------------------------------------------------------
OPENAI_STYLE = {   # providers that use the same "chat completions" web format
    "openai":     ("https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    "groq":       ("https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", ""),
}


def call_ai(system, user):
    """Send the prompt to the AI chosen in .env and return its text answer.

    .env settings:
      AI_PROVIDER = gemini | anthropic | openai | groq | openrouter   (default gemini)
      AI_API_KEY  = the key for that provider
      REPORT_MODEL = optional model name (model names change, so set it if you get a 404)
    """
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    key = (os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY")
           or os.getenv("GOOGLE_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("REPORT_MODEL")

    if provider == "gemini":
        from google import genai
        from google.genai import types
        resp = genai.Client(api_key=key).models.generate_content(
            model=model or "gemini-2.5-flash",
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system, temperature=0.2,
                response_mime_type="application/json"))
        return resp.text

    if provider == "anthropic":
        import anthropic
        msg = anthropic.Anthropic(api_key=key).messages.create(
            model=model or "claude-sonnet-5-5", max_tokens=1800, temperature=0.2,
            system=system, messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

    if provider in OPENAI_STYLE:
        import requests
        url, default_model = OPENAI_STYLE[provider]
        model = model or default_model
        if not model:
            raise ValueError("Set REPORT_MODEL in .env for this provider")
        body = {"model": model, "temperature": 0.2,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}]}
        if provider in ("openai", "groq"):
            body["response_format"] = {"type": "json_object"}
        r = requests.post(url, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    raise ValueError(f"Unknown AI_PROVIDER: {provider}")

# ---------------------------------------------------------------------------
# STEP 4: read + check the JSON
# ---------------------------------------------------------------------------
def parse_and_check(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    data = json.loads(text[start:end + 1])
    for key in ("summary", "competition", "customer_feedback", "gaps",
                "score", "score_reason", "sources"):
        if key not in data:
            raise ValueError(f"missing key: {key}")
    data["score"] = max(1, min(10, int(data["score"])))
    for key in ("customer_feedback", "gaps", "sources"):
        if not isinstance(data[key], list):
            raise ValueError(f"{key} must be a list")
    return data

# ---------------------------------------------------------------------------
# STEP 5: fallback report (numbers only)
# ---------------------------------------------------------------------------
def fallback_report(idea, area, numbers, sources):
    n, avg = numbers["competitor_count"], numbers["average_rating"]
    trend = numbers["search_interest_trend"]["direction"]
    score = 6
    if numbers["competition_level"] == "high":
        score -= 2
    elif numbers["competition_level"] == "low":
        score += 1
    if avg >= 4.5:
        score -= 1
    elif 0 < avg < 4.0:
        score += 1
    if trend == "rising":
        score += 1
    elif trend == "falling":
        score -= 1
    if n == 0:
        score = 5
    score = max(1, min(10, score))
    avg_text = f"{avg} out of 5" if avg else "not available"
    trend_text = {"rising": "Search interest is going up.", "falling": "Search interest is going down.",
                  "flat": "Search interest is steady.", "unknown": "There is not enough trend data."}[trend]
    return {
        "summary": f"We found {n} similar businesses near {area}. Their average rating is {avg_text}. {trend_text}",
        "competition": {"count": n, "average_rating": avg,
                        "notes": f"Competition looks {numbers['competition_level']} based on the number of places found."},
        "customer_feedback": ["Not enough data: the AI summary of customer reviews was not available."],
        "gaps": [],
        "score": score,
        "score_reason": "Score is based only on competitor count, ratings and search trend.",
        "sources": sources,
    }

# ---------------------------------------------------------------------------
# MAIN FUNCTION  (keep this name: app.py calls it)
# ---------------------------------------------------------------------------
def build_report(idea, area, competitors, signals, ai_call=None):
    ai_call = ai_call or call_ai
    sig = normalize_signals(signals)
    numbers = compute_numbers(competitors, sig["trends"])
    sources = collect_sources(competitors, sig)
    prompt = make_prompt(idea, area, competitors, sig, numbers)

    report, error = None, None
    for attempt in range(2):                       # first try + ONE retry
        extra = "" if attempt == 0 else (
            f"\n\nYour previous answer was not valid ({error}). "
            "Reply again with ONLY the JSON object, nothing else.")
        try:
            report = parse_and_check(ai_call(SYSTEM_PROMPT, prompt + extra))
            break
        except Exception as e:
            error, report = str(e), None

    if report is None:
        report = fallback_report(idea, area, numbers, sources)
    else:
        allowed = {s["link"] for s in sources}
        cleaned = []
        for s in report["sources"]:
            link = _get(s, "link", "url")
            if link in allowed:
                cleaned.append({"title": str(_get(s, "title", default=link)), "link": link})
        report["sources"] = cleaned or sources
        # numbers always come from Python, not the AI
        if not isinstance(report["competition"], dict):
            report["competition"] = {"notes": ""}
        report["competition"]["count"] = numbers["competitor_count"]
        report["competition"]["average_rating"] = numbers["average_rating"]
        report["competition"].setdefault("notes", "")

    if INCLUDE_EXTRAS:
        report.setdefault("risks", [])
        report["market_interest"] = {
            "trend": numbers["search_interest_trend"]["direction"],
            "notes": (report.get("market_interest") or {}).get("notes", "")}
    return report


if __name__ == "__main__":
    # Quick real-AI test with the team's fake data (needs ANTHROPIC_API_KEY)
    from sample_data import SAMPLE_COMPETITORS, SAMPLE_SIGNALS
    print(json.dumps(build_report("A student-friendly cafe",
                                  "near RNS Institute of Technology, Bengaluru",
                                  SAMPLE_COMPETITORS, SAMPLE_SIGNALS),
                     indent=2, ensure_ascii=False))
