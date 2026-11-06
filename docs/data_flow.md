# FinTrace 360 — End-to-End Data Flow & Lineage Specification

## 1. Data Pipeline Architecture Overview

The FinTrace 360 data pipeline follows a strict unidirectional flow designed for reproducibility, data provenance, and memory efficiency:

```mermaid
flowchart TD
    subgraph RawLayer["1. RAW INGESTION LAYER"]
        A1["IBM AMLSim Benchmark<br/>(accounts.csv, transactions.csv)"]
        A2["PaySim Benchmark<br/>(paysim_sample.csv)"]
        A3["IEEE-CIS Benchmark<br/>(train_transaction_sample.csv)"]
    end

    subgraph ValidationLayer["2. DATA QUALITY & AUDIT LAYER"]
        B1["quality_checker.py<br/>Null audits, duplicate checks, domain boundaries"]
        B2["Referential Integrity Audit<br/>100% foreign key match"]
    end

    subgraph CleaningLayer["3. CLEANING & STANDARDIZATION LAYER"]
        C1["amlsim_cleaner.py<br/>Type casting, surrogate keys, banking dimensions"]
        C2["Clean CSV Exports<br/>(amlsim_accounts_clean.csv, amlsim_transactions_clean.csv)"]
    end

    subgraph FeatureLayer["4. FEATURE ENGINEERING LAYER"]
        D1["amlsim_features.py<br/>Graph degrees, velocity, turnover ratio, fan-in/fan-out"]
        D2["Account Features Matrix<br/>(amlsim_account_features.csv)"]
    end

    subgraph WarehouseLayer["5. RELATIONAL DATA WAREHOUSE LAYER (POSTGRESQL)"]
        E1["Staging Tables<br/>(staging.stg_amlsim_accounts, staging.stg_amlsim_transactions)"]
        E2["Star Schema Warehouse<br/>(dim_accounts, dim_banks, dim_dates, dim_transaction_types,<br/>fact_transactions, fact_account_risk_summary)"]
        E3["Analytical Views<br/>(vw_executive_kpis, vw_daily_transaction_trends,<br/>vw_bank_performance, vw_aml_alert_triage)"]
    end

    subgraph ConsumptionLayer["6. CONSUMPTION & ANALYTICS LAYER"]
        F1["Power BI Dashboards<br/>(Executive Overview, Transaction Analytics, AML Risk Triage)"]
        F2["Machine Learning Pipeline<br/>(Logistic Regression, Random Forest, XGBoost, Isolation Forest)"]
        F3["Executive Reports<br/>(Business Insights, Data Quality, ML Evaluation)"]
    end

    A1 --> B1
    A2 & A3 --> B1
    B1 --> B2 --> C1 --> C2
    C2 --> D1 --> D2
    C2 --> E1 --> E2 --> E3
    E3 --> F1
    D2 --> F2
    E3 & F2 --> F3
```

---

## 2. Stage-by-Stage Lineage & Transformations

### Stage 1: Raw Ingestion (`src/ingestion/`)
- Raw files preserved with immutability in `data/raw/`.
- Memory tracking ensures datasets load well within 8 GB RAM limitations.

### Stage 2: Quality Assurance & Validation (`src/validation/`)
- Audits null counts, primary key collisions, negative values, and orphan foreign keys.
- Discovered 1,684 identical-day repeat transfers and 15 self-loops, resolving them through surrogate sequence keys.

### Stage 3: Dimensional Standardization (`src/cleaning/`)
- Assigns multi-bank identities (`BNK_ALPHA` to `BNK_EPSILON`) based on realistic market share weights.
- Generates calendar timestamps from simulation steps.
- Derives transaction channels (`WIRE`, `ACH_TRANSFER`, `INTERNAL_TRANSFER`, `INSTANT_PAY`).

### Stage 4: Feature Engineering (`src/features/`)
- Transforms raw transaction logs into account-level network vectors.
- Calculates graph in-degree, out-degree, total turnover, flow ratio, and smurfing indices (`fan_in_index`, `fan_out_index`).

### Stage 5: Relational Warehouse Ingestion (`sql/`, `src/database/`)
- Bulk loads staging tables via PostgreSQL `\copy`.
- Transforms staging into a certified dimensional Star Schema with 100% referential integrity.

### Stage 6: Business Intelligence & ML (`powerbi/`, `src/ml/`)
- Analytical views feed Power BI Desktop dashboards.
- Engineered feature matrix feeds supervised classifiers and unsupervised Isolation Forest.
