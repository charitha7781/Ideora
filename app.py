"""
PART 4: The screen.  Owner: Role 4

Run it with:  streamlit run app.py
It calls the three parts. Until they are ready, those parts return fake
example data, so this screen already works.
"""

import streamlit as st

from maps_part import get_competitors
from signals_part import get_signals
from report_part import build_report

st.set_page_config(page_title="Startup Idea Checker", page_icon="💡", layout="centered")

st.title("💡 Startup Idea Checker")
st.write(
    "Type a business idea and an area. We look up live Google data and "
    "write a simple report on how promising the idea looks."
)

# --- Inputs ---------------------------------------------------------------
idea = st.text_input("Your business idea", placeholder="e.g. student-friendly cafe")
area = st.text_input("Area", placeholder="e.g. near RNS Institute of Technology, Bengaluru")
check = st.button("Check my idea", type="primary")

# --- Run the three parts and show the report ------------------------------
if check:
    if not idea.strip() or not area.strip():
        st.warning("Please type both a business idea and an area.")
    else:
        try:
            with st.spinner("Looking up nearby businesses and market information..."):
                competitors = get_competitors(idea, area)
                signals = get_signals(idea, area)
            with st.spinner("Writing your report..."):
                report = build_report(idea, area, competitors, signals)
        except Exception as error:  # show a plain message, not a scary crash
            st.error(f"Something went wrong: {error}")
            st.stop()

        st.divider()

        # Summary and score
        st.subheader("Summary")
        st.write(report["summary"])
        st.metric("Idea score", f"{report['score']} / 10")
        st.caption(report["score_reason"])

        # Competition
        st.subheader("Competition")
        comp = report["competition"]
        st.write(
            f"**{comp['count']}** similar businesses found, "
            f"average rating **{comp['average_rating']}**. {comp['notes']}"
        )
        if competitors:
            st.dataframe(
                [
                    {
                        "Name": c["name"],
                        "Rating": c["rating"],
                        "Reviews": c["reviews_count"],
                        "Address": c["address"],
                    }
                    for c in competitors
                ],
                width="stretch",
            )

        # Feedback and gaps
        st.subheader("What customers say")
        for item in report["customer_feedback"]:
            st.markdown(f"- {item}")

        st.subheader("Gaps nobody fills")
        for item in report["gaps"]:
            st.markdown(f"- {item}")

        # Sources
        st.subheader("Sources")
        for source in report["sources"]:
            st.markdown(f"- [{source['title']}]({source['link']})")
