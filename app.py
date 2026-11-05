from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "processed" / "warehouse.sqlite"
st.set_page_config(page_title="E-Commerce | Sales & Customer Analytics", page_icon="📊", layout="wide")
st.title("E-Commerce Sales & Customer Analytics")
st.caption("Olist case study · Python · SQL · dimensional modelling · Power BI-ready metrics")

if not DB.exists():
    st.warning("The analytics warehouse has not been built yet. Run `python src/generate_demo_data.py` and `python src/build_warehouse.py --source demo` from the project root.")
    st.stop()
with sqlite3.connect(DB) as con:
    f = pd.read_sql_query("SELECT * FROM fact_order_items", con)

if f.empty:
    st.error("The fact table is empty. Rebuild the warehouse.")
    st.stop()
f["purchase_date"] = pd.to_datetime(f["purchase_date"], errors="coerce")
f["year_month"] = f["purchase_date"].dt.strftime("%Y-%m")
source_mode = (ROOT / "data" / "processed" / "quality_report.txt").read_text(errors="ignore") if (ROOT / "data" / "processed" / "quality_report.txt").exists() else ""
if "Source mode: demo" in source_mode:
    st.info("DEMO MODE — this dashboard currently uses fabricated synthetic data. Replace it with the real Olist CSVs and rebuild to reproduce real-dataset findings.")

with st.sidebar:
    st.header("Filters")
    dates = f.purchase_date.dropna()
    if not dates.empty:
        min_d, max_d = dates.min().date(), dates.max().date()
        selected = st.date_input("Purchase date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        if isinstance(selected, tuple) and len(selected) == 2:
            f = f[f.purchase_date.dt.date.between(selected[0], selected[1])]
    states = sorted(f.customer_state.dropna().astype(str).unique())
    chosen_states = st.multiselect("Customer state", states, default=states)
    if chosen_states:
        f = f[f.customer_state.isin(chosen_states)]
    cats = sorted(f.category.dropna().astype(str).unique())
    chosen_cats = st.multiselect("Product category", cats)
    if chosen_cats:
        f = f[f.category.isin(chosen_cats)]

orders = f.order_id.nunique()
gmv = f.groupby("order_id").gmv.sum().sum()
aov = gmv / orders if orders else 0
late = f.drop_duplicates("order_id").is_late.dropna()
late_rate = late.mean() if len(late) else 0
avg_review = f.drop_duplicates("order_id").review_score.mean()
cols = st.columns(4)
cols[0].metric("GMV", f"R$ {gmv:,.0f}")
cols[1].metric("Orders", f"{orders:,}")
cols[2].metric("Average order value", f"R$ {aov:,.2f}")
cols[3].metric("Late delivery rate", f"{late_rate:.1%}")
st.caption(f"Average review score: {avg_review:.2f}/5" if pd.notna(avg_review) else "Average review score: unavailable")

left, right = st.columns(2)
with left:
    st.subheader("Monthly GMV")
    monthly = f.groupby("year_month", as_index=False).agg(GMV=("gmv", "sum"), Orders=("order_id", "nunique")).sort_values("year_month")
    st.plotly_chart(px.line(monthly, x="year_month", y="GMV", markers=True, title="GMV by purchase month"), use_container_width=True)
with right:
    st.subheader("Revenue concentration by category")
    category = f.groupby("category", as_index=False).gmv.sum().sort_values("gmv", ascending=False)
    category["cumulative_share"] = category.gmv.cumsum() / category.gmv.sum() if category.gmv.sum() else 0
    st.plotly_chart(px.bar(category.head(15), x="gmv", y="category", orientation="h", title="Top 15 categories by GMV"), use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Delivery performance vs customer reviews")
    order_view = f.drop_duplicates("order_id").dropna(subset=["is_late", "review_score"])
    if not order_view.empty:
        delivery = order_view.groupby("is_late", as_index=False).agg(Avg_review=("review_score", "mean"), Orders=("order_id", "nunique"))
        delivery["Delivery status"] = delivery.is_late.map({0: "On time", 1: "Late"})
        st.plotly_chart(px.bar(delivery, x="Delivery status", y="Avg_review", text_auto=".2f", range_y=[0,5], title="Average review score"), use_container_width=True)
    else:
        st.info("No delivery/review records available for this selection.")
with right:
    st.subheader("Payment mix")
    payment = f.drop_duplicates("order_id").groupby("payment_type", as_index=False).order_id.nunique().rename(columns={"order_id":"Orders"})
    if not payment.empty:
        st.plotly_chart(px.pie(payment, names="payment_type", values="Orders", hole=.45, title="Orders by payment type"), use_container_width=True)

st.subheader("State-level performance")
state = f.groupby("customer_state", as_index=False).agg(GMV=("gmv", "sum"), Orders=("order_id", "nunique"), Customers=("customer_unique_id", "nunique"))
st.dataframe(state.sort_values("GMV", ascending=False), use_container_width=True, hide_index=True)

st.subheader("Category Pareto table")
category["GMV share"] = category.gmv / category.gmv.sum() if category.gmv.sum() else 0
category["Cumulative GMV share"] = category.cumulative_share
st.dataframe(category[["category", "gmv", "GMV share", "Cumulative GMV share"]].head(25).style.format({"gmv":"R$ {:,.2f}","GMV share":"{:.1%}","Cumulative GMV share":"{:.1%}"}), use_container_width=True, hide_index=True)

st.caption("Metric caveat: GMV is item price only; freight is reported separately in the underlying fact table. Order-level KPIs use distinct order IDs to avoid counting multi-item orders more than once.")
