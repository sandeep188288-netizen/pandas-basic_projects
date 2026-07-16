"""
E-Commerce Sales & Customer Analytics Dashboard
------------------------------------------------
Built on top of the cleaning/analysis logic from the original
"E-Commerce Sales.ipynb" pandas practice notebook.

Run locally:
    streamlit run app.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------
# STYLING
# --------------------------------------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #0e1117; }

    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #2d3748;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }
    .metric-label {
        font-size: 0.78rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f9fafb;
    }
    .metric-sub {
        font-size: 0.78rem;
        margin-top: 4px;
    }
    .up { color: #34d399; }
    .down { color: #f87171; }

    h1, h2, h3 { color: #f9fafb; }

    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1f2937;
        border-radius: 8px 8px 0 0;
        padding: 8px 18px;
    }
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }
</style>
""", unsafe_allow_html=True)

PRIMARY = "#6366f1"
PALETTE = ["#6366f1", "#22d3ee", "#f472b6", "#fbbf24", "#34d399", "#f87171", "#a78bfa"]


# --------------------------------------------------------------------------------
# DATA LOADING + CLEANING  (mirrors the original notebook's logic)
# --------------------------------------------------------------------------------
@st.cache_data
def load_and_clean_data(path="ecommerce_sales_data.csv"):
    data = pd.read_csv(path)

    # --- Missing value handling ---
    for col in ["Age", "Rating", "Discount", "Total_Amount", "Profit", "Cost", "Revenue"]:
        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col].astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False),
                errors="coerce"
            )
            data[col] = data[col].fillna(data[col].median())

    data["City"] = data["City"].fillna("Unknown")
    data["Customer_Satisfaction"] = data["Customer_Satisfaction"].fillna("Not Provided")

    # --- Duplicates ---
    data = data.drop_duplicates(subset="Order_ID", keep="first")

    # --- Gender standardization ---
    data["Gender"] = data["Gender"].astype(str).str.strip().str.upper()
    data["Gender"] = data["Gender"].replace(
        {"MALE": "Male", "FEMALE": "Female", "M": "Male", "F": "Female"}
    )

    # --- Unit_Price cleanup ---
    data["Unit_Price"] = (
        data["Unit_Price"].astype(str).str.replace(",", "", regex=False)
    )
    data["Unit_Price"] = pd.to_numeric(data["Unit_Price"], errors="coerce")

    # --- Age as int ---
    data["Age"] = data["Age"].round().astype(int)

    # --- Dates ---
    data["Order_Date"] = pd.to_datetime(data["Order_Date"], errors="coerce", format="mixed", dayfirst=False)
    data["Delivery_Date"] = pd.to_datetime(data["Delivery_Date"], errors="coerce", format="mixed", dayfirst=False)
    data["Delivery_Days"] = (data["Delivery_Date"] - data["Order_Date"]).dt.days

    # --- Derived fields ---
    data["Order_Month"] = data["Order_Date"].dt.to_period("M").astype(str)
    data["Order_Year"] = data["Order_Date"].dt.year
    data["Category_Avg_Amount"] = data.groupby("Product_Category")["Total_Amount"].transform("mean")

    return data


DATA_PATH = "ecommerce_sales_data.csv"
try:
    df_raw = load_and_clean_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Couldn't find `{DATA_PATH}`. Place it in the same folder as app.py, or upload it below.")
    uploaded = st.file_uploader("Upload ecommerce_sales_data.csv", type="csv")
    if uploaded is not None:
        df_raw = load_and_clean_data(uploaded)
    else:
        st.stop()

# --------------------------------------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------------------------------------
st.sidebar.markdown("## 🛒 Sales Dashboard")
st.sidebar.caption("Filter the dataset — every chart below updates live.")

