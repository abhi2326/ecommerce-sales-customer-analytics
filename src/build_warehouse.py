"""Build a clean analytics mart and SQLite warehouse from Olist-shaped CSV files."""
from pathlib import Path
import argparse
import sqlite3
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["olist_orders_dataset.csv", "olist_customers_dataset.csv", "olist_order_items_dataset.csv",
            "olist_order_payments_dataset.csv", "olist_order_reviews_dataset.csv", "olist_products_dataset.csv",
            "olist_sellers_dataset.csv", "product_category_name_translation.csv"]
DATE_COLS = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
             "order_delivered_customer_date", "order_estimated_delivery_date"]


def read_tables(folder: Path) -> dict[str, pd.DataFrame]:
    missing = [f for f in REQUIRED if not (folder / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files in {folder}: {', '.join(missing)}")
    return {Path(f).stem.replace("_dataset", "").replace("product_category_name_translation", "category_translation"):
            pd.read_csv(folder / f) for f in REQUIRED}


def build(t: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    orders = t["olist_orders"].copy()
    items = t["olist_order_items"].copy()
    customers = t["olist_customers"].copy()
    products = t["olist_products"].copy()
    sellers = t["olist_sellers"].copy()
    payments = t["olist_order_payments"].copy()
    reviews = t["olist_order_reviews"].copy()
    translations = t["category_translation"].copy()

    for c in DATE_COLS:
        if c in orders:
            orders[c] = pd.to_datetime(orders[c], errors="coerce", utc=True)
    # Aggregate many-to-one tables before joining to line items: prevents fan-out.
    pay = payments.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum"), payment_installments=("payment_installments", "max"),
        payment_type=("payment_type", lambda x: x.mode().iat[0] if not x.mode().empty else "unknown"))
    rev = reviews.groupby("order_id", as_index=False).agg(
        review_score=("review_score", "mean"), review_count=("review_id", "nunique"))
    product_dim = products.merge(translations, on="product_category_name", how="left")
    product_dim["category"] = product_dim.get("product_category_name_english", pd.Series(index=product_dim.index, dtype=object)).fillna(product_dim["product_category_name"]).fillna("Unknown")
    product_dim = product_dim.drop(columns=[c for c in ["product_category_name_english"] if c in product_dim])

    fact = items.merge(orders, on="order_id", how="left", validate="many_to_one")
    fact = fact.merge(customers, on="customer_id", how="left", validate="many_to_one")
    fact = fact.merge(product_dim[["product_id", "category"]], on="product_id", how="left", validate="many_to_one")
    fact = fact.merge(sellers[["seller_id", "seller_state", "seller_city"]], on="seller_id", how="left", validate="many_to_one")
    fact = fact.merge(pay, on="order_id", how="left", validate="many_to_one")
    fact = fact.merge(rev, on="order_id", how="left", validate="many_to_one")
    fact["category"] = fact["category"].fillna("Unknown")
    fact["customer_unique_id"] = fact["customer_unique_id"].fillna(fact["customer_id"])
    fact["gmv"] = pd.to_numeric(fact["price"], errors="coerce").fillna(0)
    fact["freight_value"] = pd.to_numeric(fact["freight_value"], errors="coerce").fillna(0)
    fact["line_total"] = fact["gmv"] + fact["freight_value"]
    fact["delivery_days"] = (fact["order_delivered_customer_date"] - fact["order_purchase_timestamp"]).dt.total_seconds() / 86400
    fact["is_late"] = np.where(fact["order_delivered_customer_date"].notna() & fact["order_estimated_delivery_date"].notna(),
                               (fact["order_delivered_customer_date"] > fact["order_estimated_delivery_date"]).astype(int), np.nan)
    fact["purchase_date"] = fact["order_purchase_timestamp"].dt.date.astype("string")
    fact["year_month"] = fact["order_purchase_timestamp"].dt.strftime("%Y-%m")

    # Keep the model at order-item grain and select analytical columns.
    fact_cols = ["order_id","order_item_id","customer_id","customer_unique_id","product_id","seller_id","purchase_date","year_month",
                 "order_status","customer_city","customer_state","seller_city","seller_state","category","price","freight_value","gmv","line_total",
                 "payment_value","payment_type","payment_installments","review_score","review_count","delivery_days","is_late"]
    fact = fact[[c for c in fact_cols if c in fact]].copy()

    dim_customer = customers.drop_duplicates("customer_id").copy()
    dim_product = product_dim.drop_duplicates("product_id").copy()
    dim_seller = sellers.drop_duplicates("seller_id").copy()
    dim_order = orders.drop_duplicates("order_id").copy()
    date_values = pd.to_datetime(orders["order_purchase_timestamp"].dropna()).dt.normalize().drop_duplicates().sort_values()
    dim_date = pd.DataFrame({"date": date_values.dt.strftime("%Y-%m-%d"), "year": date_values.dt.year,
                             "quarter": date_values.dt.quarter, "month": date_values.dt.month,
                             "month_name": date_values.dt.month_name(), "year_month": date_values.dt.strftime("%Y-%m"),
                             "day_of_week": date_values.dt.day_name()})
    return {"fact_order_items": fact, "dim_customer": dim_customer, "dim_product": dim_product,
            "dim_seller": dim_seller, "dim_order": dim_order, "dim_date": dim_date}


def quality_checks(mart: dict[str, pd.DataFrame]) -> list[str]:
    f = mart["fact_order_items"]
    errors = []
    if f.empty: errors.append("Fact table is empty")
    if f.duplicated(["order_id", "order_item_id"]).any(): errors.append("Duplicate order_id + order_item_id grain")
    if f["order_id"].isna().any(): errors.append("Null order_id in fact table")
    if (f["gmv"] < 0).any(): errors.append("Negative GMV found; investigate source adjustments")
    if f["customer_id"].isna().mean() > .01: errors.append("More than 1% of fact rows lack customer_id")
    if errors: raise ValueError("Data quality checks failed:\n- " + "\n- ".join(errors))
    return [f"PASS: {len(f):,} order-item rows", f"PASS: {f.order_id.nunique():,} distinct orders",
            f"PASS: {f.customer_unique_id.nunique():,} unique customers", "PASS: order-item grain is unique"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["demo", "raw"], default="demo")
    args = parser.parse_args()
    folder = ROOT / "data" / ("demo" if args.source == "demo" else "raw")
    out = ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    tables = read_tables(folder)
    mart = build(tables)
    checks = quality_checks(mart)
    for name, df in mart.items():
        df.to_csv(out / f"{name}.csv", index=False)
    db = out / "warehouse.sqlite"
    if db.exists(): db.unlink()
    with sqlite3.connect(db) as con:
        for name, df in mart.items(): df.to_sql(name, con, index=False)
    (out / "quality_report.txt").write_text("\n".join(checks) + f"\nSource mode: {args.source}\n", encoding="utf-8")
    print("\n".join(checks))
    print(f"Warehouse created: {db}")

if __name__ == "__main__":
    main()
