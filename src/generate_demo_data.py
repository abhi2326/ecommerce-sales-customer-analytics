"""Create deterministic synthetic source tables for an immediately runnable demo.

These records are fabricated. They are not a sample of, or derived from, Olist.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "demo"
RNG = np.random.default_rng(42)


def main(n_orders: int = 3200) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n_customers = int(n_orders * 0.82)
    customers = pd.DataFrame({
        "customer_id": [f"cust_{i:05d}" for i in range(n_customers)],
        "customer_unique_id": [f"person_{i:05d}" for i in range(n_customers)],
        "customer_zip_code_prefix": RNG.integers(1000, 99999, n_customers),
        "customer_city": RNG.choice(["sao paulo", "rio de janeiro", "belo horizonte", "curitiba", "recife", "salvador"], n_customers),
        "customer_state": RNG.choice(["SP", "RJ", "MG", "PR", "PE", "BA"], n_customers, p=[.42,.17,.14,.1,.09,.08]),
    })
    n_products = 420
    categories = [f"category_{i:02d}" for i in range(1, 72)]
    products = pd.DataFrame({
        "product_id": [f"prod_{i:04d}" for i in range(n_products)],
        "product_category_name": RNG.choice(categories, n_products),
        "product_weight_g": RNG.integers(100, 12000, n_products),
        "product_length_cm": RNG.integers(10, 80, n_products),
        "product_height_cm": RNG.integers(2, 50, n_products),
        "product_width_cm": RNG.integers(5, 60, n_products),
    })
    sellers = pd.DataFrame({
        "seller_id": [f"seller_{i:03d}" for i in range(1, 91)],
        "seller_zip_code_prefix": RNG.integers(1000, 99999, 90),
        "seller_city": RNG.choice(["sao paulo", "rio de janeiro", "curitiba", "recife"], 90),
        "seller_state": RNG.choice(["SP", "RJ", "PR", "PE"], 90),
    })
    start = np.datetime64("2017-01-01")
    purchase = start + RNG.integers(0, 640, n_orders).astype("timedelta64[D]")
    order_ids = [f"order_{i:06d}" for i in range(n_orders)]
    customer_idx = RNG.integers(0, n_customers, n_orders)
    orders = pd.DataFrame({
        "order_id": order_ids,
        "customer_id": customers.iloc[customer_idx].customer_id.to_numpy(),
        "order_status": "delivered",
        "order_purchase_timestamp": pd.to_datetime(purchase).astype(str),
    })
    approved = pd.to_datetime(purchase) + pd.to_timedelta(RNG.integers(0, 2, n_orders), unit="D")
    delivered = approved + pd.to_timedelta(RNG.integers(3, 23, n_orders), unit="D")
    estimated = delivered + pd.to_timedelta(RNG.choice([-5,-2,0,2,5,8], n_orders, p=[.04,.08,.30,.28,.2,.1]), unit="D")
    # Late when actual delivery is after estimate. Ensure a realistic mix.
    orders["order_approved_at"] = approved.astype(str)
    orders["order_delivered_customer_date"] = delivered.astype(str)
    orders["order_estimated_delivery_date"] = estimated.astype(str)
    orders["order_delivered_carrier_date"] = (approved + pd.to_timedelta(RNG.integers(1, 4, n_orders), unit="D")).astype(str)

    item_rows = []
    for i, oid in enumerate(order_ids):
        count = int(RNG.choice([1,2,3], p=[.76,.20,.04]))
        for j in range(1, count + 1):
            pidx = int(RNG.integers(0, n_products))
            item_rows.append((oid, j, products.iloc[pidx].product_id, sellers.iloc[int(RNG.integers(0, len(sellers)))].seller_id,
                              round(float(RNG.lognormal(3.35, .75)), 2), round(float(RNG.uniform(5, 35)), 2)))
    items = pd.DataFrame(item_rows, columns=["order_id","order_item_id","product_id","seller_id","price","freight_value"])
    payments = pd.DataFrame({
        "order_id": order_ids,
        "payment_sequential": 1,
        "payment_type": RNG.choice(["credit_card","boleto","voucher","debit_card"], n_orders, p=[.72,.18,.06,.04]),
        "payment_installments": RNG.choice([1,2,3,4,6,10], n_orders, p=[.34,.12,.12,.1,.18,.14]),
    })
    items["line_total"] = items["price"] + items["freight_value"]
    order_totals = items.groupby("order_id")["line_total"].sum().reindex(order_ids).to_numpy()
    payments["payment_value"] = np.round(order_totals, 2)
    # Delayed deliveries are more likely to receive lower reviews.
    late_days = (pd.to_datetime(orders.order_delivered_customer_date) - pd.to_datetime(orders.order_estimated_delivery_date)).dt.days.to_numpy()
    base = np.where(late_days > 0, 2.8, 4.35)
    scores = np.clip(np.rint(base + RNG.normal(0, 1.0, n_orders)), 1, 5).astype(int)
    reviews = pd.DataFrame({"review_id": [f"review_{i:06d}" for i in range(n_orders)], "order_id": order_ids,
                            "review_score": scores, "review_comment_title": "", "review_comment_message": "",
                            "review_creation_date": (pd.to_datetime(orders.order_delivered_customer_date) + pd.to_timedelta(2, unit="D")).astype(str),
                            "review_answer_timestamp": (pd.to_datetime(orders.order_delivered_customer_date) + pd.to_timedelta(3, unit="D")).astype(str)})
    translations = pd.DataFrame({"product_category_name": categories, "product_category_name_english": [c.replace("category_", "Category ") for c in categories]})
    tables = {"olist_customers_dataset.csv": customers, "olist_orders_dataset.csv": orders,
              "olist_order_items_dataset.csv": items, "olist_order_payments_dataset.csv": payments,
              "olist_order_reviews_dataset.csv": reviews, "olist_products_dataset.csv": products,
              "olist_sellers_dataset.csv": sellers, "product_category_name_translation.csv": translations}
    for name, df in tables.items():
        df.to_csv(OUT / name, index=False)
    print(f"Created {len(tables)} synthetic demo tables in {OUT}")

if __name__ == "__main__":
    main()
