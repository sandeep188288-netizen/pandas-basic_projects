# 🎬 Netflix Data Cleaning Studio

An interactive Streamlit app that wraps your `netflix_cleaning_proj01_.py` notebook logic
in a slick, Netflix-themed UI.

## What it does
- Upload your dirty `netflix_movies_dirty.csv` (or use the built-in synthetic demo dataset)
- Runs the **same cleaning steps** from your notebook: dedupe IDs, clean titles/genres,
  fix outlier years, parse mixed duration formats, validate ratings, strip `$`/commas from
  budget & revenue, standardize 4 date formats, unify country/language names, remove
  near-duplicates, fill remaining gaps, and fix data types.
- Shows **before/after metrics**, a **step-by-step cleaning log**, and **charts**
  (genre breakdown, top countries, IMDb rating distribution, budget vs revenue, releases per year).
- Lets you **download the cleaned CSV** with one click.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

## Deploy on Streamlit Community Cloud
1. Push this folder (`app.py` + `requirements.txt`) to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo, and set
   `app.py` as the entry point.
3. Deploy — no other config needed.

## Notes
- If you upload your own CSV, it should have (some subset of) these columns:
  `Movie_ID, Title, Genre, Release_Year, Duration, Rating, IMDb_Rating, Votes, Budget,
  Revenue, Date_Added, Country, Language, Director, Cast, Production_House`.
  The pipeline gracefully skips any column that isn't present.
- The original messy file is never modified — cleaning happens in memory and the
  cleaned result is offered as a fresh download.
