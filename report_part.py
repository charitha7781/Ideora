"""
PART 3: The AI report writer.  Owner: Role 3

Replace the body of build_report with the real AI code.
Keep the function name and the returned format exactly as it is below.
"""

from sample_data import SAMPLE_REPORT


def build_report(idea, area, competitors, signals):
    """Return the report as a dictionary.

    It must look like:
    {
      "summary": str,
      "competition": {"count": int, "average_rating": float, "notes": str},
      "customer_feedback": [str, ...],
      "gaps": [str, ...],
      "score": int (1 to 10),
      "score_reason": str,
      "sources": [{"title": str, "link": str}, ...],
    }
    """
    # TODO (Role 3): work out the numbers, send everything to the AI model with
    # a clear prompt, read its JSON answer, and return the report.
    return SAMPLE_REPORT