with st.sidebar:
    min_date, max_date = df_raw["Order_Date"].min(), df_raw["Order_Date"].max()
    date_range = st.date_input(
        "Order date range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )

    regions = st.multiselect("Region", sorted(df_raw["Region"].dropna().unique()), default=None)
    categories = st.multiselect("Product Category", sorted(df_raw["Product_Category"].dropna().unique()), default=None)
    membership = st.multiselect("Membership Type", sorted(df_raw["Membership_Type"].dropna().unique()), default=None)
    order_status = st.multiselect("Order Status", sorted(df_raw["Order_Status"].dropna().unique()), default=None)

    st.markdown("---")
    st.caption("Data cleaned from raw notebook logic: nulls imputed, duplicate Order_IDs dropped, types coerced.")
    st.caption(f"Rows after cleaning: **{len(df_raw):,}**")

# Apply filters
df = df_raw.copy()
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df = df[(df["Order_Date"] >= start) & (df["Order_Date"] <= end)]
if regions:
    df = df[df["Region"].isin(regions)]
if categories:
    df = df[df["Product_Category"].isin(categories)]
if membership:
    df = df[df["Membership_Type"].isin(membership)]
if order_status:
    df = df[df["Order_Status"].isin(order_status)]

if df.empty:
    st.warning("No rows match the current filters. Try widening your selection.")
    st.stop()

# --------------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------------
st.title("🛒 E-Commerce Sales & Customer Analytics")
st.caption("Interactive dashboard built on cleaned e-commerce order data")

# --------------------------------------------------------------------------------
# KPI ROW
# --------------------------------------------------------------------------------
total_revenue = df["Revenue"].sum()
total_profit = df["Profit"].sum()
total_orders = df["Order_ID"].nunique()
aov = df["Total_Amount"].mean()
avg_rating = df["Rating"].mean()
return_rate = (df["Returned_Product"].astype(str).str.strip().str.lower() == "yes").mean() * 100

kpi_cols = st.columns(6)
kpis = [
    ("Total Revenue", f"₹{total_revenue:,.0f}"),
    ("Total Profit", f"₹{total_profit:,.0f}"),
    ("Total Orders", f"{total_orders:,}"),
    ("Avg Order Value", f"₹{aov:,.0f}"),
    ("Avg Rating", f"{avg_rating:.2f} ★"),
    ("Return Rate", f"{return_rate:.1f}%"),
]
for col, (label, value) in zip(kpi_cols, kpis):
    col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Overview", "🌍 Geography", "👥 Customers", "📦 Products", "🔍 Explore Data"]
)

