# Data dictionary & output definitions

**olist_orders_dataset.csv** — `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp` plus delivery fields.

**olist_customers_dataset.csv** — `customer_id`, `customer_unique_id`, `customer_state` plus location fields.

### Outputs

- `outputs/dashboard.html`: offline interactive analysis results.
- `outputs/overview.png`: static presentation chart.
- `outputs/metrics.json`: computed KPI values from the selected dataset.
- `outputs/insights.md`: computed insight / interpretation memo.
- Additional `outputs/*.csv`: processed tables for auditing calculations.

### Ethics

The included `data/raw/` CSVs are synthetic sample data, not licensed copies of the original public datasets. When presenting analysis to employers, attribute the original public dataset and differentiate observational findings from demonstrated business impact.
