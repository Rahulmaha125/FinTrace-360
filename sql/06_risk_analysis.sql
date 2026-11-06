-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 06: AML & Financial Risk Intelligence Analytics
-- ==============================================================================

SET search_path TO analytics, staging, public;

-- ------------------------------------------------------------------------------
-- QUERY 1: AML Alert Summary & Risk Concentration by Institution
-- Purpose: Quantify institutional alert exposure, alert rates, and alerted capital.
-- ------------------------------------------------------------------------------
SELECT 
    b.bank_id,
    b.bank_name,
    COUNT(DISTINCT a.account_id) AS total_customer_accounts,
    SUM(CASE WHEN a.is_sar_alert THEN 1 ELSE 0 END) AS sar_alerted_accounts,
    ROUND(100.0 * SUM(CASE WHEN a.is_sar_alert THEN 1 ELSE 0 END) / COUNT(DISTINCT a.account_id), 2) AS account_alert_rate_pct,
    COUNT(t.transaction_id) AS total_outbound_tx,
    SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) AS alerted_outbound_tx,
    ROUND(SUM(CASE WHEN t.is_alerted_tx THEN t.amount ELSE 0 END), 2) AS gross_alerted_outflow_usd,
    ROUND(100.0 * SUM(CASE WHEN t.is_alerted_tx THEN t.amount ELSE 0 END) / NULLIF(SUM(t.amount), 0), 2) AS volume_alert_share_pct
FROM analytics.dim_banks b
JOIN analytics.dim_accounts a ON b.bank_id = a.bank_id
LEFT JOIN analytics.fact_transactions t ON a.account_id = t.source_account_id
GROUP BY b.bank_id, b.bank_name
ORDER BY gross_alerted_outflow_usd DESC;

-- ------------------------------------------------------------------------------
-- QUERY 2: Structuring & Smurfing Detection (Fan-In Hub Typology)
-- Purpose: Detect collection accounts receiving high volumes of micro-transfers from multiple originators.
-- ------------------------------------------------------------------------------
WITH beneficiary_fan_in AS (
    SELECT 
        target_account_id AS beneficiary_account_id,
        beneficiary_bank_id,
        COUNT(DISTINCT source_account_id) AS distinct_senders_count,
        COUNT(transaction_id) AS total_incoming_transfers,
        ROUND(SUM(amount), 2) AS total_inflow_usd,
        ROUND(AVG(amount), 2) AS avg_transfer_usd,
        ROUND(MAX(amount), 2) AS max_transfer_usd,
        MIN(step_day) AS first_step,
        MAX(step_day) AS last_step,
        (MAX(step_day) - MIN(step_day) + 1) AS active_day_span
    FROM analytics.fact_transactions
    GROUP BY target_account_id, beneficiary_bank_id
)
SELECT 
    b.beneficiary_account_id,
    b.beneficiary_bank_id,
    a.account_segment,
    a.initial_balance,
    a.is_sar_alert,
    b.distinct_senders_count,
    b.total_incoming_transfers,
    b.total_inflow_usd,
    b.avg_transfer_usd,
    b.active_day_span,
    -- Fan-in velocity: incoming transactions per active day
    ROUND(b.total_incoming_transfers::NUMERIC / NULLIF(b.active_day_span, 0), 2) AS transfers_per_active_day
FROM beneficiary_fan_in b
JOIN analytics.dim_accounts a ON b.beneficiary_account_id = a.account_id
WHERE b.distinct_senders_count >= 10
ORDER BY b.distinct_senders_count DESC, b.total_inflow_usd DESC
LIMIT 30;

-- ------------------------------------------------------------------------------
-- QUERY 3: High-Turnover Velocity Ratio (Risk Tier Classification)
-- Purpose: Segment accounts whose total transaction volume drastically exceeds opening deposits.
-- ------------------------------------------------------------------------------
SELECT 
    account_id,
    risk_tier,
    is_sar_alert,
    initial_balance,
    total_volume,
    turnover_ratio,
    total_tx_count,
    unique_counterparties,
    tx_velocity_per_day
FROM analytics.fact_account_risk_summary
WHERE turnover_ratio >= 25.0
ORDER BY turnover_ratio DESC
LIMIT 50;

-- ------------------------------------------------------------------------------
-- QUERY 4: Rapid Outflow Post-Deposit (Layering Flag)
-- Purpose: Identify accounts with near-zero net balance retention (Inflow ~= Outflow).
-- ------------------------------------------------------------------------------
SELECT 
    account_id,
    total_inflow,
    total_outflow,
    total_volume,
    net_flow,
    flow_ratio,
    turnover_ratio,
    is_sar_alert
FROM analytics.fact_account_risk_summary
WHERE total_volume > 5000.0
  AND ABS(net_flow) / NULLIF(total_volume, 0) < 0.05 -- Less than 5% retained balance
  AND total_tx_count >= 10
ORDER BY total_volume DESC
LIMIT 30;
