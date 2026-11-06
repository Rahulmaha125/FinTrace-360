# FinTrace 360 — Power BI Dashboard Implementation Guide

This guide details how to load, connect, configure, and visualize the FinTrace 360 analytical reports within Microsoft Power BI Desktop.

---

## 1. Data Connection Architecture

Power BI Desktop connects to the analytical dataset via two methods:

### Method A: PostgreSQL Direct Database Connection (Recommended)
1. Open **Microsoft Power BI Desktop**.
2. Select **Get Data** -> **PostgreSQL Database**.
3. **Server:** `localhost:5432` | **Database:** `fintrace360`.
4. **Data Connectivity mode:** `Import` (for fast in-memory DAX calculation) or `DirectQuery`.
5. In the Navigator window, select the following views and tables from schema `analytics`:
   - `analytics.dim_banks`
   - `analytics.dim_dates`
   - `analytics.dim_transaction_types`
   - `analytics.dim_accounts`
   - `analytics.fact_transactions`
   - `analytics.fact_account_risk_summary`
   - Or directly import the analytical views: `vw_executive_kpis`, `vw_daily_transaction_trends`, `vw_bank_performance`, `vw_aml_alert_triage`.

### Method B: Processed Flat CSV Ingestion (Zero-Dependency Mode)
If PostgreSQL is not running locally, connect directly to the cleaned flat files in `data/processed/`:
1. `amlsim_accounts_clean.csv` -> Load as `dim_accounts`
2. `amlsim_transactions_clean.csv` -> Load as `fact_transactions`
3. `amlsim_account_features.csv` -> Load as `fact_account_risk_summary`

---

## 2. Power BI Data Model (Relationships)

Ensure the following 1-to-many (`1:*`) single-direction relationships are active in the **Model View**:

| From Table (Dimension) | Primary Key Column | To Table (Fact) | Foreign Key Column | Cardinality | Cross Filter |
|:---|:---|:---|:---|:---:|:---:|
| `dim_accounts` | `account_id` | `fact_transactions` | `source_account_id` | `1 : *` | Single |
| `dim_accounts` | `account_id` | `fact_transactions` | `target_account_id` | `1 : *` | Single (Inactive/Userelationship) |
| `dim_accounts` | `account_id` | `fact_account_risk_summary` | `account_id` | `1 : 1` | Both |
| `dim_banks` | `bank_id` | `dim_accounts` | `bank_id` | `1 : *` | Single |
| `dim_dates` | `date_key` | `fact_transactions` | `date_key` | `1 : *` | Single |
| `dim_transaction_types` | `transaction_type` | `fact_transactions` | `transaction_type` | `1 : *` | Single |

---

## 3. Dashboard 1: Executive Financial Overview

### Visual Hierarchy & Canvas Layout
- **Theme Palette:** Corporate Navy (`#1F4E79`), Crisp White (`#FFFFFF`), Alert Crimson (`#C00000`), Slate Grey (`#595959`).
- **Top Header Bar (Y: 0, Height: 80px):**
  - Title: **FinTrace 360 — Executive Financial Overview**
  - Subtitle: *Simulated Multi-Bank Transaction Intelligence & Risk Portfolio*
  - Top Slicers: `Date Range (dim_dates[full_date])`, `Bank Name (dim_banks[bank_name])`, `Account Segment (dim_accounts[account_segment])`.

### Key Visuals:
1. **Row 1 — Executive KPI Cards (Y: 100px, 5 Cards across page):**
   - **Card 1:** `[Total Transactions]` (Formatted: `120.56K`)
   - **Card 2:** `[Total Gross Volume]` (Formatted: `$33.29M`)
   - **Card 3:** `[Average Transaction Size]` (Formatted: `$276.12`)
   - **Card 4:** `[Total Active Accounts]` (Formatted: `20,000`)
   - **Card 5:** `[Total Alerted Transactions]` (Formatted: `24.84K`, Font Color: Crimson)
