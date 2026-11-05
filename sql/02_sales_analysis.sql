-- Monthly GMV, orders and AOV
SELECT year_month,
       ROUND(SUM(gmv), 2) AS gmv_brl,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(gmv) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS average_order_value_brl
FROM fact_order_items
GROUP BY year_month
ORDER BY year_month;

-- Top categories and cumulative share (SQLite window functions)
WITH category_sales AS (
  SELECT category, SUM(gmv) AS gmv
  FROM fact_order_items
  GROUP BY category
), ranked AS (
  SELECT category, gmv,
         SUM(gmv) OVER (ORDER BY gmv DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_gmv,
         SUM(gmv) OVER () AS total_gmv
  FROM category_sales
)
SELECT category, ROUND(gmv,2) AS gmv,
       ROUND(100.0 * gmv / NULLIF(total_gmv,0),2) AS revenue_share_pct,
       ROUND(100.0 * cumulative_gmv / NULLIF(total_gmv,0),2) AS cumulative_revenue_share_pct
FROM ranked ORDER BY gmv DESC;
