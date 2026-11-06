# FinTrace 360 — Technical Interview & Defense Guide

This guide equips the candidate to defend and explain all architectural, analytical, SQL, and machine learning decisions during technical interviews with Data Analytics, FinTech, and Banking teams.

---

## 1. Project Framing & Business Problem

### Q1: Can you give an executive elevator pitch of FinTrace 360?
> **Answer:** "FinTrace 360 is an end-to-end financial transaction intelligence and Anti-Money Laundering (AML) risk analytics platform. I designed it to solve a major compliance challenge in banking: detecting subtle financial crime typologies like smurfing, layering, and cyclical transfers among millions of legitimate transactions while drastically curbing false positive alert fatigue. The architecture combines Python ETL, a PostgreSQL dimensional Star Schema, advanced window function analytics, interactive Power BI dashboards, and imbalanced machine learning models focused on Precision-Recall AUC."

### Q2: Why did you separate the project into Gate 1 and Gate 2?
> **Answer:** "In financial data engineering, data ethics and compliance boundaries are paramount. Gate 1 represents our active portfolio demo, utilizing synthetic benchmarks (IBM AMLSim, PaySim, IEEE-CIS) with simulated banking entities to ensure complete reproducibility and legal compliance without exposing confidential customer PII. Gate 2 is the architectural blueprint for enterprise deployment, detailing tenant schema isolation, mTLS 1.3 encryption, and role-based access control if a verified financial institution were to connect live core banking feeds."

---

## 2. Data Engineering & Relational Warehouse

### Q3: Why did you choose a Star Schema over a 3NF normalized schema for the database?
> **Answer:** "While 3NF is optimal for OLTP transaction processing to avoid update anomalies, analytical reporting and Power BI query engines require fast aggregation across millions of rows. By modeling dimensions (`dim_accounts`, `dim_banks`, `dim_dates`, `dim_transaction_types`) around transactional facts (`fact_transactions`), we eliminated multi-table cascading joins and provided optimal columnar performance with sub-second dashboard filtering."

### Q4: Can you explain a complex SQL query you authored in this project?
> **Answer:** "In `sql/05_advanced_analysis.sql`, I implemented window functions to compute 7-day rolling average volumes and month-over-month growth:
```sql
ROUND(AVG(daily_gross_value) OVER (
    ORDER BY step_day 
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
), 2) AS moving_avg_7d_volume_usd
```
I also used `DENSE_RANK() OVER (PARTITION BY bank_id ORDER BY total_outflow_usd DESC)` to rank high-exposure customer accounts within each individual bank, allowing compliance teams to benchmark risk within individual institutions."

---

## 3. Business Intelligence & Power BI

### Q5: How did you design the DAX measures to prevent performance bottlenecks?
> **Answer:** "I avoided inefficient row-by-row iteration in favor of set-based vector operations. For example, for time intelligence:
```dax
7-Day Rolling Volume = 
AVERAGEX(
    DATESINPERIOD(dim_dates[full_date], LASTDATE(dim_dates[full_date]), -7, DAY),
    [Total Gross Volume]
)
```
I established a dedicated date dimension table with explicit primary key-foreign key relationships to the fact table, ensuring Power BI's VertiPaq engine compresses data and computes measures in-memory without expensive runtime table scans."

---

## 4. Machine Learning & Risk Analytics (20% Scope)

### Q6: Why did you focus on PR-AUC instead of standard Accuracy or ROC-AUC?
> **Answer:** "In fraud and AML monitoring, datasets are heavily imbalanced—in our benchmark, alerts represent only 9.02% of accounts. A naive model that classifies every account as benign achieves 90.98% accuracy while failing 100% of compliance objectives. Furthermore, ROC-AUC can be deceptive because the large volume of True Negatives inflates the score. PR-AUC (Precision-Recall Area Under Curve) evaluates precision directly across varying recall thresholds, measuring how accurately the model surfaces genuine alerts without burying investigators in false alarms."

### Q7: What was the role of Isolation Forest alongside supervised models?
> **Answer:** "Supervised models (like Random Forest and XGBoost) excel at detecting historical typologies present in training data. However, financial criminals constantly invent novel layering structures. Isolation Forest operates completely unsupervised by isolating anomalies in high-dimensional feature space, successfully detecting 97 anomalous accounts without ground truth labels as an early warning system for zero-day money laundering techniques."

### Q8: What was your most predictive feature?
> **Answer:** "`turnover_ratio` (total transaction volume divided by opening deposit) accounted for over 42% of model importance. Benign accounts had an average turnover of 12.2x over 149 days, whereas alerted accounts surged to 21.9x overall and exceeded 100x–300x in rapid smurfing collection hubs."
