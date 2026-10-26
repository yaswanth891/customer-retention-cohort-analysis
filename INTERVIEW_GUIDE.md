# Interview explanation / walkthrough

**Project:** Customer Retention & Cohort Analysis

**What it does:** Monthly new-customer cohorts, calendar-month repurchase retention, and eligible 30-day repeat-purchase rate.

**Workflow:** Load validated CSV → compute SQL or Python metrics → render KPI dashboard → explain limits → propose next product action.

**Q: Why use customer_unique_id?**

A: Olist customer_id is usually an order-linked ID; customer_unique_id connects repeat purchases.

**Q: Why exclude incomplete periods?**

A: Recent buyers have had fewer chances to return, producing mechanically low apparent retention.

**Q: Is this customer lifetime value?**

A: No. The study uses no prices or profit, so LTV cannot be calculated.

**Important:** The bundled outputs are synthetic demonstrations. Re-run on genuine public data before discussing any dataset-specific results in interviews.
