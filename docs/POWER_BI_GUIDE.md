# Power BI report build guide

## 1. Load data

Use **Get Data → Text/CSV** and load `fact_order_items.csv`, `dim_customer.csv`, `dim_product.csv`, `dim_seller.csv`, `dim_order.csv`, and `dim_date.csv` from `data/processed/`. Alternatively, connect to `warehouse.sqlite` using a SQLite connector.

## 2. Relationships

Create one-to-many, single-direction relationships from each dimension to the fact:

- `dim_customer[customer_id]` → `fact_order_items[customer_id]`
- `dim_product[product_id]` → `fact_order_items[product_id]`
- `dim_seller[seller_id]` → `fact_order_items[seller_id]`
- `dim_order[order_id]` → `fact_order_items[order_id]`
- `dim_date[date]` → `fact_order_items[purchase_date]`

Set `dim_date` as the date table. Ensure date columns are typed as Date.

## 3. Measures

Copy measures from `dax/measures.dax`. Add a measure for freight and avoid summing `payment_value` over line rows.

## 4. Suggested report pages

**Executive Overview**
- KPI cards: GMV, Orders, AOV, Customers, Late Delivery Rate
- Monthly GMV line chart
- Top 10 categories bar chart
- State-level GMV map/bar chart

**Product & Category**
- Category GMV and revenue share
- Pareto cumulative revenue line
- Product/category slicers

**Customer**
- Unique customers, one-time vs repeat customer split
- RFM table/segment chart
- Customer state distribution

**Delivery & Satisfaction**
- Late vs on-time average review score
- Late delivery rate by state/category
- Average delivery days and review score trend

## 5. Formatting

Import `assets/powerbi-theme.json` via View → Themes → Browse for themes. Format monetary values as BRL (R$), percentages to one decimal, and review scores to two decimals. Add a footer noting the 2016–2018 observation period and source attribution.
