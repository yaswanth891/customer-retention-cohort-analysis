# Product insight memo — Customer Retention

**Dataset:** Synthetic demonstration data (not actual shoppers)

**Business question:** What share of customers make another purchase, and which first-purchase cohorts stay active?

## Metrics and findings

- **19,432** delivered orders from **14,577** distinct buyers (`customer_unique_id`).
- **14,568** buyers are eligible for a fully observed 30-day repeat window.
- **6.37%** of eligible buyers placed another delivered order within 30 days.
- Cohort heatmap is **the fraction of cohort customers who purchase in calendar month M1..M5**, not a survival curve. Month 0 is 100%.

## Product recommendations

1. Investigate the timing and customer segment of return purchases, without confusing correlation with causal impact.
2. Prototype a post-purchase retention email or discount experiment; measure 30-day repeat purchase against a control group.
3. Segment by geography only when sample sizes support it; do not assume the causes of differences.

## Limitations

Exclude orders not marked delivered. Last observed month is treated as incomplete for cohort cells. 30-day repeat is measured only for fully eligible users. No order-item prices are used, so **this project does not estimate customer lifetime value (LTV)**. No uplift claims are made. Synthetic demo results are not real business evidence.
