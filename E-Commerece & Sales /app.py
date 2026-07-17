import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Sales Ledger",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = ["#F2A93B", "#2FB8A6", "#F0654C", "#7C8CF2", "#E8D48A", "#5B7FBF"]

# ────────────────────────────────────────────────────────────────
# STYLE
# ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .stApp { background-color: #12172B; }
    section[data-testid="stSidebar"] { background-color: #1E2440; }
    div[data-testid="stMetric"] {
        background-color: #1E2440;
        border: 1px solid rgba(246,243,236,0.08);
        border-radius: 6px;
        padding: 14px 16px;
    }
    div[data-testid="stMetricLabel"] { color: rgba(246,243,236,0.55); }
    h1, h2, h3 { color: #F6F3EC; }
    .stDataFrame { border: 1px solid rgba(246,243,236,0.08); border-radius: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────────────────────
# DATA LOADING + CLEANING (mirrors the original notebook logic)
# ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path_or_buffer):
    data = pd.read_csv(path_or_buffer)

    # --- Missing values -------------------------------------------------
    for col in ["Age", "Rating", "Discount", "Total_Amount"]:
        data[col] = data[col].fillna(data[col].median())
    data["City"] = data["City"].fillna("Unknown")
    data["Customer_Satisfaction"] = data["Customer_Satisfaction"].fillna("Not Provided")

    # --- Duplicates -------------------------------------------------------
    data = data.drop_duplicates(subset="Order_ID", keep="first")

    # --- Gender -------------------------------------------------------
    data["Gender"] = data["Gender"].astype(str).str.strip().str.upper()
    data["Gender"] = data["Gender"].replace(
        {"MALE": "Male", "FEMALE": "Female", "M": "Male", "F": "Female"}
    )

    # --- Unit_Price -------------------------------------------------------
    data["Unit_Price"] = (
        data["Unit_Price"].astype(str).str.replace(",", "", regex=False).astype(float)
    )

    # --- Profit -------------------------------------------------------
    data["Profit"] = (
        data["Profit"]
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    data["Profit"] = pd.to_numeric(data["Profit"], errors="coerce")

    # --- Age -------------------------------------------------------
    data["Age"] = data["Age"].astype(int)

    # --- Dates -------------------------------------------------------
    data["Order_Date"] = pd.to_datetime(
        data["Order_Date"], errors="coerce", format="mixed", dayfirst=False
    )
    data["Delivery_Date"] = pd.to_datetime(
        data["Delivery_Date"], errors="coerce", format="mixed", dayfirst=False
    )
    data["Order_Month"] = data["Order_Date"].dt.to_period("M").astype(str)
    data["Delivery_Days"] = (data["Delivery_Date"] - data["Order_Date"]).dt.days

    return data


def fmt_inr(n: float) -> str:
    if pd.isna(n):
        return "—"
    if n >= 1e7:
        return f"₹{n/1e7:.2f}Cr"
    if n >= 1e5:
        return f"₹{n/1e5:.2f}L"
    if n >= 1e3:
        return f"₹{n/1e3:.1f}K"
    return f"₹{n:.0f}"


# ────────────────────────────────────────────────────────────────
# SIDEBAR — DATA SOURCE + FILTERS
# ────────────────────────────────────────────────────────────────
st.sidebar.title("📦 Sales Ledger")
st.sidebar.caption("Filters apply to every chart and the table below.")

uploaded = st.sidebar.file_uploader("Upload ecommerce_sales_data.csv", type="csv")
data_source = uploaded if uploaded is not None else "ecommerce_sales_data.csv"

try:
    df = load_data(data_source)
except FileNotFoundError:
    st.error(
        "Couldn't find **ecommerce_sales_data.csv** next to app.py. "
        "Upload it from the sidebar, or add it to the repo before deploying."
    )
    st.stop()

st.sidebar.markdown("---")

regions = sorted(df["Region"].dropna().unique())
categories = sorted(df["Product_Category"].dropna().unique())
statuses = sorted(df["Order_Status"].dropna().unique())
memberships = sorted(df["Membership_Type"].dropna().unique())

f_region = st.sidebar.multiselect("Region", regions, default=regions)
f_category = st.sidebar.multiselect("Category", categories, default=categories)
f_status = st.sidebar.multiselect("Order status", statuses, default=statuses)
f_membership = st.sidebar.multiselect("Membership", memberships, default=memberships)

min_date, max_date = df["Order_Date"].min(), df["Order_Date"].max()
f_dates = st.sidebar.date_input(
    "Order date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

mask = (
    df["Region"].isin(f_region)
    & df["Product_Category"].isin(f_category)
    & df["Order_Status"].isin(f_status)
    & df["Membership_Type"].isin(f_membership)
)
if len(f_dates) == 2:
    start, end = f_dates
    mask &= (df["Order_Date"].dt.date >= start) & (df["Order_Date"].dt.date <= end)

fdf = df[mask].copy()

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(fdf):,} of {len(df):,} orders match your filters.")

# ────────────────────────────────────────────────────────────────
# HEADER
# ────────────────────────────────────────────────────────────────
st.title("Ledger of the Marketplace")
st.caption(
    "Cleaned, deduplicated e-commerce sales data — revenue, returns, and the routes "
    "goods travelled to reach the customer."
)

if fdf.empty:
    st.warning("No orders match the current filters.")
    st.stop()

# ────────────────────────────────────────────────────────────────
# KPIs
# ────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total revenue", fmt_inr(fdf["Revenue"].sum()))
c2.metric("Total profit", fmt_inr(fdf["Profit"].sum()))
c3.metric("Orders", f"{fdf['Order_ID'].nunique():,}")
c4.metric("Avg order value", fmt_inr(fdf["Total_Amount"].mean()))
c5.metric("Avg rating", f"{fdf['Rating'].mean():.2f} ★")

st.markdown("")

# ────────────────────────────────────────────────────────────────
# ROW 1 — TREND + REGION
# ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Revenue & profit over time")
    monthly = (
        fdf.groupby("Order_Month")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
        .reset_index()
        .sort_values("Order_Month")
    )
    fig = go.Figure()
    fig.add_bar(x=monthly["Order_Month"], y=monthly["Revenue"], name="Revenue", marker_color="#2FB8A6")
    fig.add_trace(
        go.Scatter(
            x=monthly["Order_Month"], y=monthly["Profit"], name="Profit",
            yaxis="y2", mode="lines+markers", line=dict(color="#F2A93B", width=3),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="Revenue"),
        yaxis2=dict(title="Profit", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=10, r=10, t=30, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Revenue by region")
    region_rev = fdf.groupby("Region")["Revenue"].sum().sort_values(ascending=False)
    fig = px.pie(
        values=region_rev.values, names=region_rev.index, hole=0.55,
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10), height=380,
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# ROW 2 — CATEGORY + STATUS
# ────────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Revenue by category")
    cat_rev = fdf.groupby("Product_Category")["Revenue"].sum().sort_values(ascending=True)
    fig = px.bar(
        x=cat_rev.values, y=cat_rev.index, orientation="h",
        color=cat_rev.values, color_continuous_scale=["#2FB8A6", "#F2A93B"],
    )
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10), height=360,
        xaxis_title="Revenue", yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("Order status")
    status_ct = fdf.groupby("Order_Status")["Order_ID"].nunique().sort_values(ascending=True)
    fig = px.bar(
        x=status_ct.values, y=status_ct.index, orientation="h",
        color=status_ct.index, color_discrete_sequence=PALETTE,
    )
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=360,
        xaxis_title="Orders", yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# ROW 3 — PAYMENT + AGE + RATING
# ────────────────────────────────────────────────────────────────
col5, col6, col7 = st.columns(3)

with col5:
    st.subheader("Payment method")
    pay = fdf.groupby("Payment_Method")["Order_ID"].nunique()
    fig = px.pie(values=pay.values, names=pay.index, color_discrete_sequence=PALETTE)
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10), height=320,
        legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.subheader("Age of buyer")
    fig = px.histogram(fdf, x="Age", nbins=20, color_discrete_sequence=["#7C8CF2"])
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10), height=320, showlegend=False,
        yaxis_title="Orders",
    )
    st.plotly_chart(fig, use_container_width=True)

with col7:
    st.subheader("Rating distribution")
    rating_ct = fdf["Rating"].round().value_counts().sort_index()
    fig = px.bar(x=rating_ct.index, y=rating_ct.values, color_discrete_sequence=["#F0654C"])
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10), height=320, showlegend=False,
        xaxis_title="Rating", yaxis_title="Orders",
    )
    st.plotly_chart(fig, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# ROW 4 — TOP PRODUCTS + SALESPEOPLE
# ────────────────────────────────────────────────────────────────
col8, col9 = st.columns(2)

with col8:
    st.subheader("Top 10 products by revenue")
    top_products = (
        fdf.groupby("Product_Name")
        .agg(Revenue=("Revenue", "sum"), Orders=("Order_ID", "nunique"), Rating=("Rating", "mean"))
        .sort_values("Revenue", ascending=False)
        .head(10)
    )
    top_products["Revenue"] = top_products["Revenue"].map(fmt_inr)
    top_products["Rating"] = top_products["Rating"].round(2)
    st.dataframe(top_products, use_container_width=True)

with col9:
    st.subheader("Top salespeople")
    top_sales = (
        fdf.groupby("Salesperson")
        .agg(Revenue=("Revenue", "sum"), Orders=("Order_ID", "nunique"))
        .sort_values("Revenue", ascending=False)
        .head(10)
    )
    top_sales["Revenue"] = top_sales["Revenue"].map(fmt_inr)
    st.dataframe(top_sales, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# ROW 5 — ORDER REGISTER
# ────────────────────────────────────────────────────────────────
st.subheader("Order register")
search = st.text_input("Search order, customer, city, or product")

table_cols = [
    "Order_ID", "Customer_Name", "City", "Region", "Product_Category",
    "Product_Name", "Quantity", "Total_Amount", "Profit", "Order_Status",
    "Payment_Method", "Rating", "Order_Date",
]
table = fdf[table_cols].copy()
table["Order_Date"] = table["Order_Date"].dt.strftime("%Y-%m-%d")

if search:
    q = search.lower()
    keep = table.apply(
        lambda r: q in str(r["Order_ID"]).lower()
        or q in str(r["Customer_Name"]).lower()
        or q in str(r["City"]).lower()
        or q in str(r["Product_Name"]).lower(),
        axis=1,
    )
    table = table[keep]

st.dataframe(table.sort_values("Order_Date", ascending=False), use_container_width=True, height=420)

st.download_button(
    "⬇ Download filtered data as CSV",
    data=fdf.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales_data.csv",
    mime="text/csv",
)

st.caption("Cleaned from ecommerce_sales_data.csv — median-fill, dedupe on Order_ID, type coercion.")