2. **Row 2 — Trajectory & Rail Distribution (Y: 220px, Height: 300px):**
   - **Visual Left (Line & Clustered Column Chart):**
     - X-Axis: `dim_dates[full_date]`
     - Column Y-Axis: `[Total Gross Volume]`
     - Line Y-Axis: `[7-Day Rolling Volume]`, `[Alerted Volume]`
     - Title: *Daily Gross Volume Trajectory vs. 7-Day Moving Trend*
   - **Visual Right (Donut Chart):**
     - Legend: `dim_transaction_types[transaction_type]`
     - Values: `[Total Gross Volume]`
     - Title: *Gross Volume Share by Payment Rail*
3. **Row 3 — Cross-Bank Settlement & Account Health (Y: 540px, Height: 280px):**
   - **Visual Left (Horizontal Clustered Bar Chart):**
     - Y-Axis: `dim_banks[bank_name]`
     - X-Axis: `[Total Gross Volume]`, `[Alerted Volume]`
     - Title: *Gross Outflow vs. Flagged Exposure by Banking Entity*
   - **Visual Right (Gauge Chart):**
     - Value: `[Transaction Alert Rate]` (Value: `20.61%`)
     - Target: `15.0%`
     - Title: *Portfolio AML Alert Threshold Monitoring*

---

## 4. Dashboard 2: Transaction Behaviour & Velocity Analytics

### Key Visuals:
1. **Transaction Amount Distribution:**
   - Visual: Binned Column Chart (`Amount Bins: <$50, $50-100, $100-250, $250-400, $400+`).
   - X-Axis: Amount Tier | Y-Axis: Transaction Count.
2. **Payment Channel Velocity Matrix:**
   - Visual: Matrix Table.
   - Rows: `dim_transaction_types[transaction_type]`.
   - Columns: `dim_banks[bank_name]`.
   - Values: `[Total Transactions]`, `[Average Transaction Size]`, `[Interbank Volume Ratio]`.
3. **Originator vs. Beneficiary Corridor Table:**
   - Visual: Table with Data Bars.
   - Columns: `Originator Bank`, `Beneficiary Bank`, `Transfer Count`, `Gross Corridors ($)`, `Alerted Transfers`.
4. **Hourly / Step Activity Trajectory:**
   - Visual: Area Chart.
   - X-Axis: `fact_transactions[step_day]`.
   - Y-Axis: `[Total Transactions]`.

---

## 5. Dashboard 3: AML & Risk Analytics (Investigation Triage)

### Key Visuals:
1. **Risk Alert Queue Cards:**
   - `[Total SAR Alerted Accounts]` (`1,804`)
   - `[Account Alert Rate]` (`9.02%`)
   - `[High-Risk Accounts]`
   - `[High-Velocity Fan-In Hubs]`
2. **Network Degree Scatter Plot (Smurfing & Fan-in Detection):**
   - Visual: Scatter Chart.
   - X-Axis: `fact_account_risk_summary[out_tx_count]` (Fan-Out Degree).
   - Y-Axis: `fact_account_risk_summary[in_tx_count]` (Fan-In Degree).
   - Size: `fact_account_risk_summary[total_volume]`.
   - Color: `fact_account_risk_summary[is_sar_alert]` (Crimson for Alerted, Blue for Benign).
   - Play Axis / Slicer: `dim_banks[bank_name]`.
3. **Investigation Prioritization Grid:**
   - Visual: Drill-through Table.
   - Columns: `Account ID`, `Bank`, `Segment`, `Initial Balance`, `Inflow`, `Outflow`, `Turnover Ratio`, `Fan-In Index`, `Risk Tier`, `Investigation Priority`.
   - Conditional Formatting: Background color scale on `Turnover Ratio` (Red for > 50x).

---

## 6. Dashboard 4: Machine Learning Analytics (Model Benchmark)

### Key Visuals:
1. **Model Performance Comparison Bar Chart:**
   - Metrics: PR-AUC, F1-Score, Recall, Precision across Logistic Regression, Random Forest, Isolation Forest.
2. **Confusion Matrix Heatmap Card:**
   - True Negatives, False Positives, False Negatives, True Positives.
3. **Precision-Recall Trade-off Curve:**
   - Threshold vs Precision & Recall.
