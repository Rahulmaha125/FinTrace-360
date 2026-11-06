# FinTrace 360 — Power BI DAX Measures & Metric Dictionary

This document serves as the master repository for all DAX (Data Analysis Expressions) calculated measures utilized across the FinTrace 360 analytical dashboards.

---

## 1. Executive Overview Measures (Dashboard 1)

### `Total Transactions`
- **Description:** Total volume of transactions processed through the platform.
```dax
Total Transactions = COUNTROWS(fact_transactions)
```

### `Total Gross Volume ($)`
- **Description:** Cumulative gross currency value of all processed transactions.
```dax
Total Gross Volume = SUM(fact_transactions[amount])
```

### `Average Transaction Size ($)`
- **Description:** Arithmetic mean amount transferred per transaction.
```dax
Average Transaction Size = AVERAGE(fact_transactions[amount])
```

### `Active Originating Accounts`
- **Description:** Count of distinct customer accounts initiating payment transfers.
```dax
Active Originating Accounts = DISTINCTCOUNT(fact_transactions[source_account_id])
```

### `Active Beneficiary Accounts`
- **Description:** Count of distinct customer accounts receiving payment transfers.
```dax
Active Beneficiary Accounts = DISTINCTCOUNT(fact_transactions[target_account_id])
```

### `Total Active Accounts`
- **Description:** Total number of registered accounts within the monitoring perimeter.
```dax
Total Active Accounts = COUNTROWS(dim_accounts)
```

### `Total Alerted Transactions`
- **Description:** Transactions flagged by the AML monitoring engine or topology matcher.
```dax
Total Alerted Transactions = 
CALCULATE(
    COUNTROWS(fact_transactions),
    fact_transactions[is_alerted_tx] = TRUE
)
```

### `Alerted Volume ($)`
- **Description:** Gross currency value of transactions linked to active AML alerts.
```dax
Alerted Volume = 
CALCULATE(
    SUM(fact_transactions[amount]),
    fact_transactions[is_alerted_tx] = TRUE
)
```

### `Transaction Alert Rate (%)`
- **Description:** Percentage of total transactions that trigger AML investigation flags.
```dax
Transaction Alert Rate = 
DIVIDE([Total Alerted Transactions], [Total Transactions], 0)
```

### `Volume Alert Share (%)`
- **Description:** Proportion of gross monetary volume attributable to flagged transactions.
```dax
Volume Alert Share = 
DIVIDE([Alerted Volume], [Total Gross Volume], 0)
```

---

## 2. Time Intelligence & Trajectory Measures

### `7-Day Rolling Volume ($)`
- **Description:** 7-day trailing moving average to smooth day-to-day volatility.
```dax
7-Day Rolling Volume = 
AVERAGEX(
    DATESINPERIOD(
        dim_dates[full_date],
        LASTDATE(dim_dates[full_date]),
        -7,
        DAY
    ),
    [Total Gross Volume]
)
```

### `Previous Month Volume ($)`
- **Description:** Total gross volume for the prior calendar month.
```dax
Previous Month Volume = 
CALCULATE(
    [Total Gross Volume],
    PREVIOUSMONTH(dim_dates[full_date])
)
```

### `Month-over-Month Volume Growth (%)`
- **Description:** Percentage change in transaction volume relative to previous month.
```dax
MoM Volume Growth % = 
VAR PrevVol = [Previous Month Volume]
VAR CurrVol = [Total Gross Volume]
RETURN
    IF(
        ISBLANK(PrevVol) || PrevVol = 0,
        BLANK(),
        DIVIDE(CurrVol - PrevVol, PrevVol)
    )
```

---

## 3. Transaction Behaviour & Velocity Measures (Dashboard 2)

### `Interbank Transactions Count`
- **Description:** Number of transfers spanning two different financial institutions.
```dax
Interbank Transactions = 
CALCULATE(
    COUNTROWS(fact_transactions),
    fact_transactions[is_interbank] = TRUE
)
```

### `Interbank Volume Ratio (%)`
- **Description:** Percentage of total payment transfers conducted across interbank rails.
```dax
Interbank Volume Ratio = 
DIVIDE([Interbank Transactions], [Total Transactions], 0)
```

### `High-Value Wire Transactions`
- **Description:** Total count of WIRE transactions exceeding $400 statutory thresholds.
```dax
High Value Wire Transactions = 
CALCULATE(
    COUNTROWS(fact_transactions),
    fact_transactions[transaction_type] = "WIRE"
)
```

### `Average Transactions Per Active Day`
- **Description:** Daily average transaction velocity across active business days.
```dax
Avg Transactions Per Day = 
AVERAGEX(
    VALUES(dim_dates[full_date]),
    [Total Transactions]
)
```

---

## 4. AML & Risk Analytics Measures (Dashboard 3)

### `Total SAR Alerted Accounts`
- **Description:** Number of unique customer accounts implicated in confirmed AML typologies.
```dax
Total SAR Alerted Accounts = 
CALCULATE(
    COUNTROWS(dim_accounts),
    dim_accounts[is_sar_alert] = TRUE
)
```

### `Account Alert Rate (%)`
- **Description:** Ratio of alerted accounts to total monitored customer base.
```dax
Account Alert Rate = 
DIVIDE([Total SAR Alerted Accounts], [Total Active Accounts], 0)
```

### `High-Risk Account Count`
- **Description:** Customer accounts classified as CRITICAL or HIGH risk tier.
```dax
High Risk Accounts = 
CALCULATE(
    COUNTROWS(fact_account_risk_summary),
    fact_account_risk_summary[risk_tier] IN {"CRITICAL", "HIGH"}
)
```

### `High-Velocity Fan-In Hubs`
- **Description:** Accounts exhibiting over 20 incoming transactions with high turnover ratios.
```dax
High Velocity Fan-In Hubs = 
CALCULATE(
    COUNTROWS(fact_account_risk_summary),
    fact_account_risk_summary[in_tx_count] >= 20,
    fact_account_risk_summary[turnover_ratio] >= 50
)
```

---

## 5. Machine Learning Evaluation Measures (Dashboard 4)

### `Model Precision`
```dax
Model Precision = DIVIDE([True Positives], [True Positives] + [False Positives], 0)
```

### `Model Recall`
```dax
Model Recall = DIVIDE([True Positives], [True Positives] + [False Negatives], 0)
```

### `Model F1-Score`
```dax
Model F1-Score = 
VAR P = [Model Precision]
VAR R = [Model Recall]
RETURN
    IF(P + R = 0, 0, 2 * DIVIDE(P * R, P + R))
```
