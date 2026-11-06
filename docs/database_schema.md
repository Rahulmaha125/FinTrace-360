# FinTrace 360 — Relational Database Schema & Data Warehouse Design

## 1. Dimensional Star Schema Architecture

FinTrace 360 utilizes a dimensional Star Schema warehouse hosted in PostgreSQL, cleanly separating the `staging` and `analytics` schemas:

```mermaid
erDiagram
    dim_banks ||--o{ dim_accounts : "issues / manages"
    dim_banks ||--o{ fact_transactions : "originates"
    dim_banks ||--o{ fact_transactions : "receives"
    dim_dates ||--o{ fact_transactions : "records on"
    dim_transaction_types ||--o{ fact_transactions : "executed via"
    dim_accounts ||--o{ fact_transactions : "sends"
    dim_accounts ||--o{ fact_transactions : "receives"
    dim_accounts ||--|| fact_account_risk_summary : "profiled by"

    dim_banks {
        string bank_id PK
        string bank_name
        string institution_type
        string country_code
        string risk_rating
    }

    dim_dates {
        int date_key PK
        date full_date
        smallint day_of_month
        smallint month_number
        string month_name
        smallint quarter
        smallint year_number
        string day_name
        boolean is_weekend
    }

    dim_transaction_types {
        string transaction_type PK
        string rail_category
        string settlement_speed
        boolean is_high_value_channel
    }

    dim_accounts {
        bigint account_id PK
        string bank_id FK
        string account_segment
        string country_code
        string account_status
        numeric initial_balance
        boolean is_sar_alert
        bigint sar_start_step
    }

    fact_transactions {
        bigint transaction_id PK
        int date_key FK
        timestamp transaction_timestamp
        bigint source_account_id FK
        bigint target_account_id FK
        string originator_bank_id FK
        string beneficiary_bank_id FK
        string transaction_type FK
        numeric amount
        boolean is_interbank
        boolean is_alerted_tx
        int step_day
    }

    fact_account_risk_summary {
        bigint account_id PK, FK
        int out_tx_count
        int in_tx_count
        int total_tx_count
        numeric total_outflow
        numeric total_inflow
        numeric total_volume
        numeric net_flow
        numeric flow_ratio
        int unique_counterparties
        int total_active_days
        numeric tx_velocity_per_day
        numeric turnover_ratio
        numeric fan_in_index
        numeric fan_out_index
        boolean is_sar_alert
        string risk_tier
    }
```

---

## 2. Table Specifications & Cardinalities

### 2.1 Dimension Tables
- **`analytics.dim_banks` (5 Rows):** Simulated partner banking institutions (`BNK_ALPHA` to `BNK_EPSILON`) with institution classifications (Tier 1 Commercial, Merchant, Private Wealth).
- **`analytics.dim_dates` (365 Rows):** Date dimension covering calendar dimensions, business days vs weekends, and month/quarter aggregations.
- **`analytics.dim_transaction_types` (4 Rows):** Payment rails (`WIRE`, `ACH_TRANSFER`, `INTERNAL_TRANSFER`, `INSTANT_PAY`) mapped to settlement mechanisms.
- **`analytics.dim_accounts` (20,000 Rows):** Dimension entity for customer accounts with initial balances, segments, and baseline AML alert flags.

### 2.2 Fact Tables
- **`analytics.fact_transactions` (120,558 Rows):** Granular transaction event table containing exact payment amounts, timestamps, counterparty account references, and cross-bank indicators.
- **`analytics.fact_account_risk_summary` (20,000 Rows):** Pre-aggregated behavioral fact table capturing cumulative turnover, velocity, network fan-in/fan-out ratios, and multi-tier risk ratings (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

---

## 3. Indexing Strategy & Performance Optimization

To deliver sub-second query response times across analytical CTEs and Power BI import queries, specific composite and B-tree indexes are implemented:
- `idx_fact_tx_date` on `(date_key)`: Optimizes time-series filtering and rolling 7-day window calculations.
- `idx_fact_tx_src` & `idx_fact_tx_dst` on `(source_account_id)` and `(target_account_id)`: Enables instantaneous graph edge joins and counterparty corridor aggregations.
- `idx_fact_tx_alert` on `(is_alerted_tx)`: Accelerates compliance alert slicing and SAR volume filtering.
- `idx_fact_tx_amount` on `(amount)`: Powers ticket size segmentation and high-value wire analysis.
