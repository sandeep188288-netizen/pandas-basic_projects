"""
Netflix Data Cleaning Studio
============================
An interactive Streamlit front-end for the Netflix dirty-dataset cleaning
pipeline (Title / Genre / Year / Duration / Rating / IMDb / Votes / Budget /
Revenue / Date / Country / Language cleaning + de-duplication).

Run with:
    streamlit run netflix_cleaning_studio.py
"""

import io
import random
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Netflix Data Cleaning Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# THEME / CSS  — cinematic screening-room palette
# ----------------------------------------------------------------------
CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root{
    --bg:            #0B0B0D;
    --bg-panel:      #16161A;
    --bg-panel-2:    #1E1E23;
    --line:          #2A2A30;
    --red:           #E50914;
    --red-dim:       #8C060D;
    --gold:          #F2B705;
    --ink:           #ECECEE;
    --ink-dim:       #9A9AA2;
    --good:          #2FBF71;
}

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.stApp{ background: radial-gradient(circle at 10% 0%, #17131a 0%, #0B0B0D 45%) fixed; color: var(--ink); }

#MainMenu, footer, header{ visibility: hidden; }

/* ---------- FILM-STRIP DIVIDER ---------- */
.filmstrip{
    height: 22px;
    background:
        repeating-linear-gradient(90deg, #000 0 10px, #000 10px);
    background-color:#000;
    position:relative;
    margin: 8px 0 28px 0;
    border-top:2px solid var(--line);
    border-bottom:2px solid var(--line);
}
.filmstrip::before, .filmstrip::after{
    content:"";
    position:absolute; top:0; bottom:0; left:0; right:0;
    background-image: radial-gradient(circle, var(--bg) 3px, transparent 3.5px);
    background-size: 26px 22px;
    background-position: 6px 0;
}

/* ---------- HERO ---------- */
.hero-wrap{ padding: 6px 4px 0 4px; }
.hero-eyebrow{
    font-family:'JetBrains Mono', monospace;
    letter-spacing:.22em;
    font-size:.72rem;
    color: var(--gold);
    text-transform:uppercase;
    margin-bottom:6px;
}
.hero-title{
    font-family:'Bebas Neue', sans-serif;
    font-size: 4.6rem;
    line-height: .95;
    letter-spacing: .01em;
    background: linear-gradient(90deg, #fff 0%, #fff 55%, var(--red) 120%);
    -webkit-background-clip: text;
    background-clip:text;
    color: transparent;
    margin:0;
}
.hero-sub{
    color: var(--ink-dim);
    font-size: 1.02rem;
    max-width: 640px;
    margin-top: 10px;
    line-height:1.55;
}

/* ---------- CARDS ---------- */
.card{
    background: linear-gradient(180deg, var(--bg-panel) 0%, var(--bg-panel-2) 100%);
    border: 1px solid var(--line);
    border-left: 3px solid var(--red);
    border-radius: 10px;
    padding: 18px 20px;
    height:100%;
}
.card h3{ margin:0 0 4px 0; font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-dim); font-weight:600;}
.card .big{ font-family:'Bebas Neue', sans-serif; font-size:2.3rem; color:var(--ink); line-height:1;}
.card .delta-good{ color: var(--good); font-size:.82rem; font-weight:600; }
.card .delta-bad{ color: var(--red); font-size:.82rem; font-weight:600; }

.step-card{
    background: var(--bg-panel);
    border:1px solid var(--line);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 10px;
}
.step-num{
    font-family:'Bebas Neue', sans-serif;
    color: var(--red);
    font-size: 1.6rem;
    margin-right: 10px;
}
.step-title{ font-weight:700; font-size: 1.02rem; color: var(--ink);}
.step-desc{ color: var(--ink-dim); font-size:.88rem; margin-top:2px;}
.pill{
    display:inline-block; font-family:'JetBrains Mono',monospace; font-size:.72rem;
    padding:2px 9px; border-radius:20px; margin-right:6px; margin-top:8px;
    background: rgba(229,9,20,.12); color:#ff5b62; border:1px solid rgba(229,9,20,.35);
}
.pill.gold{ background: rgba(242,183,5,.12); color:var(--gold); border:1px solid rgba(242,183,5,.35);}
.pill.good{ background: rgba(47,191,113,.12); color:var(--good); border:1px solid rgba(47,191,113,.35);}

/* Section headings */
.section-title{
    font-family:'Bebas Neue', sans-serif;
    font-size: 1.9rem;
    letter-spacing:.02em;
    color: var(--ink);
    margin: 6px 0 2px 0;
    border-left: 4px solid var(--red);
    padding-left: 10px;
}
.section-sub{ color: var(--ink-dim); font-size:.88rem; margin: 0 0 16px 14px;}

/* Buttons */
.stButton>button, .stDownloadButton>button{
    background: linear-gradient(90deg, var(--red) 0%, #B00610 100%);
    color: white; border:none; border-radius: 8px; padding: .6rem 1.3rem;
    font-weight:700; letter-spacing:.02em; box-shadow: 0 4px 16px rgba(229,9,20,.25);
    transition: all .15s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover{
    transform: translateY(-1px); box-shadow: 0 6px 22px rgba(229,9,20,.4);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{ gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"]{
    background: transparent; color: var(--ink-dim); border-radius: 8px 8px 0 0;
    padding: 10px 16px; font-weight:600;
}
.stTabs [aria-selected="true"]{ color: var(--ink) !important; border-bottom: 3px solid var(--red) !important; }

/* Sidebar */
section[data-testid="stSidebar"]{
    background: #0E0E11; border-right:1px solid var(--line);
}
.brand{
    font-family:'Bebas Neue', sans-serif; font-size:1.7rem; letter-spacing:.03em; color:var(--ink);
}
.brand span{ color: var(--red); }

/* Dataframe */
[data-testid="stDataFrame"]{ border:1px solid var(--line); border-radius:10px; overflow:hidden;}

hr{ border-color: var(--line); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def film_divider():
    st.markdown('<div class="filmstrip"></div>', unsafe_allow_html=True)


def section(title, sub=""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def metric_card(label, value, delta=None, good=True):
    delta_html = ""
    if delta is not None:
        cls = "delta-good" if good else "delta-bad"
        delta_html = f'<div class="{cls}">{delta}</div>'
    st.markdown(
        f"""<div class="card"><h3>{label}</h3><div class="big">{value}</div>{delta_html}</div>""",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# SAMPLE / SYNTHETIC DIRTY DATA  (so the app works with zero uploads)
# ----------------------------------------------------------------------
def generate_sample_data(n=300, seed=42):
    rng = random.Random(seed)
    titles = ["Inception", "The Matrix", "Parasite", "His House", "Roma",
              "Whiplash", "Coco", "Arrival", "Tenet", "Get Out", "Her",
              "Moonlight", "Interstellar", "Amélie", "Drive"]
    genres_raw = ["action", "ACTION", "Action, Drama", "Comedy | Romance",
                  "Drama/Thriller", " Fantasy", "\tDrama", "Sci-Fi", "horror",
                  "Documentary", "Action ", "comedy"]
    countries_raw = ["USA", "U.S.", "U.S.A.", "US", "United States", "UK",
                      "U.K.", "Britain", "India", "South Korea", "France", None]
    languages_raw = ["english", "English", "Eng", "Hin", "Kor", "Ger", "Fre",
                      "Jap", "Spa", "Ita", "Chinese", None]
    date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%Y%m%d"]

    rows = []
    for i in range(n):
        title = rng.choice(titles)
        deco = rng.choice(["", "  ", "\n", "!!!", "   \n"])
        title_val = f"{title.upper() if rng.random()<.2 else title}{deco}"
        year = rng.choice([1890, 2099] + list(range(1980, 2025)))
        dur_style = rng.choice(["hm", "min", "plain"])
        base_minutes = rng.randint(70, 190)
        if dur_style == "hm":
            duration = f"{base_minutes//60}h {base_minutes%60}m"
        elif dur_style == "min":
            duration = f"{base_minutes}min" if rng.random() < .5 else f"{base_minutes} mins"
        else:
            duration = str(base_minutes)
        rating = rng.choice([str(round(rng.uniform(1, 10), 1)), "", None])
        imdb = rng.choice([round(rng.uniform(-1, 15), 1), round(rng.uniform(0, 10), 1)])
        votes = f"{rng.randint(500, 2_000_000):,}"
        budget = rng.choice([f"${rng.randint(-5_000_000, 200_000_000):,}", None])
        revenue = rng.choice([f"{rng.randint(0, 900_000_000):,}", "0", None])
        d = rng.choice(date_formats)
        try:
            date_val = (dt.date(2015, 1, 1) + dt.timedelta(days=rng.randint(0, 3600))).strftime(d)
        except Exception:
            date_val = None
        movie_id = f"NF{ (i % int(n*0.92)) + 1 :04d}"  # forces some duplicate IDs

        rows.append({
            "Movie_ID": movie_id,
            "Title": title_val,
            "Genre": rng.choice(genres_raw),
            "Release_Year": year,
            "Duration": duration,
            "Rating": rating,
            "IMDb_Rating": imdb,
            "Votes": votes,
            "Budget": budget,
            "Revenue": revenue,
            "Date_Added": date_val,
            "Country": rng.choice(countries_raw),
            "Language": rng.choice(languages_raw),
            "Director": rng.choice([f"Director {chr(65+i%20)}", None]),
            "Cast": rng.choice([f"Actor {chr(65+i%26)}, Actor {chr(90-i%26)}", None]),
            "Production_House": rng.choice([f"Studio {i%7}", None]),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# CLEANING FUNCTIONS  (ported from the notebook, hardened with try/except
# so the app never crashes on unexpected real-world input)
# ----------------------------------------------------------------------
def clean_title(title):
    if pd.isnull(title):
        return np.nan
    title = str(title).replace("\n", " ").replace("\t", " ")
    title = " ".join(title.split())
    title = title.rstrip("!")
    if not title:
        return np.nan
    return title.title()


def clean_genre(genre):
    if pd.isnull(genre):
        return np.nan
    genre = str(genre).replace("\n", "").replace("\t", "")
    genre = genre.replace("|", ",").replace("/", ",")
    genre = genre.split(",")[0].strip()
    if not genre:
        return np.nan
    return genre.title()


def clean_year(year, lo=1900, hi=2025):
    try:
        if pd.isnull(year):
            return np.nan
        year = float(year)
        if year < lo or year > hi:
            return np.nan
        return int(year)
    except Exception:
        return np.nan


def clean_duration(duration):
    try:
        if pd.isnull(duration):
            return np.nan
        d = str(duration).strip()
        if "h" in d:
            hours, mins = d.split("h")
            hours = int(hours.strip()) * 60
            mins = mins.replace("m", "").strip()
            mins = int(mins) if mins else 0
            total = hours + mins
        elif "min" in d:
            total = int(d.replace("mins", "").replace("min", "").strip())
        else:
            total = int(float(d))
        if total < 30 or total > 600:
            return np.nan
        return total
    except Exception:
        return np.nan


def clean_rating(rating):
    try:
        if pd.isnull(rating) or str(rating).strip() == "":
            return np.nan
        return float(rating)
    except Exception:
        return np.nan


def clean_imdb(rating):
    try:
        if pd.isnull(rating):
            return np.nan
        rating = float(rating)
        if rating < 0 or rating > 10:
            return np.nan
        return rating
    except Exception:
        return np.nan


def clean_votes(votes):
    try:
        if pd.isnull(votes):
            return np.nan
        return int("".join(str(votes).split(",")))
    except Exception:
        return np.nan


def clean_budget(budget):
    try:
        if pd.isnull(budget):
            return np.nan
        budget = str(budget).replace("$", "").replace(",", "")
        budget = float(budget)
        return np.nan if budget < 0 else budget
    except Exception:
        return np.nan


def clean_revenue(revenue):
    try:
        if pd.isnull(revenue):
            return np.nan
        revenue = str(revenue).replace(",", "")
        revenue = float(revenue)
        return np.nan if revenue <= 0 else revenue
    except Exception:
        return np.nan


COUNTRY_MAP = {
    "U.S.": "United States", "U.S.A.": "United States", "US": "United States",
    "USA": "United States", "Britain": "United Kingdom", "U.K.": "United Kingdom",
    "UK": "United Kingdom",
}

LANGUAGE_MAP = {
    "english": "English", "English": "English", "Eng": "English", "Hin": "Hindi",
    "Kor": "Korean", "Ger": "German", "Fre": "French", "Jap": "Japanese",
    "Spa": "Spanish", "Ita": "Italian", "Chinese": "Chinese",
}


def clean_country(value):
    if pd.isnull(value):
        return np.nan
    return COUNTRY_MAP.get(str(value).strip(), str(value).strip())


def clean_language(value):
    if pd.isnull(value):
        return np.nan
    value = str(value).strip()
    if value in LANGUAGE_MAP:
        return LANGUAGE_MAP[value]
    return value.title()


# ----------------------------------------------------------------------
# PIPELINE RUNNER — executes every step, logs before/after stats
# ----------------------------------------------------------------------
def run_pipeline(df_raw: pd.DataFrame):
    df = df_raw.copy()
    log = []

    def snapshot(name, desc, col=None):
        nulls = int(df.isnull().sum().sum())
        log.append({
            "step": name, "desc": desc, "rows": len(df),
            "nulls": nulls, "col": col,
        })

    snapshot("Raw Load", "Dataset loaded exactly as uploaded.")

    if "Movie_ID" in df.columns:
        before = len(df)
        df = df.drop_duplicates("Movie_ID", keep="first")
        snapshot("De-duplicate Movie_ID", f"Removed {before-len(df)} rows sharing a Movie_ID.")

    if "Title" in df.columns:
        df["Title"] = df["Title"].apply(clean_title)
        snapshot("Clean Title", "Trimmed whitespace/newlines, stripped '!!!', title-cased.", "Title")

    if "Genre" in df.columns:
        df["Genre"] = df["Genre"].apply(clean_genre)
        snapshot("Clean Genre", "Took primary genre, unified separators, title-cased.", "Genre")

    if "Release_Year" in df.columns:
        df["Release_Year"] = df["Release_Year"].apply(clean_year)
        snapshot("Fix Release Year", "Flagged years outside 1900-2025 as missing.", "Release_Year")

    if "Duration" in df.columns:
        df["Duration"] = df["Duration"].apply(clean_duration)
        snapshot("Normalize Duration", "Converted 'Xh Ym' / 'Xmin' formats to total minutes.", "Duration")

    if "Rating" in df.columns:
        df["Rating"] = df["Rating"].apply(clean_rating)
        snapshot("Convert Rating", "Cast text ratings to numeric, invalid values -> NaN.", "Rating")

    if "IMDb_Rating" in df.columns:
        df["IMDb_Rating"] = df["IMDb_Rating"].apply(clean_imdb)
        snapshot("Validate IMDb Rating", "Enforced the 0-10 domain rule.", "IMDb_Rating")

    if "Votes" in df.columns:
        df["Votes"] = df["Votes"].apply(clean_votes)
        snapshot("Clean Votes", "Removed thousands separators, cast to integer.", "Votes")

    if "Budget" in df.columns:
        df["Budget"] = df["Budget"].apply(clean_budget)
        snapshot("Clean Budget", "Stripped '$'/commas, negative budgets -> NaN.", "Budget")

    if "Revenue" in df.columns:
        df["Revenue"] = df["Revenue"].apply(clean_revenue)
        snapshot("Clean Revenue", "Stripped commas, zero/negative revenue -> NaN.", "Revenue")

    if "Date_Added" in df.columns:
        df["Date_Added"] = pd.to_datetime(df["Date_Added"], format="mixed", errors="coerce")
        snapshot("Parse Date Added", "Unified 4 mixed date formats into one datetime dtype.", "Date_Added")

    if "Country" in df.columns:
        df["Country"] = df["Country"].apply(clean_country)
        snapshot("Standardize Country", "Mapped USA/UK variants to one canonical name.", "Country")

    if "Language" in df.columns:
        df["Language"] = df["Language"].apply(clean_language)
        snapshot("Standardize Language", "Mapped abbreviations (Eng/Hin/Kor...) to full names.", "Language")

    if {"Title", "Release_Year"}.issubset(df.columns):
        before = len(df)
        df = df.drop_duplicates(subset=["Title", "Release_Year"], keep="first")
        snapshot("Remove Near-duplicates", f"Removed {before-len(df)} rows sharing Title + Year.")

    for col in ["Release_Year", "IMDb_Rating", "Duration", "Rating", "Votes"]:
        if col in df.columns and df[col].notna().any():
            df[col] = df[col].fillna(df[col].median())
    if "Title" in df.columns:
        df["Title"] = df["Title"].fillna("Unknown")
    snapshot("Impute Remaining Nulls", "Filled numeric gaps with column medians; Title -> 'Unknown'.")

    return df, pd.DataFrame(log)


# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand">NETFLIX<span>CLEAN</span></div>', unsafe_allow_html=True)
    st.caption("Data Cleaning Studio · v1.0")
    st.markdown("---")

    uploaded = st.file_uploader("Upload dirty CSV", type=["csv"])
    use_sample = st.checkbox("Use synthetic demo data instead", value=(uploaded is None))

    st.markdown("---")
    st.markdown("**Pipeline covers**")
    st.markdown(
        "- Duplicate IDs & near-duplicates\n"
        "- Title / Genre normalization\n"
        "- Year / Rating / IMDb range checks\n"
        "- Duration, Votes, Budget, Revenue parsing\n"
        "- Mixed-format date parsing\n"
        "- Country & Language standardization\n"
        "- Median imputation"
    )
    st.markdown("---")
    st.caption("Built with pandas + NumPy + Streamlit")

# ----------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------
st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
st.markdown('<div class="hero-eyebrow">DATA ENGINEERING · PORTFOLIO PROJECT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">NETFLIX DATA<br>CLEANING STUDIO</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">A messy, real-world Netflix catalogue — duplicate IDs, mixed date '
    'formats, currency-formatted budgets, and inconsistent country/language labels — turned into '
    'an analysis-ready dataset. Upload a CSV, watch the pipeline run column by column, and export '
    'the cleaned result.</div>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)
film_divider()

# ----------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------
if uploaded is not None and not use_sample:
    try:
        df_raw = pd.read_csv(uploaded)
        source_label = uploaded.name
    except Exception as e:
        st.error(f"Could not read that CSV: {e}")
        st.stop()
else:
    df_raw = generate_sample_data()
    source_label = "synthetic_demo_data.csv"

st.markdown(
    f'<span class="pill gold">SOURCE: {source_label}</span>'
    f'<span class="pill">{df_raw.shape[0]:,} rows</span>'
    f'<span class="pill">{df_raw.shape[1]} columns</span>',
    unsafe_allow_html=True,
)

run = st.button("▶  Run Cleaning Pipeline", use_container_width=False)

if "cleaned" not in st.session_state:
    st.session_state.cleaned = None
    st.session_state.log = None

if run:
    with st.spinner("Running pipeline..."):
        cleaned_df, log_df = run_pipeline(df_raw)
        st.session_state.cleaned = cleaned_df
        st.session_state.log = log_df

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab_overview, tab_pipeline, tab_compare, tab_data, tab_download = st.tabs(
    ["📊 Overview", "🧪 Pipeline", "⚖️ Before vs After", "🧹 Cleaned Data", "⬇️ Download"]
)

# ---- OVERVIEW ----
with tab_overview:
    section("Raw Dataset Snapshot", "First look before any cleaning happens.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Rows", f"{df_raw.shape[0]:,}")
    with c2: metric_card("Columns", df_raw.shape[1])
    with c3: metric_card("Missing Cells", f"{int(df_raw.isnull().sum().sum()):,}")
    dup_id = df_raw['Movie_ID'].duplicated().sum() if 'Movie_ID' in df_raw.columns else 0
    with c4: metric_card("Duplicate IDs", dup_id)

    st.write("")
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("**Preview**")
        st.dataframe(df_raw.head(12), use_container_width=True, height=340)
    with right:
        st.markdown("**Missing values by column**")
        miss = df_raw.isnull().sum().sort_values(ascending=False)
        miss = miss[miss > 0]
        if len(miss):
            fig = px.bar(
                x=miss.values, y=miss.index, orientation="h",
                labels={"x": "Missing cells", "y": ""},
                color_discrete_sequence=["#E50914"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#ECECEE", height=340, margin=dict(l=0, r=10, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No missing values detected in this file.")

# ---- PIPELINE ----
with tab_pipeline:
    section("Cleaning Pipeline", "Each step below runs in sequence — click Run in the top bar to execute.")
    if st.session_state.log is None:
        st.info("Click **▶ Run Cleaning Pipeline** above to execute and see step-by-step results.")
    else:
        log_df = st.session_state.log
        for i, row in log_df.iterrows():
            st.markdown(
                f"""<div class="step-card">
                    <span class="step-num">{i:02d}</span>
                    <span class="step-title">{row['step']}</span>
                    <div class="step-desc">{row['desc']}</div>
                    <span class="pill">{row['rows']:,} rows</span>
                    <span class="pill gold">{row['nulls']:,} nulls remaining</span>
                </div>""",
                unsafe_allow_html=True,
            )

# ---- BEFORE VS AFTER ----
with tab_compare:
    section("Before vs After", "Impact of the pipeline on shape, completeness, and duplication.")
    if st.session_state.cleaned is None:
        st.info("Run the pipeline first to unlock this comparison.")
    else:
        cleaned_df = st.session_state.cleaned
        rows_before, rows_after = df_raw.shape[0], cleaned_df.shape[0]
        nulls_before = int(df_raw.isnull().sum().sum())
        nulls_after = int(cleaned_df.isnull().sum().sum())

        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Rows", f"{rows_after:,}", f"-{rows_before-rows_after} duplicates removed", good=True)
        with c2:
            pct = (1 - nulls_after / nulls_before) * 100 if nulls_before else 0
            metric_card("Missing Cells", f"{nulls_after:,}", f"↓ {pct:.0f}% vs raw", good=True)
        with c3:
            quality = 100 * (1 - nulls_after / (cleaned_df.shape[0] * cleaned_df.shape[1]))
            metric_card("Data Quality Score", f"{quality:.0f}/100", "cells non-null", good=True)

        st.write("")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Missing cells: raw vs cleaned**")
            comp = pd.DataFrame({
                "Stage": ["Raw", "Cleaned"],
                "Missing cells": [nulls_before, nulls_after],
            })
            fig = px.bar(comp, x="Stage", y="Missing cells",
                         color="Stage", color_discrete_sequence=["#8C060D", "#2FBF71"])
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               font_color="#ECECEE", showlegend=False, height=320)
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            st.markdown("**Row count: raw vs cleaned**")
            comp2 = pd.DataFrame({"Stage": ["Raw", "Cleaned"], "Rows": [rows_before, rows_after]})
            fig2 = px.bar(comp2, x="Stage", y="Rows", color="Stage",
                          color_discrete_sequence=["#8C060D", "#E50914"])
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#ECECEE", showlegend=False, height=320)
            st.plotly_chart(fig2, use_container_width=True)

        if "Genre" in cleaned_df.columns:
            st.markdown("**Genre distribution (cleaned)**")
            gc = cleaned_df["Genre"].value_counts().head(10)
            fig3 = px.bar(x=gc.index, y=gc.values,
                          labels={"x": "Genre", "y": "Count"},
                          color_discrete_sequence=["#F2B705"])
            fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#ECECEE", height=320)
            st.plotly_chart(fig3, use_container_width=True)

# ---- CLEANED DATA ----
with tab_data:
    section("Cleaned Dataset", "Analysis-ready output of the pipeline.")
    if st.session_state.cleaned is None:
        st.info("Run the pipeline first to view cleaned data.")
    else:
        st.dataframe(st.session_state.cleaned, use_container_width=True, height=480)

# ---- DOWNLOAD ----
with tab_download:
    section("Export", "Download the cleaned dataset as CSV.")
    if st.session_state.cleaned is None:
        st.info("Run the pipeline first to enable download.")
    else:
        buf = io.StringIO()
        st.session_state.cleaned.to_csv(buf, index=False)
        st.download_button(
            "⬇  Download cleaned_netflix.csv",
            data=buf.getvalue(),
            file_name="cleaned_netflix.csv",
            mime="text/csv",
        )
        st.caption("File is generated fresh from the current pipeline run — nothing is stored server-side.")

film_divider()
st.caption("Netflix Data Cleaning Studio — built with pandas, NumPy, Streamlit & Plotly.")
