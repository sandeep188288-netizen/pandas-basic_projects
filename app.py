"""
🎬 Netflix Data Cleaning Studio
An interactive Streamlit app that takes a messy Netflix movies CSV and
cleans it live, step by step, showing before/after impact at every stage.
"""

import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG + THEME
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Netflix Data Cleaning Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

.stApp {
    background: radial-gradient(circle at 10% 0%, #1a0000 0%, #0b0b0b 45%, #000000 100%);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #140000 0%, #0b0b0b 100%);
    border-right: 1px solid #2a0000;
}

h1, h2, h3 { font-family: 'Inter', sans-serif; color: #ffffff; }

.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4.2rem;
    letter-spacing: 3px;
    color: #E50914;
    margin-bottom: -10px;
    line-height: 1;
}
.hero-sub {
    color: #b3b3b3;
    font-size: 1.05rem;
    margin-top: 4px;
}

.metric-card {
    background: linear-gradient(145deg, #161616, #0d0d0d);
    border: 1px solid #2b2b2b;
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 4px 18px rgba(229,9,20,0.08);
}
.metric-label { color: #9c9c9c; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { color: #ffffff; font-size: 1.9rem; font-weight: 800; }
.metric-delta-good { color: #2ecc71; font-size: 0.85rem; font-weight: 600; }
.metric-delta-bad { color: #ff4757; font-size: 0.85rem; font-weight: 600; }

.step-card {
    background: #121212;
    border-left: 4px solid #E50914;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.step-title { color: #ffffff; font-weight: 700; font-size: 1rem; }
.step-desc { color: #a8a8a8; font-size: 0.88rem; }

div[data-testid="stExpander"] {
    background: #111111;
    border: 1px solid #262626;
    border-radius: 10px;
}

.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    background-color: #141414;
    border-radius: 8px 8px 0 0;
    color: #cccccc;
    padding: 10px 18px;
}
.stTabs [aria-selected="true"] {
    background-color: #E50914 !important;
    color: white !important;
}

.stButton>button, .stDownloadButton>button {
    background: linear-gradient(90deg, #E50914, #b0060f);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    padding: 0.6rem 1.4rem;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    background: linear-gradient(90deg, #ff0a16, #c8060f);
    color: white;
}

footer {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
NETFLIX_RED = "#E50914"
PALETTE = ["#E50914", "#F5F5F1", "#B81D24", "#831010", "#564d4d", "#ff6b6b", "#ffa8a8"]


# ----------------------------------------------------------------------------
# CLEANING FUNCTIONS (ported from the original notebook, hardened a bit)
# ----------------------------------------------------------------------------
def clean_title(title):
    if pd.isnull(title):
        return np.nan
    title = str(title).replace("\n", " ").replace("\t", " ")
    title = " ".join(title.split())
    title = title.rstrip("!")
    if "(" in title:
        title = title[: title.index("(")].strip()
    if title == "":
        return np.nan
    return title.title()


def clean_genre(genre):
    if pd.isnull(genre):
        return np.nan
    genre = str(genre).replace("\n", " ").replace("\t", " ")
    for sep in [",", "|", "/"]:
        genre = genre.replace(sep, " ")
    genre = " ".join(genre.split())
    if genre == "":
        return np.nan
    return genre.split()[0].title()


def clean_year(year):
    if pd.isnull(year):
        return np.nan
    try:
        year = float(year)
    except (ValueError, TypeError):
        return np.nan
    if year < 1900 or year > 2025:
        return np.nan
    return year


def clean_duration(duration):
    if pd.isnull(duration):
        return np.nan
    duration = str(duration).strip()
    try:
        if "h" in duration:
            hours, minutes = duration.split("h")
            hours = int(hours.strip()) * 60
            minutes = minutes.replace("m", "").replace("min", "").strip()
            minutes = int(minutes) if minutes else 0
            total = hours + minutes
        elif "min" in duration:
            total = int(duration.replace("mins", "").replace("min", "").strip())
        else:
            total = int(duration)
    except (ValueError, TypeError):
        return np.nan
    if total < 30 or total > 600:
        return np.nan
    return total


def clean_rating(rating):
    try:
        return float(rating)
    except (ValueError, TypeError):
        return np.nan


def clean_imdb(rating):
    if pd.isnull(rating):
        return np.nan
    try:
        rating = float(rating)
    except (ValueError, TypeError):
        return np.nan
    if rating < 0 or rating > 10:
        return np.nan
    return rating


def clean_votes(votes):
    if pd.isnull(votes):
        return np.nan
    votes = str(votes).replace(",", "").strip()
    try:
        return int(float(votes))
    except (ValueError, TypeError):
        return np.nan


def clean_budget(budget):
    if pd.isnull(budget):
        return np.nan
    budget = str(budget).replace("$", "").replace(",", "").strip()
    try:
        budget = float(budget)
    except (ValueError, TypeError):
        return np.nan
    if budget < 0:
        return np.nan
    return budget


def clean_revenue(revenue):
    if pd.isnull(revenue):
        return np.nan
    revenue = str(revenue).replace(",", "").replace("$", "").strip()
    try:
        revenue = float(revenue)
    except (ValueError, TypeError):
        return np.nan
    if revenue <= 0:
        return np.nan
    return revenue


COUNTRY_MAP = {
    "U.S.": "United States", "US": "United States", "USA": "United States",
    "U.S.A": "United States", "U.S.A.": "United States",
    "U.K.": "United Kingdom", "UK": "United Kingdom", "Britain": "United Kingdom",
}

LANGUAGE_MAP = {
    "english": "English", "Eng": "English", "eng": "English",
    "Hin": "Hindi", "hin": "Hindi",
    "Kor": "Korean", "kor": "Korean",
    "Ger": "German", "ger": "German",
    "Fre": "French", "fre": "French",
    "Jap": "Japanese", "jap": "Japanese",
    "Spa": "Spanish", "spa": "Spanish",
    "Ita": "Italian", "ita": "Italian",
}


def clean_country(value):
    if pd.isnull(value):
        return np.nan
    value = str(value).strip()
    return COUNTRY_MAP.get(value, value.title() if value.isupper() or value.islower() else value)


def clean_language(value):
    if pd.isnull(value):
        return np.nan
    value = str(value).strip()
    if value in LANGUAGE_MAP:
        return LANGUAGE_MAP[value]
    return value.title()


def run_pipeline(df_raw: pd.DataFrame, progress_cb=None):
    """Runs the full cleaning pipeline, returns (clean_df, step_log)."""
    df = df_raw.copy()
    df.columns = [c.strip() for c in df.columns]
    log = []

    def record(step, desc, extra=""):
        log.append({"step": step, "desc": desc, "rows": len(df), "extra": extra})
        if progress_cb:
            progress_cb(step, desc, len(df))

    record("Load", f"Loaded raw dataset with {len(df)} rows and {df.shape[1]} columns.")

    if "Movie_ID" in df.columns:
        before = len(df)
        df = df.drop_duplicates("Movie_ID", keep="first")
        record("De-duplicate IDs", f"Removed {before - len(df)} rows with duplicate Movie_ID.")

    if "Title" in df.columns:
        df["Title"] = df["Title"].apply(clean_title)
        before = len(df)
        df = df.dropna(subset=["Title"])
        record("Clean titles", f"Standardized casing/whitespace; dropped {before - len(df)} rows with empty titles.")

    if "Genre" in df.columns:
        df["Genre"] = df["Genre"].apply(clean_genre)
        record("Clean genres", "Extracted primary genre, standardized casing and separators.")

    if "Release_Year" in df.columns:
        df["Release_Year"] = df["Release_Year"].apply(clean_year)
        record("Fix release years", "Flagged years outside 1900–2025 as missing.")

    if "Duration" in df.columns:
        df["Duration"] = df["Duration"].apply(clean_duration)
        record("Parse durations", "Converted 'Xh Ym' / 'X min' formats into total minutes.")

    if "Rating" in df.columns:
        df["Rating"] = df["Rating"].apply(clean_rating)
        record("Convert ratings", "Cast Rating column to numeric.")

    if "IMDb_Rating" in df.columns:
        df["IMDb_Rating"] = df["IMDb_Rating"].apply(clean_imdb)
        record("Validate IMDb ratings", "Flagged values outside the 0–10 range as missing.")

    if "Votes" in df.columns:
        df["Votes"] = df["Votes"].apply(clean_votes)
        record("Clean votes", "Removed comma separators and converted to integers.")

    if "Budget" in df.columns:
        df["Budget"] = df["Budget"].apply(clean_budget)
        record("Clean budget", "Stripped $ and commas; flagged negative budgets as missing.")

    if "Revenue" in df.columns:
        df["Revenue"] = df["Revenue"].apply(clean_revenue)
        record("Clean revenue", "Stripped commas; flagged zero/negative revenue as missing.")

    if "Date_Added" in df.columns:
        df["Date_Added"] = pd.to_datetime(df["Date_Added"], format="mixed", errors="coerce")
        record("Standardize dates", "Parsed 4 mixed date formats into a single datetime type.")

    if "Country" in df.columns:
        df["Country"] = df["Country"].apply(clean_country)
        record("Standardize countries", "Mapped country-name variants to one canonical name.")

    if "Language" in df.columns:
        df["Language"] = df["Language"].apply(clean_language)
        record("Standardize languages", "Mapped abbreviations/casing to full language names.")

    if {"Title", "Release_Year"}.issubset(df.columns):
        before = len(df)
        df = df.drop_duplicates(subset=["Title", "Release_Year"])
        record("Remove near-duplicates", f"Removed {before - len(df)} rows sharing the same Title + Year.")

    for col, strategy in [("Duration", "median"), ("Rating", "median"),
                           ("IMDb_Rating", "mean"), ("Votes", "median")]:
        if col in df.columns and df[col].isnull().any():
            fill_val = df[col].median() if strategy == "median" else df[col].mean()
            df[col] = df[col].fillna(fill_val)
    if "Release_Year" in df.columns:
        df["Release_Year"] = df["Release_Year"].fillna(df["Release_Year"].median())
    record("Fill remaining gaps", "Filled numeric gaps with median/mean; left Budget/Revenue/names as NaN by design.")

    if "Release_Year" in df.columns:
        df["Release_Year"] = df["Release_Year"].astype("Int64")
    if "Votes" in df.columns:
        df["Votes"] = df["Votes"].astype("Int64")
    if "Duration" in df.columns:
        df["Duration"] = df["Duration"].astype("Int64")
    record("Fix data types", "Converted year/votes/duration to nullable integers.")

    return df, log


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def metric_card(label, value, help_text=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div style="color:#7a7a7a; font-size:0.75rem; margin-top:4px;">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def make_demo_data(n=400):
    rng = np.random.default_rng(42)
    genres = ["Action, Drama", "comedy", "ROMANCE", "Sci-Fi | Thriller", "Drama/Comedy", " Horror\n"]
    countries = ["USA", "U.S.", "US", "UK", "U.K.", "United Kingdom", "India", "France", "Japan  "]
    languages = ["english", "Eng", "Hin", "ENGLISH", "Kor", "Spa", "French"]
    titles = [f"  Movie {i}!!!\n" if i % 5 == 0 else f"Movie Title {i}" for i in range(n)]

    df = pd.DataFrame({
        "Movie_ID": list(range(1, n + 1)) + list(rng.integers(1, 20, 5).tolist()),
        "Title": (titles + titles[:5]),
        "Genre": rng.choice(genres, n + 5),
        "Release_Year": rng.choice([1890, 2099] + list(range(1980, 2025)), n + 5),
        "Duration": [f"{rng.integers(1,3)}h {rng.integers(0,59)}m" if i % 2 == 0
                      else f"{rng.integers(70,180)} min" for i in range(n + 5)],
        "Rating": rng.choice(["PG", "PG-13", "R", "G", None], n + 5).astype(object),
        "IMDb_Rating": np.round(rng.uniform(-1, 15, n + 5), 1),
        "Votes": [f"{rng.integers(100,999999):,}" for _ in range(n + 5)],
        "Budget": [f"${rng.integers(1_000_000,200_000_000):,}" for _ in range(n + 5)],
        "Revenue": [f"{rng.integers(0,500_000_000):,}" for _ in range(n + 5)],
        "Date_Added": rng.choice(["2024-05-01", "01/05/2024", "May 1, 2024", "20240501"], n + 5),
        "Country": rng.choice(countries, n + 5),
        "Language": rng.choice(languages, n + 5),
        "Director": rng.choice(["Dir A", "Dir B", None], n + 5),
        "Cast": rng.choice(["Actor X", "Actor Y", None], n + 5),
        "Production_House": rng.choice(["Studio 1", "Studio 2", None], n + 5),
    })
    return df


def to_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎬 Netflix Cleaning Studio")
    st.caption("Upload your messy dataset and watch it get spotless.")
    uploaded = st.file_uploader("Upload netflix_movies_dirty.csv", type=["csv"])
    use_demo = st.checkbox("Use built-in demo dataset instead", value=uploaded is None)
    st.divider()
    st.markdown("**Pipeline steps applied**")
    st.caption(
        "De-dup IDs → Clean titles → Clean genres → Fix years → Parse durations → "
        "Numeric ratings/votes/budget/revenue → Standardize dates/country/language → "
        "Remove near-dupes → Fill gaps → Fix dtypes"
    )
    st.divider()
    st.caption("Built with your original notebook logic, wrapped in Streamlit ✨")

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown('<div class="hero-title">DATA CLEANING STUDIO</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">A messy Netflix catalogue, cleaned in front of your eyes — '
    'duplicate IDs, mixed date formats, dollar signs, outlier ratings and all.</div>',
    unsafe_allow_html=True,
)
st.write("")

# ----------------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------------
if uploaded is not None and not use_demo:
    raw_df = pd.read_csv(uploaded, dtype=str)
    source_label = uploaded.name
elif use_demo:
    raw_df = make_demo_data()
    source_label = "Built-in demo dataset (synthetic, mirrors the same messiness)"
else:
    st.info("👈 Upload a CSV or check **'Use built-in demo dataset'** in the sidebar to get started.")
    st.stop()

st.caption(f"Source: **{source_label}**")

with st.spinner("Running the cleaning pipeline..."):
    clean_df, step_log = run_pipeline(raw_df)

# ----------------------------------------------------------------------------
# TOP-LEVEL METRICS
# ----------------------------------------------------------------------------
rows_removed = len(raw_df) - len(clean_df)
missing_before = raw_df.isnull().sum().sum() + (raw_df == "").sum().sum()
missing_after = clean_df.isnull().sum().sum()
dup_before = raw_df.duplicated().sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Rows: Before → After", f"{len(raw_df)} → {len(clean_df)}",
                f"{rows_removed} rows removed")
with c2:
    metric_card("Columns", f"{clean_df.shape[1]}", "standardized & type-fixed")
with c3:
    metric_card("Missing / Blank Cells (before)", f"{int(missing_before):,}", "across raw data")
with c4:
    metric_card("Missing Cells (after)", f"{int(missing_after):,}", "intentionally left as NaN where unknowable")

st.write("")

# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------
tab_overview, tab_pipeline, tab_insights, tab_download = st.tabs(
    ["📊 Overview", "🧹 Cleaning Pipeline", "📈 Insights", "⬇️ Download"]
)

# --- OVERVIEW -----------------------------------------------------------
with tab_overview:
    left, right = st.columns(2)
    with left:
        st.subheader("Raw data (first look)")
        st.dataframe(raw_df.head(15), use_container_width=True, height=380)
    with right:
        st.subheader("Cleaned data")
        st.dataframe(clean_df.head(15), use_container_width=True, height=380)

    st.subheader("Missing values by column — before vs after")
    common_cols = [c for c in raw_df.columns if c in clean_df.columns]
    miss_before = raw_df[common_cols].replace("", np.nan).isnull().sum()
    miss_after = clean_df[common_cols].isnull().sum()
    miss_df = pd.DataFrame({"Before": miss_before, "After": miss_after}).reset_index()
    miss_df.columns = ["Column", "Before", "After"]
    miss_df = miss_df.melt(id_vars="Column", var_name="Stage", value_name="Missing Count")
    fig = px.bar(
        miss_df, x="Column", y="Missing Count", color="Stage", barmode="group",
        color_discrete_map={"Before": "#565656", "After": NETFLIX_RED},
        template=PLOTLY_TEMPLATE,
    )
    fig.update_layout(height=420, xaxis_tickangle=-35, legend_title="")
    st.plotly_chart(fig, use_container_width=True)

# --- PIPELINE -------------------------------------------------------------
with tab_pipeline:
    st.subheader("Step-by-step cleaning log")
    prev_rows = len(raw_df)
    for entry in step_log:
        delta = entry["rows"] - prev_rows
        delta_html = ""
        if delta != 0:
            cls = "metric-delta-bad" if delta < 0 else "metric-delta-good"
            delta_html = f'<span class="{cls}">({delta:+d} rows)</span>'
        st.markdown(
            f"""
            <div class="step-card">
                <div class="step-title">{entry['step']} — {entry['rows']} rows {delta_html}</div>
                <div class="step-desc">{entry['desc']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        prev_rows = entry["rows"]

# --- INSIGHTS ---------------------------------------------------------
with tab_insights:
    colA, colB = st.columns(2)

    with colA:
        if "Genre" in clean_df.columns:
            st.subheader("Movies by genre")
            genre_counts = clean_df["Genre"].value_counts().reset_index()
            genre_counts.columns = ["Genre", "Count"]
            fig = px.bar(genre_counts, x="Genre", y="Count", color="Genre",
                         color_discrete_sequence=PALETTE, template=PLOTLY_TEMPLATE)
            fig.update_layout(showlegend=False, height=360)
            st.plotly_chart(fig, use_container_width=True)

        if "IMDb_Rating" in clean_df.columns:
            st.subheader("IMDb rating distribution")
            fig = px.histogram(clean_df, x="IMDb_Rating", nbins=25,
                               color_discrete_sequence=[NETFLIX_RED], template=PLOTLY_TEMPLATE)
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)

    with colB:
        if "Country" in clean_df.columns:
            st.subheader("Top countries")
            top_countries = clean_df["Country"].value_counts().head(10).reset_index()
            top_countries.columns = ["Country", "Count"]
            fig = px.bar(top_countries, x="Count", y="Country", orientation="h",
                         color="Count", color_continuous_scale=["#3a0000", NETFLIX_RED],
                         template=PLOTLY_TEMPLATE)
            fig.update_layout(height=360, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

        if {"Budget", "Revenue"}.issubset(clean_df.columns):
            st.subheader("Budget vs Revenue")
            plot_df = clean_df.dropna(subset=["Budget", "Revenue"])
            if len(plot_df):
                fig = px.scatter(
                    plot_df, x="Budget", y="Revenue",
                    color="IMDb_Rating" if "IMDb_Rating" in plot_df.columns else None,
                    color_continuous_scale=["#565656", NETFLIX_RED],
                    template=PLOTLY_TEMPLATE, opacity=0.75,
                )
                fig.update_layout(height=360)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Not enough non-missing Budget/Revenue rows to plot.")

    if "Release_Year" in clean_df.columns:
        st.subheader("Releases per year")
        year_counts = clean_df["Release_Year"].value_counts().sort_index().reset_index()
        year_counts.columns = ["Release_Year", "Count"]
        fig = px.area(year_counts, x="Release_Year", y="Count",
                      color_discrete_sequence=[NETFLIX_RED], template=PLOTLY_TEMPLATE)
        fig.update_layout(height=340)
        st.plotly_chart(fig, use_container_width=True)

# --- DOWNLOAD -----------------------------------------------------------
with tab_download:
    st.subheader("Grab your cleaned dataset")
    st.write("Everything above, saved as a fresh CSV — the original file is never touched.")
    st.download_button(
        "⬇️ Download cleaned CSV",
        data=to_csv_bytes(clean_df),
        file_name="netflix_movies_cleaned.csv",
        mime="text/csv",
    )
    st.write("")
    st.subheader("Full cleaned table")
    st.dataframe(clean_df, use_container_width=True, height=500)
