# Methodology and analytical caveats

1. **Load:** read the eight required source CSVs. Geolocation is optional because no map is required for the core dashboard.
2. **Parse timestamps:** coerce malformed timestamp strings to null and use UTC-aware timestamps.
3. **Aggregate before joining:** payments and reviews can contain multiple records per order. Aggregate them to one row per order before joining to order items; otherwise the fact table would fan out and inflate GMV.
4. **Join:** start from order items and attach order, customer, product, seller, payment and review attributes using many-to-one validated joins.
5. **Model:** retain one row per order line. Distinct order/customer metrics must use distinct identifiers.
6. **Validate:** check non-empty fact, non-null order key, unique order-line grain, non-negative GMV and customer-key coverage.

## Interpretation cautions

- The source is historical (2016–2018) and Brazil-specific. It is not representative of today's e-commerce market or India.
- Olist's `customer_id` identifies the customer record for an order; use `customer_unique_id` to identify repeat customers.
- The source includes cancelled/unavailable orders. Revenue and delivery metrics should be filtered to relevant statuses where the business question requires it. This project retains statuses in the fact table so analysts can choose and disclose their policy. For delivered-order satisfaction analysis, filter to delivered orders with both delivery timestamps and a review.
- `payment_value` is an order-level aggregate repeated on each order item in the fact table. Do not sum it at item grain. Use it only after deduplicating to one row per order, or build a separate order-payment fact table.
- Review score is repeated across an order's line items. Use one row per order or a distinct-order aggregation for review analysis.
- A correlation between late delivery and lower review score is observational; it does not establish causation.
- The resume example's exact figures (for example, category count responsible for 80% of revenue and the review-score gap) must be recomputed on the real dataset and should only be quoted if the result matches the final analysis.