# ---------------- TAB 1: OVERVIEW ----------------
with tab1:
    c1, c2 = st.columns((2, 1))

    with c1:
        monthly = df.groupby("Order_Month").agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum")
        ).reset_index().sort_values("Order_Month")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly["Order_Month"], y=monthly["Revenue"],
                                  mode="lines+markers", name="Revenue",
                                  line=dict(color=PRIMARY, width=3), fill="tozeroy",
                                  fillcolor="rgba(99,102,241,0.15)"))
        fig.add_trace(go.Scatter(x=monthly["Order_Month"], y=monthly["Profit"],
                                  mode="lines+markers", name="Profit",
                                  line=dict(color="#34d399", width=3)))
        fig.update_layout(title="Revenue & Profit Over Time", template="plotly_dark",
                           height=380, legend=dict(orientation="h", y=1.1),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        status_counts = df["Order_Status"].value_counts().reset_index()
        status_counts.columns = ["Order_Status", "Count"]
        fig2 = px.pie(status_counts, names="Order_Status", values="Count", hole=0.55,
                       color_discrete_sequence=PALETTE)
        fig2.update_layout(title="Order Status Breakdown", template="plotly_dark",
                            height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        cat_rev = df.groupby("Product_Category")["Revenue"].sum().sort_values(ascending=True).reset_index()
        fig3 = px.bar(cat_rev, x="Revenue", y="Product_Category", orientation="h",
                       color="Revenue", color_continuous_scale="Purples")
        fig3.update_layout(title="Revenue by Product Category", template="plotly_dark",
                            height=360, showlegend=False,
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        pay = df["Payment_Method"].value_counts().reset_index()
        pay.columns = ["Payment_Method", "Count"]
        fig4 = px.bar(pay, x="Payment_Method", y="Count", color="Payment_Method",
                       color_discrete_sequence=PALETTE)
        fig4.update_layout(title="Orders by Payment Method", template="plotly_dark",
                            height=360, showlegend=False,
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig4, use_container_width=True)

# ---------------- TAB 2: GEOGRAPHY ----------------
with tab2:
    c1, c2 = st.columns((1, 1))
    with c1:
        region_rev = df.groupby("Region").agg(
            Revenue=("Revenue", "sum"), Orders=("Order_ID", "count")
        ).reset_index().sort_values("Revenue", ascending=False)
        fig = px.bar(region_rev, x="Region", y="Revenue", color="Region",
                     color_discrete_sequence=PALETTE, text_auto=".2s")
        fig.update_layout(title="Revenue by Region", template="plotly_dark", height=420,
                           showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        top_cities = df.groupby("City")["Revenue"].sum().sort_values(ascending=False).head(12).reset_index()
        fig = px.bar(top_cities, x="Revenue", y="City", orientation="h",
                     color="Revenue", color_continuous_scale="Teal")
        fig.update_layout(title="Top 12 Cities by Revenue", template="plotly_dark", height=420,
                           yaxis=dict(categoryorder="total ascending"), showlegend=False,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    warehouse = df.groupby("Warehouse").agg(
        Orders=("Order_ID", "count"), Revenue=("Revenue", "sum"), Avg_Rating=("Rating", "mean")
    ).reset_index().sort_values("Revenue", ascending=False)
    st.markdown("#### Warehouse Performance")
    st.dataframe(warehouse.style.format({"Revenue": "₹{:,.0f}", "Avg_Rating": "{:.2f}"}),
                 use_container_width=True, hide_index=True)

# ---------------- TAB 3: CUSTOMERS ----------------
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(df, x="Age", nbins=25, color_discrete_sequence=[PRIMARY])
        fig.update_layout(title="Customer Age Distribution", template="plotly_dark", height=360,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        gender_counts = df["Gender"].value_counts().reset_index()
        gender_counts.columns = ["Gender", "Count"]
        fig = px.pie(gender_counts, names="Gender", values="Count", hole=0.5,
                     color_discrete_sequence=PALETTE)
        fig.update_layout(title="Gender Split", template="plotly_dark", height=360,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        mem = df.groupby("Membership_Type").agg(
            Revenue=("Revenue", "sum"), Orders=("Order_ID", "count")
        ).reset_index().sort_values("Revenue", ascending=False)
        fig = px.bar(mem, x="Membership_Type", y="Revenue", color="Membership_Type",
                     color_discrete_sequence=PALETTE, text_auto=".2s")
        fig.update_layout(title="Revenue by Membership Tier", template="plotly_dark", height=360,
                           showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        satisfaction = df["Customer_Satisfaction"].value_counts().reset_index()
        satisfaction.columns = ["Customer_Satisfaction", "Count"]
        fig = px.bar(satisfaction, x="Customer_Satisfaction", y="Count",
                     color="Customer_Satisfaction", color_discrete_sequence=PALETTE)
        fig.update_layout(title="Customer Satisfaction Levels", template="plotly_dark", height=360,
                           showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🏆 Top 10 Customers by Spend")
    top_customers = df.groupby(["Customer_ID", "Customer_Name"]).agg(
        Total_Spend=("Total_Amount", "sum"), Orders=("Order_ID", "count"), Avg_Rating=("Rating", "mean")
    ).reset_index().sort_values("Total_Spend", ascending=False).head(10)
    st.dataframe(
        top_customers.style.format({"Total_Spend": "₹{:,.0f}", "Avg_Rating": "{:.2f}"}),
        use_container_width=True, hide_index=True
    )

# ---------------- TAB 4: PRODUCTS ----------------
with tab4:
    c1, c2 = st.columns(2)
    with c1:
        top_products = df.groupby("Product_Name")["Revenue"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_products, x="Revenue", y="Product_Name", orientation="h",
                     color="Revenue", color_continuous_scale="Sunset")
        fig.update_layout(title="Top 10 Products by Revenue", template="plotly_dark", height=420,
                           yaxis=dict(categoryorder="total ascending"), showlegend=False,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        scatter_df = df.copy()
        scatter_df["Quantity_Size"] = scatter_df["Quantity"].abs().clip(lower=1)
        fig = px.scatter(scatter_df, x="Discount", y="Total_Amount", color="Product_Category",
                         size="Quantity_Size", opacity=0.6, color_discrete_sequence=PALETTE)
        fig.update_layout(title="Discount vs Order Value", template="plotly_dark", height=420,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Category Summary")
    cat_summary = df.groupby("Product_Category").agg(
        Orders=("Order_ID", "count"),
        Total_Revenue=("Revenue", "sum"),
        Total_Profit=("Profit", "sum"),
        Avg_Order_Value=("Total_Amount", "mean"),
        Avg_Rating=("Rating", "mean"),
    ).reset_index().sort_values("Total_Revenue", ascending=False)
    st.dataframe(
        cat_summary.style.format({
            "Total_Revenue": "₹{:,.0f}", "Total_Profit": "₹{:,.0f}",
            "Avg_Order_Value": "₹{:,.0f}", "Avg_Rating": "{:.2f}"
        }),
        use_container_width=True, hide_index=True
    )

# ---------------- TAB 5: EXPLORE DATA ----------------
with tab5:
    st.markdown("#### Filtered Dataset")
    st.caption(f"Showing {len(df):,} rows matching your current filters.")
    st.dataframe(df, use_container_width=True, height=500)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data as CSV", data=csv,
                        file_name="filtered_ecommerce_sales.csv", mime="text/csv")

st.markdown("---")
st.caption("Built with Streamlit + Plotly · Data cleaning logic adapted from the original pandas practice notebook.")
