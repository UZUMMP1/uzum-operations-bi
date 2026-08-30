# Business Case: From KPI Monitoring to an Operational Decision

> This case uses fictional portfolio data. It does not disclose real company performance.

## Context

The daily reporting process previously required multiple spreadsheets to be cleaned, matched, calculated, and reviewed manually. The objective was not only to visualize results, but to shorten the path from raw data to an operational decision.

## Question

Why did sales remain almost unchanged between 2026-08-02–2026-08-06 and the preceding five-day period?

## Evidence

| Metric | Observation |
|---|---|
| Net sales (SO) | 325 → 327 (+0.6%) |
| UV | Increased 13.6% |
| CVR | Decreased 5.3% |
| ASP | Decreased 5.7% |
| Cancellation / return rate | 23.1%, increasing 30.1% versus the preceding period |
| Sellable inventory | 2,698 → 2,423, a decrease of 275 units |
| Key-SKU stock-outs | 10 high-priority SKUs |
| Positive category contribution | AIOT contributed +16 units |

## Diagnosis

The data did not support a simple “traffic problem” explanation: traffic increased. Instead, the dashboard highlighted four constraints that offset that growth—conversion weakened, ASP decreased, after-sales pressure rose, and several high-contribution SKUs were out of stock.

This is a directional diagnosis, not a claim of proven causality. Price, promotion, competitor, and traffic-source data would be required for deeper causal validation.

## Recommended Actions

1. Replenish the highest-contribution zero-stock SKUs first.
2. Compare CVR by SKU and traffic source before increasing traffic investment.
3. Review the products contributing most to cancellations and returns.
4. Check whether ASP decline came from price changes or a lower-value product mix.
5. Re-run the same diagnostic after the next inventory and traffic refresh.

## My Role

I defined the business question, KPI formulas, comparison logic, inventory-risk rules, information hierarchy, and validation criteria. I used AI-assisted coding as an implementation tool, reviewed the generated work, tested the outputs, and decided how the final workflow should support daily operations.

## Outcome

The project reduced a repeated multi-file reporting workflow from approximately four or more hours to around 30 minutes and created a consistent framework for discussing sales, traffic, conversion, inventory, and after-sales risks together.

