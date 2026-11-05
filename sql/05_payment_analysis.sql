SELECT payment_type, COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(payment_value),2) AS payment_value_brl,
       ROUND(AVG(payment_installments),2) AS avg_installments
FROM fact_order_items
GROUP BY payment_type
ORDER BY payment_value_brl DESC;
