# Data dictionary

## Fact table: `fact_order_items`

**Grain:** one row per `order_id` + `order_item_id`.

| Column | Meaning |
|---|---|
| order_id, order_item_id | Composite order-line identifier |
| customer_id | Source customer/order record key |
| customer_unique_id | Customer-level identifier for repeat analysis |
| product_id, seller_id | Product and seller keys |
| purchase_date, year_month | Purchase date and month bucket |
| order_status | Source order lifecycle status |
| customer_state, customer_city | Customer geography |
| seller_state, seller_city | Seller geography |
| category | English category where translation exists |
| price / gmv | Item price in BRL; GMV is defined as item price |
| freight_value | Shipping charge in BRL |
| line_total | GMV + freight |
| payment_value | Payments summed to order grain before line join; repeated on each order line, so **do not sum this column across item rows** |
| payment_type | Modal payment type at order grain |
| payment_installments | Maximum installment count recorded for the order |
| review_score | Mean review score at order grain |
| review_count | Number of distinct reviews at order grain |
| delivery_days | Purchase-to-delivery elapsed days |
| is_late | 1 if delivered after estimate, 0 if on/before estimate, null if timestamps unavailable |

## Dimensions

- `dim_customer`: customer/order-record attributes. Use `customer_unique_id` for customer-level aggregation.
- `dim_product`: product attributes plus translated `category`.
- `dim_seller`: seller attributes.
- `dim_order`: one row per order and lifecycle timestamps.
- `dim_date`: distinct purchase dates with year, quarter, month, month name and weekday.

## Source tables

The original Olist dataset includes orders, customers, order items, payments, reviews, products, sellers, geolocation, and category translations. Geolocation is optional for the core analysis in this repository.
