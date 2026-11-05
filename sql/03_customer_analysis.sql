-- Customer repeat-purchase summary; customer_unique_id is the customer-level key.
WITH customer_orders AS (
  SELECT customer_unique_id, COUNT(DISTINCT order_id) AS order_count,
         SUM(gmv) AS lifetime_gmv, MIN(purchase_date) AS first_purchase
  FROM fact_order_items
  GROUP BY customer_unique_id
)
SELECT CASE WHEN order_count > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type,
       COUNT(*) AS customers,
       ROUND(AVG(lifetime_gmv),2) AS avg_customer_gmv
FROM customer_orders
GROUP BY customer_type;

-- RFM-style recency, frequency and monetary values (reference date = latest purchase date in data)
WITH customer_rfm AS (
  SELECT customer_unique_id,
         CAST(julianday((SELECT MAX(purchase_date) FROM fact_order_items)) - julianday(MAX(purchase_date)) AS INTEGER) AS recency_days,
         COUNT(DISTINCT order_id) AS frequency,
         ROUND(SUM(gmv),2) AS monetary_brl
  FROM fact_order_items GROUP BY customer_unique_id
)
SELECT * FROM customer_rfm ORDER BY monetary_brl DESC;
