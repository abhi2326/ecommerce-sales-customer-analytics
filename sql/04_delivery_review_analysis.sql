-- Compare average review scores for on-time vs late deliveries.
WITH order_level AS (
  SELECT order_id, MAX(is_late) AS is_late, AVG(review_score) AS review_score,
         MAX(delivery_days) AS delivery_days
  FROM fact_order_items
  GROUP BY order_id
)
SELECT CASE WHEN is_late = 1 THEN 'Late' WHEN is_late = 0 THEN 'On time' ELSE 'Unknown' END AS delivery_status,
       COUNT(*) AS orders,
       ROUND(AVG(review_score),2) AS average_review_score,
       ROUND(AVG(delivery_days),2) AS average_delivery_days
FROM order_level
GROUP BY delivery_status;

-- State-level delivery performance
SELECT customer_state, COUNT(DISTINCT order_id) AS orders,
       ROUND(AVG(is_late) * 100,2) AS late_delivery_rate_pct,
       ROUND(AVG(review_score),2) AS average_review_score
FROM fact_order_items
GROUP BY customer_state
ORDER BY late_delivery_rate_pct DESC;
