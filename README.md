# E-Commerce Sales Ledger — Streamlit App

An interactive dashboard for `ecommerce_sales_data.csv`, built with the same
cleaning steps as the original notebook (median-fill on numeric columns,
dedupe on `Order_ID`, gender/price/profit normalization, date parsing).

## Files
- `app.py` — the Streamlit app
- `requirements.txt` — dependencies
- `ecommerce_sales_data.csv` — your data (the app also lets you upload a CSV
  from the sidebar if you'd rather not commit the file)

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Deploy to Streamlit Community Cloud (free)

1. Create a new GitHub repo and push these three files to it (keep them at
   the repo root, or note the folder path for step 4).
2. Go to **share.streamlit.io** and sign in with GitHub.
3. Click **New app**, pick your repo and branch.
4. Set **Main file path** to `app.py`.
5. Click **Deploy**. Streamlit Cloud installs `requirements.txt`
   automatically and gives you a public URL.

If you don't want the CSV in your repo, skip step 1 for that file — the app
has a file-uploader in the sidebar as a fallback, so anyone can drop the CSV
in at runtime instead.

## Other ways to deploy
- **Hugging Face Spaces**: create a Space with the "Streamlit" SDK, upload
  the same three files.
- **Render / Railway**: use a standard Python web service with the start
  command `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.
- **Your own server**: `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`
  behind a reverse proxy (nginx/Caddy).
