# Startup Idea Checker

Startup Idea Checker is a web app that tells you whether a business idea looks promising, using live data instead of guesses.

You type a business idea and an area, for example "student-friendly cafe near RNS Institute of Technology, Bengaluru". The app then:

1. Finds similar businesses nearby on Google Maps, with their ratings and reviews.
2. Collects recent search results and news about the topic.
3. Uses AI to write a simple report: the competition, what customers like or dislike, the gaps nobody fills, and a score out of 10.

Every point in the report links back to its source.

Built for the Beyond 9TO5 Buildathon, Track 1: Best Use of SerpApi.

## How to run

1. Install Python, then install the requirements:

   ```
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to a new file named `.env` and add your keys.
3. Start the app:

   ```
   streamlit run app.py
   ```

Until the real parts are finished, the app shows fake example data from `sample_data.py`.

## Project files

| File | What it does | Owner |
| --- | --- | --- |
| `maps_part.py` | Finds nearby businesses on Google Maps | Role 1 |
| `signals_part.py` | Finds search results and news about the idea | Role 2 |
| `report_part.py` | Uses AI to write the report and score | Role 3 |
| `app.py` | The screen people use, joins all parts | Role 4 |
| `sample_data.py` | Fake example data for testing | Everyone |

## Rules for the team

- Do not change the shared data format. If it must change, tell everyone first.
- Never upload your `.env` file or any API key to GitHub.
- Work on your own file, and make small commits often.

## Tech

Python, Streamlit, SerpApi (Google Maps, Google Search, Google News), and an AI model API.

## Team

Add your four names here.
