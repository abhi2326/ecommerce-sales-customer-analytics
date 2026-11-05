# Business brief

## Scenario
An online marketplace wants a consolidated view of commercial performance and the customer experience. Source information is spread across order, order-line, customer, product, seller, payment and review files.

## Stakeholder questions
1. Is GMV growing month over month, and what is the average order value?
2. Is revenue concentrated in a small set of categories?
3. Are late deliveries associated with lower review scores?
4. Which customer states and payment methods contribute most to orders and GMV?
5. What proportion of identified customers place more than one order?

## Deliverables
- Reproducible ingestion and cleaning pipeline.
- Validated order-item fact table and conformed dimensions.
- SQLite analytical warehouse and reusable SQL.
- Power BI-ready DAX measures and report specification.
- Interactive Streamlit dashboard for fast exploration.
- Data dictionary, assumptions, limitations and automated tests.

## Definition of done
A clean environment can install dependencies, generate demo data, build the warehouse, pass automated tests, and launch the dashboard using the commands in the README. The real-data workflow is documented separately and does not redistribute the third-party dataset.
