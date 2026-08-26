# UZUM Operations BI Dashboard

An AI-assisted business intelligence dashboard for daily e-commerce operations, integrating sales, inventory, traffic, conversion, returns, and cancellation data into one operational view.

> **Portfolio Project**  
> All public data and examples in this repository are anonymized or recreated. The original production repository remains private.

**Live Demo:** [UZUM Operations BI](https://uzum-bi-production.up.railway.app/)

## Table of Contents

- [Project Overview](#project-overview)
- [Business Context](#business-context)
- [Problems to Solve](#problems-to-solve)
- [Core Metrics](#core-metrics)
- [Key Features](#key-features)
- [Dashboard Structure](#dashboard-structure)
- [Business Logic](#business-logic)
- [Impact](#impact)
- [Screenshots](#screenshots)
- [My Contribution](#my-contribution)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Run Locally](#run-locally)
- [Data Privacy](#data-privacy)
- [Future Improvements](#future-improvements)

## Project Overview

The **UZUM Operations BI Dashboard** is an operational analytics project built to improve the efficiency and consistency of daily e-commerce management.

Before this project, sales, inventory, and traffic data were processed manually across multiple Excel files. Daily reporting required repeated cleaning, matching, calculation, and validation. The dashboard turns this workflow into a structured monitoring system by integrating multiple sources, standardizing business metrics, retaining historical records, and highlighting operational anomalies.

## Business Context

The project supports daily e-commerce operations across product categories such as smartphones, tablets, and wearable devices. Operational decisions require continuous monitoring of:

- Sales and GMV performance
- Inventory availability and Days of Supply
- Traffic and conversion efficiency
- Returns and cancellations
- SKU / SPU performance
- Historical inventory and traffic trends

## Problems to Solve

### 1. Fragmented data sources

Sales, traffic, and inventory data came from separate files and required repeated manual integration.

### 2. Time-consuming daily reporting

Significant time was spent cleaning data, matching product information, calculating indicators, and checking consistency.

### 3. Limited historical retention

Daily inventory and traffic snapshots were not always retained, making historical trend analysis difficult.

### 4. Slow anomaly detection

Abnormal changes in conversion, inventory, sales, returns, or cancellations could not always be identified quickly.

### 5. Repetitive operational analysis

The same calculation and diagnostic logic had to be applied manually every day.

## Core Metrics

| Metric | Description |
|---|---|
| SO | Net sales volume after returns and cancellations according to business logic |
| GMV | Gross Merchandise Value |
| ASP | Average Selling Price |
| UV | Unique Visitors or the available traffic proxy |
| CVR | Conversion Rate |
| DOS | Days of Supply |
| Inventory | Current sellable stock |
| Return Volume | Returned order volume |
| Cancellation Volume | Cancelled order volume |
| Return Rate | Share of returned orders |
| WoW / DoD Change | Weekly or daily performance change |

Detailed definitions are available in [docs/metric-definitions.md](docs/metric-definitions.md).

## Key Features

### Multi-source Data Integration

Combines sales, inventory, and traffic files in a unified processing workflow.

### Business Metric Calculation

Calculates operational KPIs from standardized business rules.

### Sales Performance Monitoring

Tracks overall, category-level, and SKU-level SO, GMV, ASP, and conversion performance.

### Inventory Monitoring

Monitors current inventory, Days of Supply, and potential replenishment or slow-stock risks.

### Traffic and Conversion Analysis

Tracks traffic and CVR changes to identify traffic-quality or product-conversion issues.

### Return and Cancellation Monitoring

Separates cancellation and refund scenarios and supports product-level diagnosis.

### Historical Data Retention

Stores daily inventory and traffic snapshots for trend analysis and period comparison.

### Operational Alerts

Highlights missing data, unusual changes, stock-outs, and other conditions requiring attention.

## Dashboard Structure

1. **Business Overview** — SO, GMV, ASP, UV, CVR, inventory, and DOS
2. **Category Performance** — performance across major product groups
3. **SKU / SPU Analysis** — product-level monitoring and comparison
4. **Inventory and Replenishment** — stock health and replenishment priorities
5. **Traffic and Conversion** — traffic and funnel performance over time
6. **Returns and Cancellations** — after-sales operational risks
7. **Historical Data** — retained traffic and inventory snapshots
8. **Data Quality** — missing dates, incomplete sources, and upload history

## Business Logic

The project is more than a visualization layer. A major part of the work was translating operational experience into reusable rules, including:

- Net sales calculation
- ASP calculation
- SKU / SPU grouping
- Inventory risk identification
- DOS monitoring
- Conversion anomaly detection
- Return / cancellation classification
- Daily and weekly comparison logic

These rules later became the foundation of the [UZUM AI Operations Agent](https://github.com/UZUMMP1/uzum-ai-operations-agent).

## Impact

### Before

- Manual data cleaning and cross-file matching
- Repeated spreadsheet calculations
- Manual KPI validation
- Manual anomaly identification
- Limited historical-data retention

### After

- Standardized KPI calculations
- Automated multi-source processing
- Faster operational monitoring
- Historical data retention
- More structured anomaly identification

**Daily data-processing time was reduced from approximately 4+ hours to around 30 minutes.**

## Screenshots

> Replace these placeholders with anonymized screenshots before publishing the final portfolio.

### Business Overview

![Business Overview placeholder](assets/screenshot-placeholder.svg)

### Sales and Category Performance

![Category Performance placeholder](assets/screenshot-placeholder.svg)

### Inventory Monitoring

![Inventory Monitoring placeholder](assets/screenshot-placeholder.svg)

### Traffic and Conversion

![Traffic and Conversion placeholder](assets/screenshot-placeholder.svg)

### Returns and Cancellations

![Returns and Cancellations placeholder](assets/screenshot-placeholder.svg)

## My Contribution

I translated operational requirements into the dashboard structure and data logic. My contributions included:

- Defining core business metrics and calculation rules
- Designing the dashboard information architecture
- Mapping recurring operational pain points to product features
- Validating outputs against original spreadsheet reports
- Designing historical inventory and traffic retention
- Designing anomaly-monitoring and data-quality requirements
- Building and iterating the dashboard with AI-assisted coding
- Connecting BI outputs to an AI-supported decision workflow

## Tech Stack

- **Frontend:** React, TypeScript, Vite, ECharts
- **Backend:** FastAPI, Python, SQLAlchemy
- **Database:** PostgreSQL in production; SQLite for local development
- **Deployment:** Docker and Railway
- **Methods:** Data cleaning, metric design, business intelligence, e-commerce operations analysis

## Repository Structure

```text
uzum-operations-bi/
├── README.md
├── assets/
├── sample_data/
│   └── anonymized_sample.csv
├── docs/
│   ├── architecture.md
│   ├── business-logic.md
│   ├── metric-definitions.md
│   └── privacy-checklist.md
└── src/
    ├── backend/
    └── frontend/
```

## Run Locally

The portfolio-safe source extract is under `src/`.

```bash
cd src/backend
python -m venv .venv
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

In another terminal:

```bash
cd src/frontend
corepack enable
pnpm install
pnpm dev
```

Do not use a production database connection when testing the public version.

## Data Privacy

- No confidential company data is published
- No customer information is included
- No API keys or database credentials are included
- Screenshots must be anonymized
- Sample datasets are fully fictional
- The original production repository remains private

See [docs/privacy-checklist.md](docs/privacy-checklist.md) before adding files.

## Future Improvements

- Scheduled data ingestion and validation
- More flexible historical-data management
- Statistical anomaly detection
- Inventory forecasting and replenishment simulation
- Saved daily and weekly business reports
- Permission and account controls
- Deeper integration with an AI Operations Agent
