# FinTrace 360 — Data Quality and Audit Report

## 1. Executive Quality Status: **VALIDATED WITH BUSINESS NOTICES**

This data quality audit evaluates structural integrity, missingness, duplicate keys, numeric validity, and relational foreign keys across the primary IBM AMLSim benchmark datasets.

---

## 2. Accounts Dataset (`accounts.csv`) Audit

| Audit Dimension | Metric Value | Benchmark Expectation | Compliance Status |
|:---|:---:|:---:|:---:|
| **Total Record Count** | 20,000 | 20,000 | PASS |
| **Total Attribute Columns** | 4 | 4 | PASS |
| **In-Memory Size** | 0.48 MB | < 10 MB | PASS |
| **Duplicate Full Rows** | 0 | 0 | PASS |
| **Duplicate `account_id` Keys** | 0 | 0 (Strict Primary Key) | PASS |
| **Missing / Null Values** | 0 | 0 | PASS |
| **Negative Balances** | 0 | 0 | PASS |
| **Minimum Initial Balance** | $100.04 | > 0.00 | PASS |
| **Maximum Initial Balance** | $599.92 | Reasonable boundary | PASS |
| **Benign Accounts** | 18,196 (90.98%) | Majority class | PASS |
| **Alerted Accounts (SAR)** | 1,804 (9.02%) | Realistic financial anomaly rate (~9%) | PASS |

---

## 3. Transactions Dataset (`transactions.csv`) Audit

| Audit Dimension | Metric Value | Benchmark Expectation | Compliance Status |
|:---|:---:|:---:|:---:|
| **Total Record Count** | 120,558 | ~120,000 | PASS |
| **Total Attribute Columns** | 4 | 4 | PASS |
| **In-Memory Size** | 3.68 MB | < 50 MB | PASS |
| **Burst / Recurring Same-Day Duplicates** | 1,684 (1.39%) | Business Recurring / Burst Transfers | PASS (Monitored) |
| **Non-Positive / Negative Amounts** | 0 | 0 | PASS |
| **Negative Time Steps** | 0 | 0 | PASS |
| **Orphan Source Accounts (FK)** | 0 | 0 (All sources exist in accounts) | PASS |
| **Orphan Target Accounts (FK)** | 0 | 0 (All targets exist in accounts) | PASS |
| **Self-Loop Transactions (`src == dst`)** | 15 (0.01%) | Internal Account Rebalancing | PASS (Monitored) |
| **Temporal Span** | Step 1 to Step 149 (149 Days) | Continuous sequence | PASS |
| **Total Gross Value Transferred** | $33,287,919.20 USD | Exact aggregate | PASS |
| **Average Transaction Size** | $276.12 USD | Exact aggregate | PASS |
| **Transaction Range** | $2.51 – $599.91 | Bounded | PASS |

---

## 4. Referential Integrity & Analytical Observations

1. **Burst / Recurring Transfers (1,684 records):** In the raw dataset, 1,684 records share identical sender, receiver, amount, and day step. In financial transaction processing, multiple identical payments on the same date occur naturally (e.g. repeated daily payroll allocations or batch invoice settlements) or represent structuring attempts (smurfing identical micro-amounts). Our cleaning pipeline attaches an explicit surrogate primary key (`transaction_id`) to preserve every distinct payment event.
2. **Self-Loop Transfers (15 records):** Exactly 15 transactions represent intra-account sweeps or internal rebalancing where source equals destination.
3. **Foreign Key Integrity:** 100% of originator accounts (`sourceNodeId`) and beneficiary accounts (`targetNodeId`) resolve directly to an existing `nodeid` in the `accounts` table. Zero orphan transactions exist.
4. **Completeness:** No synthetic missing fields or imputed placeholders detected.
5. **Temporal Monotonicity:** Transaction steps adhere to a realistic multi-day sequence with active daily flows.
