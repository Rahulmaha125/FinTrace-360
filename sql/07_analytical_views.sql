-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 07: Analytical Reporting Views (Power BI Direct Import Layer)
-- ==============================================================================

SET search_path TO analytics, staging, public;

-- ------------------------------------------------------------------------------
-- VIEW 1: Executive KPI Overview (For Power BI Executive Cards)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_executive_kpis AS
SELECT 
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_gross_value_usd,
    ROUND(AVG(amount), 2) AS average_transaction_value_usd,
    ROUND(MIN(amount), 2) AS minimum_transaction_amount_usd,
    ROUND(MAX(amount), 2) AS maximum_transaction_amount_usd,
    (SELECT COUNT(*) FROM analytics.dim_accounts) AS total_active_accounts,
    (SELECT COUNT(*) FROM analytics.dim_accounts WHERE is_sar_alert) AS total_alerted_accounts,
    SUM(CASE WHEN is_alerted_tx THEN 1 ELSE 0 END) AS total_alerted_transactions,
    ROUND(SUM(CASE WHEN is_alerted_tx THEN amount ELSE 0 END), 2) AS alerted_gross_value_usd,
    ROUND(100.0 * SUM(CASE WHEN is_alerted_tx THEN 1 ELSE 0 END) / COUNT(*), 2) AS transaction_alert_rate_pct
FROM analytics.fact_transactions;

-- ------------------------------------------------------------------------------
-- VIEW 2: Daily Transaction Trends (For Power BI Time-Series Visuals)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_daily_transaction_trends AS
SELECT 
    d.date_key,
    d.full_date,
    d.day_name,
    d.month_name,
    d.is_weekend,
    t.step_day,
    COUNT(t.transaction_id) AS daily_transaction_count,
    ROUND(SUM(t.amount), 2) AS daily_gross_volume_usd,
    ROUND(AVG(t.amount), 2) AS daily_average_amount_usd,
    SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) AS daily_alerted_count,
    ROUND(SUM(CASE WHEN t.is_alerted_tx THEN t.amount ELSE 0 END), 2) AS daily_alerted_volume_usd,
    ROUND(100.0 * SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) / NULLIF(COUNT(t.transaction_id), 0), 2) AS daily_alert_rate_pct,
    -- 7-Day Rolling Average
    ROUND(AVG(SUM(t.amount)) OVER (ORDER BY t.step_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS rolling_7d_volume_usd
FROM analytics.fact_transactions t
JOIN analytics.dim_dates d ON t.date_key = d.date_key
GROUP BY d.date_key, d.full_date, d.day_name, d.month_name, d.is_weekend, t.step_day
ORDER BY t.step_day;

-- ------------------------------------------------------------------------------
-- VIEW 3: Bank Performance & Cross-Institutional Clearing
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_bank_performance AS
SELECT 
    b.bank_id,
    b.bank_name,
    b.institution_type,
    b.country_code,
    b.risk_rating,
    COUNT(DISTINCT a.account_id) AS total_accounts,
    SUM(CASE WHEN a.is_sar_alert THEN 1 ELSE 0 END) AS alerted_accounts,
    COUNT(t.transaction_id) AS total_outbound_tx,
    ROUND(SUM(t.amount), 2) AS gross_outflow_usd,
    ROUND(AVG(t.amount), 2) AS avg_transfer_size_usd,
    SUM(CASE WHEN t.is_interbank THEN 1 ELSE 0 END) AS interbank_tx_count,
    SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) AS alerted_tx_count,
    ROUND(SUM(CASE WHEN t.is_alerted_tx THEN t.amount ELSE 0 END), 2) AS alerted_outflow_usd,
    ROUND(100.0 * SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) / NULLIF(COUNT(t.transaction_id), 0), 2) AS institutional_alert_rate_pct
FROM analytics.dim_banks b
JOIN analytics.dim_accounts a ON b.bank_id = a.bank_id
LEFT JOIN analytics.fact_transactions t ON a.account_id = t.source_account_id
GROUP BY b.bank_id, b.bank_name, b.institution_type, b.country_code, b.risk_rating;

-- ------------------------------------------------------------------------------
-- VIEW 4: Transaction Type Metrics & Channel Risk Profile
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_transaction_type_metrics AS
SELECT 
    t.transaction_type,
    dt.rail_category,
    dt.settlement_speed,
    dt.is_high_value_channel,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(SUM(t.amount), 2) AS gross_volume_usd,
    ROUND(AVG(t.amount), 2) AS avg_amount_usd,
    ROUND(MIN(t.amount), 2) AS min_amount_usd,
    ROUND(MAX(t.amount), 2) AS max_amount_usd,
    SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) AS alerted_tx_count,
    ROUND(SUM(CASE WHEN t.is_alerted_tx THEN t.amount ELSE 0 END), 2) AS alerted_volume_usd,
    ROUND(100.0 * SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) / NULLIF(COUNT(t.transaction_id), 0), 2) AS channel_alert_rate_pct
FROM analytics.fact_transactions t
JOIN analytics.dim_transaction_types dt ON t.transaction_type = dt.transaction_type
GROUP BY t.transaction_type, dt.rail_category, dt.settlement_speed, dt.is_high_value_channel;

-- ------------------------------------------------------------------------------
-- VIEW 5: AML Risk & Case Investigation Triage Queue
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_aml_alert_triage AS
SELECT 
    r.account_id,
    a.bank_id,
    b.bank_name,
    a.account_segment,
    a.initial_balance,
    r.risk_tier,
    r.is_sar_alert,
    r.total_tx_count,
    r.out_tx_count,
    r.in_tx_count,
    r.total_outflow,
    r.total_inflow,
    r.total_volume,
    r.net_flow,
    r.turnover_ratio,
    r.tx_velocity_per_day,
    r.unique_counterparties,
    r.fan_in_index,
    r.fan_out_index,
    CASE 
        WHEN r.turnover_ratio >= 100.0 AND r.in_tx_count >= 20 THEN 'CRITICAL - HIGH VELOCITY FAN-IN HUB'
        WHEN r.turnover_ratio >= 50.0 THEN 'ELEVATED - EXCESSIVE TURNOVER'
        WHEN r.is_sar_alert THEN 'PRIORITY - TOPOLOGY ALERT (CYCLE/FAN-IN)'
        ELSE 'STANDARD MONITORING'
    END AS investigation_priority
FROM analytics.fact_account_risk_summary r
JOIN analytics.dim_accounts a ON r.account_id = a.account_id
JOIN analytics.dim_banks b ON a.bank_id = b.bank_id
ORDER BY r.turnover_ratio DESC;
