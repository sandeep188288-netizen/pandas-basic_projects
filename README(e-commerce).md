# 🛒 E-Commerce Sales Dashboard (Streamlit)

An interactive dashboard for the `ecommerce_sales_data.csv` dataset, built on top
of the cleaning logic from your original pandas practice notebook (missing value
imputation, duplicate removal, dtype fixes, date parsing).

## What's inside
- `app.py` — the Streamlit app
- `requirements.txt` — Python dependencies
- `ecommerce_sales_data.csv` — your dataset (place it alongside `app.py`)

## Features
- KPI cards: revenue, profit, orders, AOV, avg rating, return rate
- Sidebar filters: date range, region, category, membership tier, order status
- Tabs: Overview, Geography, Customers, Products, and a raw data explorer with CSV export
- Dark, modern UI using Plotly dark theme + custom CSS

## Run it locally

```bash
# 1. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Make sure ecommerce_sales_data.csv is in the same folder as app.py

# 4. Run the app
streamlit run app.py
```

It will open automatically at `http://localhost:8501`.

## Deploy for free on Streamlit Community Cloud

1. Create a new GitHub repo and push these three files (`app.py`,
   `requirements.txt`, `ecommerce_sales_data.csv`) to it.
2. Go to **https://share.streamlit.io** and sign in with GitHub.
3. Click **"New app"**, pick your repo/branch, and set the main file path to
   `app.py`.
4. Click **Deploy**. In a minute or two you'll get a public URL like
   `https://your-app-name.streamlit.app`.

That's it — every time you push new commits to the repo, the app auto-updates.

## Notes
- If the CSV isn't found next to `app.py`, the app will show a file uploader
  so you (or anyone you share the deployed link with) can drop in the CSV
  manually.
- All charts respect the sidebar filters, including the date range, so this
  can be used as a general-purpose exploration tool, not just a fixed report.
