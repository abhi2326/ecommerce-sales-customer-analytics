# E-Commerce Sales & Customer Analytics

An end-to-end analytics project built around the **Brazilian E-Commerce Public Dataset by Olist**. It demonstrates data ingestion, quality checks, dimensional modelling, SQL analysis, Python analytics, and an interactive Streamlit dashboard.

> **Data note:** The repository ships with a small, deterministic **synthetic demo dataset** so the project runs immediately. It is not Olist data and must not be used to support claims about Olist. To reproduce the analysis on the real ~100k-order dataset, download it from Kaggle and place the nine CSVs in `data/raw/` (instructions below). Raw Olist data is not redistributed here.

## What this project answers

- How are revenue, orders, average order value (AOV), and freight changing over time?
- Which product categories contribute most to revenue, and how concentrated is revenue?
- How do actual delivery delays relate to customer review scores?
- Which states and payment methods contribute most to sales?
- How many customers return, and what does basic RFM segmentation show?

## Architecture

```text
Olist Kaggle CSVs / synthetic demo CSVs
                 |
                 v
        Python + pandas pipeline
                 |
        validation + cleaning
                 |
        star-schema CSV outputs ----> SQLite warehouse
                 |                         |
                 +-------------------------+
                           |
                    Streamlit dashboard
                           |
                  SQL analysis + DAX guide
```

## Repository layout

```text
src/                 Data generation, ingestion, modelling and QA
sql/                 SQLite-compatible analysis queries and schema
assets/              Power BI theme
dax/                 Power BI DAX measures
 data/demo/          Synthetic demo source tables (small)
 data/raw/           Put the real Olist CSVs here (gitignored)
 data/processed/     Pipeline outputs (gitignored)
 docs/                Business brief, data dictionary, methodology, Power BI build guide
notebooks/           Guided analysis walkthrough
 tests/               Automated data-model tests
 app.py               Interactive Streamlit dashboard
```

## Quick start (demo mode)

Requires Python 3.10+.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/generate_demo_data.py
python src/build_warehouse.py --source demo
streamlit run app.py
```

The synthetic demo is intentionally modest in size and labelled as synthetic in the app. It allows you to inspect every page before downloading the full dataset.

## Run on the real Olist dataset

1. Create/sign in to a Kaggle account and accept the dataset terms: <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>.
2. Download the dataset ZIP and extract the nine CSV files into `data/raw/`.
3. Confirm the filenames match the list below.
4. Run:

```bash
python src/build_warehouse.py --source raw
streamlit run app.py
```

Required source files:

- `olist_orders_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv` (optional for this project's core model)
- `product_category_name_translation.csv`

Optional Kaggle CLI download (after configuring `~/.kaggle/kaggle.json`):

```bash
pip install kaggle
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
```

## Data model and metric definitions

The warehouse uses a **star-schema-style model**. `fact_order_items` is at one row per order line (`order_id` + `order_item_id`); dimensions include date, customer, product, seller, and order. Payment and review tables are aggregated to order grain before joining to avoid multiplying item revenue when an order has multiple payments or reviews.

- **Gross merchandise value (GMV):** sum of item price; excludes freight and payment-only adjustments.
- **Freight revenue:** sum of freight value.
- **Total order value:** GMV + freight at order-line grain.
- **Orders:** distinct count of `order_id` (not item rows).
- **AOV:** GMV / distinct orders.
- **Late delivery:** delivered timestamp is later than estimated delivery timestamp. Orders without both timestamps are excluded from this rate.
- **Delivery days:** calendar-day difference between purchase and delivered timestamps.
- **Repeat customer:** customer with more than one distinct order in the available observation window. Olist's customer unique ID is order-specific in the source; use `customer_unique_id` for customer-level analysis.

The dataset spans 2016–2018, so it is a historical case study, not a live/current market view. All monetary amounts are in Brazilian Real (BRL).

## SQL analysis

Run the scripts in `sql/` against the generated `data/processed/warehouse.sqlite` database. They include monthly sales, category Pareto, delivery/review analysis, customer repeat rate, and payment mix.

## Power BI

This repository includes a star-schema guide, a Power BI theme, and copy-ready DAX measures in `dax/measures.dax`. Connect Power BI Desktop to `data/processed/*.csv` (or SQLite via an appropriate connector), create the relationships described in `docs/POWER_BI_GUIDE.md`, then paste the measures. A `.pbix` is not included because Power BI report files are authored and saved by Power BI Desktop itself.

## Quality checks

```bash
pytest -q
```

The pipeline validates required source files, keys, nulls in essential columns, join coverage, and output grain. See `docs/DATA_DICTIONARY.md` and `docs/METHODOLOGY.md` for details.

## Suggested GitHub description

End-to-end e-commerce analytics project using Python, SQL, SQLite and Power BI (DAX). Built a star-schema warehouse from linked transactional tables, added data-quality checks, and developed an interactive dashboard to analyse sales, category concentration, customer retention and delivery performance.

## Attribution and license

Dataset: Olist, *Brazilian E-Commerce Public Dataset by Olist*, Kaggle. Dataset license: **CC BY-NC-SA 4.0** (verify current Kaggle terms before reuse). This repository's original code and documentation are licensed under MIT; that does **not** change the dataset's license. Do not commit Olist raw CSVs to this repository.
