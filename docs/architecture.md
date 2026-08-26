# Architecture

```text
Excel / CSV Inputs
        ↓
FastAPI Import and Validation
        ↓
SQLAlchemy Data Layer
        ↓
PostgreSQL / Local SQLite
        ↓
Metrics and Diagnostic APIs
        ↓
React + TypeScript + ECharts Dashboard
```

The production application is packaged with Docker. The public repository intentionally omits production credentials, databases, raw exports, and internal deployment handover material.
