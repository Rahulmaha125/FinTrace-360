-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 05: Advanced SQL Analytics (CTEs, Window Functions, Trends, Ranking)
-- ==============================================================================

SET search_path TO analytics, staging, public;

-- ------------------------------------------------------------------------------
-- QUERY 1: Running Cumulative Volume & Daily 7-Day Moving Average
-- Purpose: Track liquidity accumulation and smooth daily volume volatility using window functions.
-- ------------------------------------------------------------------------------
WITH daily_aggregates AS (
    SELECT 
        d.full_date,
        t.step_day,
        COUNT(t.transaction_id) AS daily_tx_count,
        ROUND(SUM(t.amount), 2) AS daily_gross_value,
        SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) AS daily_alerted_tx
    FROM analytics.fact_transactions t
    JOIN analytics.dim_dates d ON t.date_key = d.date_key
    GROUP BY d.full_date, t.step_day
)
SELECT 
    full_date,
    step_day,
    daily_tx_count,
    daily_gross_value,
    -- Window Function: Running Cumulative Volume
    ROUND(SUM(daily_gross_value) OVER (ORDER BY step_day), 2) AS cumulative_volume_usd,
    -- Window Function: 7-Day Rolling Moving Average Volume
    ROUND(AVG(daily_gross_value) OVER (
        ORDER BY step_day 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_7d_volume_usd,
    -- Daily Alert Ratio
    ROUND(100.0 * daily_alerted_tx / NULLIF(daily_tx_count, 0), 2) AS daily_alert_rate_pct
FROM daily_aggregates
ORDER BY step_day;

-- ------------------------------------------------------------------------------
-- QUERY 2: Month-over-Month (MoM) Growth Analysis
-- Purpose: Quantify month-on-month transaction growth, volume velocity, and percentage change.
-- ------------------------------------------------------------------------------
WITH monthly_metrics AS (
    SELECT 
        d.year_number,
        d.month_number,
        d.month_name,
        COUNT(t.transaction_id) AS monthly_tx_count,
        ROUND(SUM(t.amount), 2) AS monthly_volume_usd,
        ROUND(AVG(t.amount), 2) AS avg_monthly_ticket_usd
    FROM analytics.fact_transactions t
    JOIN analytics.dim_dates d ON t.date_key = d.date_key
    GROUP BY d.year_number, d.month_number, d.month_name
)
SELECT 
    year_number,
    month_number,
    TRIM(month_name) AS month_name,
    monthly_tx_count,
    monthly_volume_usd,
    -- Window Function: Lagging previous month volume
    LAG(monthly_volume_usd, 1) OVER (ORDER BY year_number, month_number) AS prev_month_volume,
    -- Month-over-Month Absolute Change
    ROUND(monthly_volume_usd - LAG(monthly_volume_usd, 1) OVER (ORDER BY year_number, month_number), 2) AS mom_volume_change_usd,
    -- Month-over-Month Percentage Growth
    ROUND(100.0 * (monthly_volume_usd - LAG(monthly_volume_usd, 1) OVER (ORDER BY year_number, month_number)) / 
          NULLIF(LAG(monthly_volume_usd, 1) OVER (ORDER BY year_number, month_number), 0), 2) AS mom_growth_rate_pct
FROM monthly_metrics
ORDER BY year_number, month_number;

-- ------------------------------------------------------------------------------
-- QUERY 3: Account Activity Ranking by Total Volume and Velocity
-- Purpose: Identify and rank top originator and beneficiary accounts within each bank.
-- ------------------------------------------------------------------------------
WITH account_bank_activity AS (
    SELECT 
        a.account_id,
        a.bank_id,
        a.account_segment,
        a.is_sar_alert,
        COUNT(t.transaction_id) AS total_outbound_tx,
        ROUND(SUM(t.amount), 2) AS total_outflow_usd,
        ROUND(AVG(t.amount), 2) AS avg_transfer_usd
    FROM analytics.dim_accounts a
    JOIN analytics.fact_transactions t ON a.account_id = t.source_account_id
    GROUP BY a.account_id, a.bank_id, a.account_segment, a.is_sar_alert
)
SELECT 
    bank_id,
    account_id,
    account_segment,
    is_sar_alert,
    total_outbound_tx,
    total_outflow_usd,
    avg_transfer_usd,
    -- Window Function: Dense Rank within each bank
    DENSE_RANK() OVER (PARTITION BY bank_id ORDER BY total_outflow_usd DESC) AS rank_within_bank,
    -- Window Function: Overall Rank across all financial institutions
    DENSE_RANK() OVER (ORDER BY total_outflow_usd DESC) AS global_rank
FROM account_bank_activity
ORDER BY total_outflow_usd DESC
LIMIT 50;

-- ------------------------------------------------------------------------------
-- QUERY 4: Top Counterparty Corridor Analysis (High-Density Account Pairs)
-- Purpose: Detect recurring payment corridors and high-frequency pairwise relationships.
-- ------------------------------------------------------------------------------
WITH counterparty_corridors AS (
    SELECT 
        source_account_id,
        target_account_id,
        originator_bank_id,
        beneficiary_bank_id,
        COUNT(*) AS transfer_count,
        ROUND(SUM(amount), 2) AS corridor_total_amount_usd,
        ROUND(AVG(amount), 2) AS corridor_avg_amount_usd,
        SUM(CASE WHEN is_alerted_tx THEN 1 ELSE 0 END) AS alerted_transfer_count
    FROM analytics.fact_transactions
    GROUP BY source_account_id, target_account_id, originator_bank_id, beneficiary_bank_id
)
SELECT 
    source_account_id,
    target_account_id,
    originator_bank_id,
    beneficiary_bank_id,
    transfer_count,
    corridor_total_amount_usd,
    corridor_avg_amount_usd,
    alerted_transfer_count,
    DENSE_RANK() OVER (ORDER BY corridor_total_amount_usd DESC) AS corridor_value_rank
FROM counterparty_corridors
WHERE transfer_count > 1
ORDER BY corridor_total_amount_usd DESC
LIMIT 25;
